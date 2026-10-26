"""Ícones do Orguine: geral (robô com caixas) e favicon (rosto do robô) do cabeçalho."""

from __future__ import annotations

from PySide6.QtGui import QIcon

from ..paths import resource_path


def _icon(*names: str) -> QIcon:
    icon = QIcon()
    for name in names:
        p = resource_path(name)
        if p.exists():
            icon.addFile(str(p))
    return icon


def app_icon() -> QIcon:
    """Ícone geral (janela, barra de tarefas, executável)."""
    return _icon("orguine_icon.ico", "orguine_icon.png")


def header_icon() -> QIcon:
    """Logo pequeno no topo da janela."""
    return _icon("orguine_favicon.ico", "orguine_favicon.png")
