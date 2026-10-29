"""Teste de fumaça da interface (roda com QT_QPA_PLATFORM=offscreen)."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("pytestqt")
pytest.importorskip("PySide6.QtCharts")

from PySide6.QtCore import QSettings  # noqa: E402
from PySide6.QtWidgets import QMessageBox  # noqa: E402

from conftest import make  # noqa: E402


@pytest.fixture
def window(qtbot, tmp_path, monkeypatch):
    from orguine.gui.main_window import MainWindow

    settings = QSettings(str(tmp_path / "s.ini"), QSettings.IniFormat)
    w = MainWindow(settings)
    qtbot.addWidget(w)
    monkeypatch.setattr(QMessageBox, "exec", lambda self: QMessageBox.Ok)
    return w


def wait_idle(qtbot, w):
    qtbot.waitUntil(lambda: w.worker is None, timeout=10_000)


def test_full_flow_preview_organize_undo(window, qtbot, folder, monkeypatch):
    make(folder, "a.jpg")
    make(folder, "b.pdf")
    make(folder, "senha.txt")
    asked = []
    monkeypatch.setattr(type(window), "_ask", lambda self, title, *a, **k: asked.append(title) or True)

    window.folder_edit.setText(str(folder))
    window.analyze()
    wait_idle(qtbot, window)
    assert window.plan is not None and window.plan.summary()["move"] == 2
    assert window.stats["sensitive"].value.text() == "1"
    assert window.table.model.rowCount() == 3
    assert window.tree.topLevelItemCount() >= 1
    assert (folder / "a.jpg").exists()  # prévia não move nada

    window.organize()
    wait_idle(qtbot, window)
    assert (folder / "Imagens/a.jpg").exists()
    assert (folder / "senha.txt").exists()  # sensível ficou no lugar
    assert asked  # confirmação foi pedida

    window.undo()
    wait_idle(qtbot, window)
    assert (folder / "a.jpg").exists() and not (folder / "Imagens").exists()


def test_blocked_folder_shows_error(window, monkeypatch):
    errors = []
    monkeypatch.setattr(type(window), "_error", lambda self, t, m: errors.append(m))
    window.folder_edit.setText(os.path.abspath(os.sep))
    window.analyze()
    assert errors and window.plan is None


def test_language_and_theme_switch(window):
    window.lang_combo.setCurrentIndex(window.lang_combo.findData("en"))
    assert window.analyze_btn.text() == "Analyze and preview"
    window.apply_theme("light")
    window.apply_theme("dark")


def test_about_dialog_has_link_buttons(window, monkeypatch):
    from PySide6.QtWidgets import QDialog

    from orguine import DONATE_URL, GITHUB_PROFILE_URL, REPO_URL, SITE_URL
    from orguine.gui.about import AboutDialog

    opened = []
    monkeypatch.setattr("orguine.gui.about.QDesktopServices.openUrl", lambda url: opened.append(url.toString()))
    monkeypatch.setattr(QDialog, "exec", lambda self: 0)
    window.open_about()
    dlg = window._about
    assert isinstance(dlg, AboutDialog)
    urls = [b.property("url") for b in dlg.link_buttons.values()]
    assert urls == [GITHUB_PROFILE_URL, REPO_URL, SITE_URL, DONATE_URL]
    assert dlg.link_buttons["about.github"].text() == "Meu GitHub"
    dlg.link_buttons["about.donate"].click()
    assert opened == [DONATE_URL]


def test_animations_toggle_and_pause(window, qtbot):
    window.show()
    qtbot.waitExposed(window)
    assert window.animator.enabled and window.animator.running
    window.anim_cb.setChecked(False)
    assert not window.animator.running
    assert window.settings.value("animations", type=bool) is False
    window.anim_cb.setChecked(True)
    assert window.animator.running
    window.hide()  # janela oculta => animação pausada (sem gastar CPU)
    assert not window.animator.running
    window.show()
    assert window.animator.running


def test_window_title_and_icon(window):
    assert window.windowTitle().startswith("Orguine")
    assert not window.windowIcon().isNull()
    assert not window.logo.pixmap().isNull()


# ---------------------------------------------------------------- prévia ao vivo
def _analyzed(window, qtbot, folder):
    window.folder_edit.setText(str(folder))
    window.analyze()
    wait_idle(qtbot, window)
    assert window.plan is not None
    return window.plan


def wait_refreshed(qtbot, w, check):
    qtbot.waitUntil(lambda: w.worker is None and not w._refresh_timer.isActive()
                    and w.plan is not None and check(w.plan), timeout=10_000)


def test_mode_change_refreshes_preview(window, qtbot, folder):
    from orguine.core import Mode

    make(folder, "a.jpg")
    make(folder, "b.pdf")
    old = _analyzed(window, qtbot, folder)
    assert old.options.mode is Mode.CATEGORY

    window.mode_radios[1].click()  # Tipo (extensão)
    # Enquanto espera, a prévia antiga continua visível (apagada), não some.
    assert window.plan is old
    assert window.tree_stack.currentIndex() == 1
    assert not window.table.isEnabled()
    assert not window.organize_btn.isEnabled()
    assert window.status_label.text() == "Atualizando prévia…"

    wait_refreshed(qtbot, window, lambda p: p.options.mode is Mode.EXTENSION)
    dsts = {i.dst.parent.name for i in window.plan.moves}
    assert dsts == {"JPG", "PDF"}
    assert window.table.isEnabled() and window.organize_btn.isEnabled()
    assert window.table.model.rowCount() == 2
    assert (folder / "a.jpg").exists() and (folder / "b.pdf").exists()  # nada foi movido


def test_option_changes_refresh_preview(window, qtbot, folder):
    from orguine.core import DupStrategy

    make(folder, "a.jpg", b"igual")
    make(folder, "b.jpg", b"igual")
    make(folder, "sub/c.pdf", b"pdf")
    make(folder, "senha.txt", b"segredo")
    plan = _analyzed(window, qtbot, folder)
    assert len(plan.items) == 3

    window.recursive_cb.setChecked(True)
    wait_refreshed(qtbot, window, lambda p: p.options.recursive)
    assert len(window.plan.items) == 4

    window.sensitive_cb.setChecked(True)
    wait_refreshed(qtbot, window, lambda p: p.options.include_sensitive)
    assert any(i.src.name == "senha.txt" and i.dst is not None for i in window.plan.items)

    window.dup_combo.setCurrentIndex(3)  # lixeira (manter o mais antigo)
    wait_refreshed(qtbot, window, lambda p: p.options.duplicates is DupStrategy.TRASH)
    assert window.plan.summary()["trash"] == 1
    assert window.stats["total"].value.text() == "4"
    assert (folder / "a.jpg").exists() and (folder / "b.jpg").exists()  # nunca executa sozinho


def test_rapid_changes_are_debounced_and_cancel_running_analysis(window, qtbot, folder, monkeypatch):
    from orguine.core import Mode
    import orguine.gui.main_window as mw

    make(folder, "a.jpg")
    _analyzed(window, qtbot, folder)
    calls = []
    real = mw.build_plan
    monkeypatch.setattr(mw, "build_plan", lambda *a, **k: calls.append(a[1]) or real(*a, **k))
    for idx in (1, 2, 3, 0, 2):
        window.mode_radios[idx].click()
    wait_refreshed(qtbot, window, lambda p: p.options.mode is Mode.DATE)
    assert len(calls) == 1  # só uma análise depois da rajada de cliques

    # Mudança durante uma análise em andamento: cancela e refaz com a opção nova.
    window.analyze(refresh=True)
    assert window.worker is not None
    window.mode_radios[3].click()
    window._refresh_timer.timeout.emit()
    wait_refreshed(qtbot, window, lambda p: p.options.mode is Mode.ALPHABET)
    assert window.plan.options.mode is Mode.ALPHABET
    assert not window._pending_organize


def test_settings_that_do_not_affect_plan_keep_preview(window, qtbot, folder):
    make(folder, "a.jpg")
    plan = _analyzed(window, qtbot, folder)
    window.apply_theme("light")
    window.anim_cb.setChecked(not window.anim_cb.isChecked())
    window.backup_combo.setCurrentIndex(1)
    window.folder_edit.setText(str(folder) + " ")  # mesma pasta
    qtbot.wait(450)
    assert window.plan is plan and window.worker is None
    assert window.table.isEnabled() and window.organize_btn.isEnabled()


def test_language_change_refreshes_folder_names(window, qtbot, folder):
    make(folder, "a.jpg")
    _analyzed(window, qtbot, folder)
    assert window.plan.moves[0].dst.parent.name == "Imagens"
    window.lang_combo.setCurrentIndex(window.lang_combo.findData("en"))
    wait_refreshed(qtbot, window, lambda p: p.options.lang == "en")
    assert window.plan.moves[0].dst.parent.name == "Images"


def test_changing_folder_clears_preview(window, qtbot, folder, tmp_path):
    make(folder, "a.jpg")
    _analyzed(window, qtbot, folder)
    window.folder_edit.setText(str(tmp_path / "outra"))
    assert window.plan is None
    window.mode_radios[2].click()
    qtbot.wait(450)
    assert window.plan is None and window.worker is None  # sem pasta analisada, nada a refazer
