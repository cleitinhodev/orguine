"""Executa um plano já confirmado pelo usuário: backup -> mover/lixeira -> diário."""

from __future__ import annotations

import logging
import os
import shutil
import stat
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .backup import create_backup
from .hashing import Cancelled, sha256_file
from .journal import Journal
from .models import Action, BackupMode, Plan, PlanItem
from .naming import path_key, unique_path
from .safety import ensure_folder_allowed

log = logging.getLogger(__name__)
ProgressFn = Callable[[int, int, str], None]
SAVE_EVERY = 25


def _default_trash(path: str) -> None:
    from send2trash import send2trash  # import tardio: só quando realmente precisar

    send2trash(path)


@dataclass
class RunResult:
    moved: int = 0
    renamed: int = 0
    trashed: int = 0
    skipped: int = 0
    errors: list[tuple[str, str]] = field(default_factory=list)
    cancelled: bool = False
    journal_path: Path | None = None
    backup_path: Path | None = None


def _is_real_dir(p: Path) -> bool:
    return p.is_dir() and not p.is_symlink()


def _temp_name(p: Path) -> Path:
    """Nome provisório, na mesma pasta, para tirar um arquivo do caminho de uma pasta nova."""
    return unique_path(p.with_name(f"{p.name}.orguine-tmp-{uuid.uuid4().hex[:8]}"))


def _unstash(stashed: dict[int, tuple[PlanItem, Path, Path]]) -> None:
    """Arquivos tirados do caminho que acabaram não sendo movidos (erro/cancelamento): volta o
    nome original se ele estiver livre. Se não estiver, o desfazer cuida disso pelo diário."""
    for item, original, tmp in stashed.values():
        try:
            if os.path.lexists(tmp) and not os.path.lexists(original):
                os.rename(tmp, original)
                item.src = original
        except OSError as exc:
            log.warning("Não foi possível devolver o nome de %s: %s", tmp, exc)


def _check_item(item: PlanItem) -> str:
    st = os.lstat(item.src)
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        raise OSError("não é mais um arquivo comum")
    if st.st_size != item.size:
        raise OSError("o arquivo mudou depois da prévia; analise de novo")
    return item.sha256 or sha256_file(item.src)


def execute_plan(plan: Plan, backup: BackupMode = BackupMode.NONE,
                 progress: ProgressFn | None = None, cancel: threading.Event | None = None,
                 trash_func: Callable[[str], None] | None = None,
                 backup_progress: ProgressFn | None = None,
                 allow_sensitive_trash: bool = False) -> RunResult:
    """Move/manda para a lixeira conforme o plano. Nunca sobrescreve, nunca apaga de vez."""
    ensure_folder_allowed(plan.root)
    trash = trash_func or _default_trash
    res = RunResult(skipped=len(plan.skipped))
    ops = [i for i in plan.items if i.action is not Action.SKIP]
    if not allow_sensitive_trash:  # camada extra: segredo só vai p/ lixeira com aval explícito
        protected = [i for i in ops if i.is_sensitive and i.action is Action.TRASH]
        for i in protected:
            res.skipped += 1
            res.errors.append((str(i.src), "sensitive_protected"))
        ops = [i for i in ops if i not in protected]
    if not ops:
        return res

    # 1) Backup (aborta tudo se falhar).
    try:
        res.backup_path = create_backup(plan.root, [i.src for i in ops], backup,
                                        backup_progress or progress, cancel)
    except Cancelled:
        res.cancelled = True
        return res

    # 2) Diário criado ANTES de mexer em qualquer arquivo.
    journal = Journal.create(plan.root, plan.options.mode.value, res.backup_path)
    res.journal_path = journal.path
    status = "done"
    total = len(ops)
    root = plan.root
    pending: dict[str, PlanItem] = {path_key(i.src): i for i in ops}  # ainda não processados
    done: set[int] = set()
    stashed: dict[int, tuple[PlanItem, Path, Path]] = {}  # id -> (item, nome original, provisório)

    def trash_item(item: PlanItem) -> None:
        pending.pop(path_key(item.src), None)
        done.add(id(item))
        digest = _check_item(item)
        trash(str(item.src))
        journal.add("trash", item.src, None, item.size, digest)
        res.trashed += 1

    def clear_way(blocker: Path) -> bool:
        """Um arquivo ocupa o nome de uma pasta a criar. Se ele também sai pelo plano, sai da
        frente agora; devolve False se ele fica (então a pasta ganha um sufixo)."""
        item = pending.get(path_key(blocker))
        if item is None:
            return False
        if item.action is Action.TRASH:
            try:
                trash_item(item)
            except Exception as exc:  # noqa: BLE001
                res.errors.append((str(item.src), str(exc)))
                return False
            return not os.path.lexists(blocker)
        # MOVE: renomeia para um nome provisório na mesma pasta. O diário é salvo ANTES de
        # renomear, então mesmo se o programa cair aqui o desfazer sabe o nome original.
        try:
            _check_item(item)
        except Exception as exc:  # noqa: BLE001 - ele não será movido: fica, e a pasta ganha sufixo
            pending.pop(path_key(item.src), None)
            done.add(id(item))
            res.errors.append((str(item.src), str(exc)))
            return False
        tmp = _temp_name(item.src)
        pending.pop(path_key(item.src), None)
        journal.add("stash", item.src, tmp, item.size, item.sha256)
        journal.save()
        os.rename(item.src, tmp)
        stashed[id(item)] = (item, item.src, tmp)
        item.src = tmp
        pending[path_key(tmp)] = item
        return True

    def mkdirs(folder: Path) -> Path:
        """Cria as pastas de destino (registrando as novas) e devolve a pasta real usada."""
        cur = root
        for comp in folder.relative_to(root).parts:
            cand, n = cur / comp, 2
            while True:
                if _is_real_dir(cand):
                    break
                if not os.path.lexists(cand) or clear_way(cand):
                    cand.mkdir()
                    journal.add_dir(cand)
                    break
                # ocupado por algo que fica (ex.: mudou depois da prévia): pasta com sufixo
                cand, n = cur / f"{comp} ({n})", n + 1
            cur = cand
        return cur

    try:
        for n, item in enumerate(ops, 1):
            if cancel is not None and cancel.is_set():
                res.cancelled = True
                status = "cancelled"
                break
            if progress:
                progress(n, total, item.src.name)
            if id(item) in done:
                continue
            try:
                if item.action is Action.MOVE:
                    assert item.dst is not None
                    digest = _check_item(item)
                    folder = mkdirs(item.dst.parent)
                    pending.pop(path_key(item.src), None)
                    done.add(id(item))
                    planned = folder / item.dst.name
                    target = unique_path(planned)  # checagem final contra sobrescrita
                    if target != item.dst or item.renamed:
                        res.renamed += 1
                    shutil.move(str(item.src), str(target))
                    journal.add("move", item.src, target, item.size, digest)
                    stashed.pop(id(item), None)
                    res.moved += 1
                elif item.action is Action.TRASH:
                    trash_item(item)
            except Cancelled:
                raise
            except Exception as exc:  # erro em UM arquivo não para os outros
                log.warning("Falha em %s: %s", item.src, exc)
                res.errors.append((str(item.src), str(exc)))
            if n % SAVE_EVERY == 0:
                journal.save()
    except Cancelled:
        res.cancelled = True
        status = "cancelled"
    except BaseException:
        _unstash(stashed)
        journal.finish("error")
        raise
    _unstash(stashed)
    journal.finish(status)
    log.info("Organização concluída em %s: %d movidos, %d na lixeira, %d erros",
             plan.root, res.moved, res.trashed, len(res.errors))
    return res
