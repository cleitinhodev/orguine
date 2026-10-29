"""Nome das pastas de destino: só ganham " (2)" quando o nome está ocupado por algo que FICA."""

import json
import os
import unicodedata
from datetime import datetime

import pytest

from conftest import make
from orguine.core import DupStrategy, Mode, PlanOptions, build_plan, execute_plan, undo_journal
from orguine.core import executor as executor_mod

T2020 = datetime(2020, 4, 10, 12).timestamp()
T2021 = datetime(2021, 1, 10, 12).timestamp()
T2023 = datetime(2023, 5, 10, 12).timestamp()


def rel(plan, name):
    item = next(i for i in plan.items if unicodedata.normalize("NFC", i.src.name) == name)
    if item.dst is None:
        return None
    return unicodedata.normalize("NFC", item.dst.relative_to(plan.root).as_posix())


def snapshot(folder):
    return {unicodedata.normalize("NFC", p.relative_to(folder).as_posix()): p.read_bytes()
            for p in folder.rglob("*") if p.is_file()}


def no_temp_left(folder):
    return not [p for p in folder.rglob("*") if ".orguine-tmp-" in p.name]


# ------------------------------------------------------------------ prévia
@pytest.mark.parametrize("mode,blocker,other,expected_other,expected_blocker", [
    (Mode.ALPHABET, "A", "abacate.txt", "A/abacate.txt", "A/A"),
    (Mode.ALPHABET, "0-9", "123.txt", "0-9/123.txt", "0-9/0-9"),
    (Mode.ALPHABET, "Outros", "_x.txt", "Outros/_x.txt", "O/Outros"),
    (Mode.CATEGORY, "Documentos", "doc.pdf", "Documentos/doc.pdf", "Outros/Documentos"),
    (Mode.CATEGORY, "Outros", "x.xyz", "Outros/x.xyz", "Outros/Outros"),
    (Mode.EXTENSION, "PDF", "doc.pdf", "PDF/doc.pdf", "Sem extensão/PDF"),
    (Mode.DATE, "2023", "nota.txt", "2023/05/nota.txt", "2020/04/2023"),
])
def test_no_suffix_when_blocking_file_is_moved(folder, mode, blocker, other, expected_other,
                                               expected_blocker):
    make(folder, blocker, "bloqueador", mtime=T2020)
    make(folder, other, "outro", mtime=T2023)
    plan = build_plan(folder, PlanOptions(mode=mode, use_exif=False))
    assert rel(plan, other) == expected_other
    assert rel(plan, blocker) == expected_blocker
    assert not any(" (2)" in str(i.dst) for i in plan.moves)


def test_suffix_when_blocking_file_stays_sensitive(folder):
    make(folder, "PIN", "segredo")          # sensível: fica onde está
    make(folder, "algo.pin", "dados")
    plan = build_plan(folder, PlanOptions(mode=Mode.EXTENSION))
    assert rel(plan, "PIN") is None
    assert rel(plan, "algo.pin") == "PIN (2)/algo.pin"
    # incluindo sensíveis, o arquivo PIN também sai: pasta com o nome simples
    plan = build_plan(folder, PlanOptions(mode=Mode.EXTENSION, include_sensitive=True))
    assert rel(plan, "algo.pin") == "PIN/algo.pin"
    assert rel(plan, "PIN") == "Sem extensão/PIN"


def test_suffix_when_blocking_file_stays_duplicate_skip(folder):
    make(folder, "abc.txt", "mesmo", mtime=T2020)   # mais antigo: é o que fica como original
    make(folder, "A", "mesmo", mtime=T2023)         # duplicado "ignorar": fica onde está
    plan = build_plan(folder, PlanOptions(mode=Mode.ALPHABET, duplicates=DupStrategy.SKIP))
    assert rel(plan, "A") is None
    assert rel(plan, "abc.txt") == "A (2)/abc.txt"
    # duplicado indo para a lixeira também libera o nome
    plan = build_plan(folder, PlanOptions(mode=Mode.ALPHABET, duplicates=DupStrategy.TRASH))
    assert rel(plan, "abc.txt") == "A/abc.txt"


def test_suffix_when_blocker_is_not_part_of_plan_nested_date(folder):
    make(folder, "2023/05", "arquivo sem extensão dentro de 2023", mtime=T2021)
    make(folder, "nota.txt", "n", mtime=T2023)
    plan = build_plan(folder, PlanOptions(mode=Mode.DATE))  # sem subpastas: 2023/05 fica
    assert rel(plan, "nota.txt") == "2023/05 (2)/nota.txt"
    plan = build_plan(folder, PlanOptions(mode=Mode.DATE, recursive=True))  # agora ele sai
    assert rel(plan, "nota.txt") == "2023/05/nota.txt"
    assert rel(plan, "05") == "2021/01/05"


def test_symlink_named_like_folder_stays(folder):
    target = make(folder, "sub/alvo.txt", "x")
    try:
        os.symlink(target, folder / "A")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks indisponíveis")
    make(folder, "abacate.txt")
    plan = build_plan(folder, PlanOptions(mode=Mode.ALPHABET))
    assert rel(plan, "abacate.txt") == "A (2)/abacate.txt"


def test_existing_folder_is_reused(folder):
    make(folder, "A/ja_estava.txt")
    make(folder, "abacate.txt")
    plan = build_plan(folder, PlanOptions(mode=Mode.ALPHABET))
    assert rel(plan, "abacate.txt") == "A/abacate.txt"


def test_existing_folder_with_other_case_is_reused(folder):
    make(folder, "imagens/velha.jpg", "v")
    make(folder, "nova.jpg", "n")
    plan = build_plan(folder, PlanOptions(mode=Mode.CATEGORY))
    assert rel(plan, "nova.jpg") == "imagens/nova.jpg"
    make(folder, "o/antigo.txt", "a")
    make(folder, "Ótimo.txt", "o")
    plan = build_plan(folder, PlanOptions(mode=Mode.ALPHABET))
    assert rel(plan, "Ótimo.txt") == "o/Ótimo.txt"


def test_lowercase_file_blocking_capitalized_folder(folder):
    make(folder, "imagens", "arquivo sem extensão")     # vai para Outros
    make(folder, "foto.jpg", "f")
    plan = build_plan(folder, PlanOptions(mode=Mode.CATEGORY))
    assert rel(plan, "foto.jpg") == "Imagens/foto.jpg"
    assert rel(plan, "imagens") == "Outros/imagens"


def test_names_freed_by_plan_in_recursive_mode(folder):
    make(folder, "sub/A", "a-da-subpasta", mtime=T2020)
    make(folder, "A", "a-da-raiz", mtime=T2021)
    make(folder, "abacate.txt", "x")
    plan = build_plan(folder, PlanOptions(mode=Mode.ALPHABET, recursive=True))
    dests = sorted(rel(plan, n) if n != "A" else None for n in ["abacate.txt"])
    assert dests == ["A/abacate.txt"]
    assert sorted(i.dst.relative_to(folder).as_posix() for i in plan.moves) == \
        ["A/A", "A/A (1)", "A/abacate.txt"]


# ------------------------------------------------------------------ execução + desfazer
CASES = [
    (Mode.ALPHABET, False, {"A": ("bloqueador", T2020), "abacate.txt": ("x", T2023)},
     {"A/A", "A/abacate.txt"}),
    (Mode.CATEGORY, False, {"Documentos": ("b", T2020), "Outros": ("o", T2020), "doc.pdf": ("d", T2023)},
     {"Outros/Documentos", "Outros/Outros", "Documentos/doc.pdf"}),
    (Mode.EXTENSION, False, {"PDF": ("b", T2020), "doc.pdf": ("d", T2023)},
     {"Sem extensão/PDF", "PDF/doc.pdf"}),
    (Mode.DATE, False, {"2023": ("b", T2023), "nota.txt": ("n", T2023)},
     {"2023/05/2023", "2023/05/nota.txt"}),
    (Mode.DATE, True, {"2023/05": ("b", T2023), "nota.txt": ("n", T2023)},
     {"2023/05/05", "2023/05/nota.txt"}),
]


@pytest.mark.parametrize("mode,recursive,files,expected", CASES)
def test_execute_and_undo_roundtrip(folder, mode, recursive, files, expected):
    for name, (content, mtime) in files.items():
        make(folder, name, content, mtime=mtime)
    before = snapshot(folder)
    plan = build_plan(folder, PlanOptions(mode=mode, recursive=recursive, use_exif=False))
    assert {i.dst.relative_to(folder).as_posix() for i in plan.moves} == expected
    res = execute_plan(plan)
    assert not res.errors and res.renamed == 0
    assert set(snapshot(folder)) == expected
    assert no_temp_left(folder)
    data = json.loads(res.journal_path.read_text(encoding="utf-8"))
    assert any(e["op"] == "stash" for e in data["entries"])  # o nome provisório ficou registrado

    r = undo_journal(res.journal_path)
    assert not r.errors and not r.missing and r.renamed == 0
    assert snapshot(folder) == before
    assert no_temp_left(folder)


def test_blocking_duplicate_is_trashed_first(folder):
    make(folder, "abc.txt", "mesmo", mtime=T2020)
    make(folder, "A", "mesmo", mtime=T2023)
    trashed = []

    def fake_trash(p):
        trashed.append(os.path.basename(p))
        os.remove(p)

    plan = build_plan(folder, PlanOptions(mode=Mode.ALPHABET, duplicates=DupStrategy.TRASH))
    res = execute_plan(plan, trash_func=fake_trash)
    assert not res.errors and trashed == ["A"]
    assert set(snapshot(folder)) == {"A/abc.txt"}


class Crash(BaseException):
    pass


def test_crash_after_stash_is_undoable(folder, monkeypatch):
    make(folder, "A", "bloqueador")
    make(folder, "abacate.txt", "x")
    before = snapshot(folder)
    plan = build_plan(folder, PlanOptions(mode=Mode.ALPHABET))
    real_move = executor_mod.shutil.move

    def crashing_move(src, dst):
        if ".orguine-tmp-" in src:
            raise Crash()
        return real_move(src, dst)

    monkeypatch.setattr(executor_mod.shutil, "move", crashing_move)
    with pytest.raises(Crash):
        execute_plan(plan)
    monkeypatch.setattr(executor_mod.shutil, "move", real_move)
    # o arquivo "A" está com o nome provisório (a pasta A ocupa o nome), mas o diário sabe
    assert not no_temp_left(folder)
    r = undo_journal()
    assert not r.errors
    assert snapshot(folder) == before and no_temp_left(folder)


def test_failed_rename_before_stash_keeps_names(folder, monkeypatch):
    make(folder, "A", "bloqueador")
    make(folder, "abacate.txt", "x")
    before = snapshot(folder)
    plan = build_plan(folder, PlanOptions(mode=Mode.ALPHABET))

    def broken_rename(a, b):
        raise PermissionError("negado")

    monkeypatch.setattr(executor_mod.os, "rename", broken_rename)
    res = execute_plan(plan)
    monkeypatch.undo()
    assert res.errors  # o "A" não pôde sair do caminho
    assert (folder / "A").is_file()  # nome original intacto
    assert (folder / "A (2)/abacate.txt").exists()  # pasta com sufixo como último recurso
    r = undo_journal(res.journal_path)
    assert not r.errors
    assert snapshot(folder) == before and no_temp_left(folder)


def test_existing_nested_date_folders_are_reused(folder):
    make(folder, "2023/05/antigo.txt", "a", mtime=T2021)
    make(folder, "nota.txt", "n", mtime=T2023)
    plan = build_plan(folder, PlanOptions(mode=Mode.DATE))
    assert rel(plan, "nota.txt") == "2023/05/nota.txt"
    res = execute_plan(plan)
    assert not res.errors and (folder / "2023/05/nota.txt").exists()
    assert not json.loads(res.journal_path.read_text(encoding="utf-8"))["created_dirs"]
