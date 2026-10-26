"""Janela "Sobre" do Orguine, com botões para os links do autor e do projeto."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .. import DONATE_URL, GITHUB_PROFILE_URL, REPO_URL, SITE_URL, __version__
from ..i18n import tr
from .icons import app_icon
from .neon import NeonAnimator, NeonLine

# Ícones vetoriais simples (GitHub/repositório: Octicons, licença MIT).
_SVG = {
    "github": '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82'
              '-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 '
              '1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 '
              '0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 '
              '1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07'
              '-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 '
              '8.013 0 0016 8c0-4.42-3.58-8-8-8z" fill="{c}"/>',
    "repo": '<path d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 '
            '110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9zm10.5-1V9h-8'
            'c-.356 0-.694.074-1 .208V2.5a1 1 0 011-1h8zM5 12.25v3.25a.25.25 0 00.4.2l1.45-1.087a.25.25 0 01.3'
            ' 0L8.6 15.7a.25.25 0 00.4-.2v-3.25a.25.25 0 00-.25-.25h-3.5a.25.25 0 00-.25.25z" fill="{c}"/>',
    "site": '<g fill="none" stroke="{c}" stroke-width="1.3"><circle cx="8" cy="8" r="6.6"/>'
            '<ellipse cx="8" cy="8" rx="2.9" ry="6.6"/><path d="M1.6 5.6h12.8M1.6 10.4h12.8"/></g>',
    "donate": '<path d="M8 14.2S1.6 10.4 1.6 5.9C1.6 3.6 3.3 2 5.3 2c1.2 0 2.1.6 2.7 1.4C8.6 2.6 9.5 2 10.7 2'
              'c2 0 3.7 1.6 3.7 3.9 0 4.5-6.4 8.3-6.4 8.3z" fill="{c}"/>',
}


def svg_icon(name: str, color: str, size: int = 18) -> QIcon:
    data = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">{_SVG[name].format(c=color)}</svg>'
    renderer = QSvgRenderer(QByteArray(data.encode()))
    pm = QPixmap(size * 3, size * 3)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    renderer.render(p, QRectF(0, 0, pm.width(), pm.height()))
    p.end()
    return QIcon(pm)


LINKS = (  # (chave do texto, url, ícone, objectName)
    ("about.github", GITHUB_PROFILE_URL, "github", "LinkBtn"),
    ("about.repo", REPO_URL, "repo", "LinkBtn"),
    ("about.site", SITE_URL, "site", "LinkBtn"),
    ("about.donate", DONATE_URL, "donate", "Donate"),
)


class AboutDialog(QDialog):
    def __init__(self, parent, animator: NeonAnimator, theme: str) -> None:
        super().__init__(parent)
        self.setObjectName("About")
        self.setWindowTitle(tr("about.title"))
        self.setModal(True)
        self.setMinimumWidth(460)
        dark = theme == "dark"
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 22)
        lay.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(16)
        logo = QLabel()
        logo.setPixmap(app_icon().pixmap(96, 96))
        top.addWidget(logo, 0, Qt.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(2)
        name = QLabel("Orguine")
        name.setObjectName("AboutName")
        version = QLabel(tr("about.version", version=__version__))
        version.setObjectName("Badge")
        tagline = QLabel(tr("about.tagline"))
        tagline.setObjectName("Muted")
        tagline.setWordWrap(True)
        col.addWidget(name)
        col.addWidget(version, 0, Qt.AlignLeft)
        col.addSpacing(6)
        col.addWidget(tagline)
        col.addStretch(1)
        top.addLayout(col, 1)
        lay.addLayout(top)

        lay.addWidget(NeonLine(animator, self))
        credits = QLabel(tr("about.credits"))
        credits.setObjectName("Muted")
        credits.setWordWrap(True)
        lay.addWidget(credits)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)
        self.link_buttons: dict[str, QPushButton] = {}
        icon_color = "#E6E8EF" if dark else "#1B1E2B"
        for n, (key, url, icon, obj) in enumerate(LINKS):
            b = QPushButton(tr(key))
            b.setObjectName(obj)
            b.setCursor(Qt.PointingHandCursor)
            b.setIcon(svg_icon(icon, "#FFFFFF" if obj == "Donate" else icon_color))
            b.setIconSize(QSize(18, 18))
            b.setToolTip(url)
            b.setProperty("url", url)
            b.clicked.connect(lambda _=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            grid.addWidget(b, n // 2, n % 2)
            self.link_buttons[key] = b
        lay.addSpacing(4)
        lay.addLayout(grid)

        close = QPushButton(tr("about.close"))
        close.setObjectName("Ghost")
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(close)
        lay.addSpacing(4)
        lay.addLayout(row)
