"""Efeitos neon animados (cor #6ff8c8 do robozinho do Orguine) misturados ao roxo do tema.

Tudo é movido por um único ``QTimer`` compartilhado (``NeonAnimator``), a ~30 fps,
que para sozinho quando a janela está oculta/minimizada ou quando o usuário
desliga as animações. Cada widget só se redesenha quando precisa.
"""

from __future__ import annotations

import math
import os

from PySide6.QtCore import (QElapsedTimer, QEasingCurve, QEvent, QObject, QPropertyAnimation, QRectF, Qt,
                            QTimer, Signal)
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QProgressBar, QPushButton, QTabBar, QWidget

NEON = "#6FF8C8"

# Cores por tema: o neon "puro" brilha melhor no escuro; no claro usamos um tom mais
# profundo para as linhas (contraste) e o neon puro só como brilho.
NEON_COLORS = {
    "dark": {"neon": "#6FF8C8", "line": "#6FF8C8", "accent": "#7C6CF0", "track": "#1F2330", "glow_alpha": 150, "base_alpha": 150},
    "light": {"neon": "#6FF8C8", "line": "#14B886", "accent": "#6A5AE0", "track": "#E6E8F2", "glow_alpha": 190, "base_alpha": 230},
}


def animations_disabled_by_env() -> bool:
    return os.environ.get("ORGUINE_NO_ANIM", "").strip().lower() in {"1", "true", "yes", "sim"}


def qcolor(hex_: str, alpha: int = 255) -> QColor:
    c = QColor(hex_)
    c.setAlpha(max(0, min(255, int(alpha))))
    return c


class NeonAnimator(QObject):
    """Relógio compartilhado das animações."""

    tick = Signal(float)
    changed = Signal()  # tema ou liga/desliga mudou

    FPS = 30

    def __init__(self, parent: QObject | None = None, enabled: bool = True) -> None:
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setInterval(1000 // self.FPS)
        self._timer.setTimerType(Qt.CoarseTimer)
        self._timer.timeout.connect(self._emit)
        self._clock = QElapsedTimer()
        self._clock.start()
        self._enabled = bool(enabled) and not animations_disabled_by_env()
        self._active = False
        self.theme = "dark"

    # --------------------------------------------------------------- estado
    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def running(self) -> bool:
        return self._timer.isActive()

    def set_enabled(self, on: bool) -> None:
        on = bool(on) and not animations_disabled_by_env()
        if on != self._enabled:
            self._enabled = on
            self._sync()
            self.changed.emit()

    def set_active(self, on: bool) -> None:
        """Janela visível? (pausa quando oculta ou minimizada)."""
        self._active = bool(on)
        self._sync()

    def set_theme(self, theme: str) -> None:
        self.theme = theme if theme in NEON_COLORS else "dark"
        self.changed.emit()

    def colors(self) -> dict:
        return NEON_COLORS[self.theme]

    def time(self) -> float:
        return self._clock.elapsed() / 1000.0

    def _sync(self) -> None:
        if self._enabled and self._active:
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()

    def _emit(self) -> None:
        self.tick.emit(self.time())


class _Animated:
    """Mixin: conecta o widget ao relógio e redesenha só quando visível."""

    def _attach(self, animator: NeonAnimator) -> None:
        self._anim = animator
        animator.tick.connect(self._on_tick)
        animator.changed.connect(self.update)

    def _on_tick(self, t: float) -> None:  # pode ser sobrescrito
        if self.isVisible():
            self.update()


def _streak_gradient(x0: float, x1: float, color: QColor, core: QColor | None = None) -> QLinearGradient:
    g = QLinearGradient(x0, 0, x1, 0)
    clear = QColor(color)
    clear.setAlpha(0)
    g.setColorAt(0.0, clear)
    g.setColorAt(0.5, color)
    if core is not None:
        g.setColorAt(0.62, core)
    g.setColorAt(1.0, clear)
    return g


class NeonLine(QWidget, _Animated):
    """Linha fina sob o cabeçalho: degradê roxo→neon com faixas de luz correndo."""

    # (velocidade em larguras/s, comprimento em px, deslocamento de fase, intensidade)
    STREAKS = ((0.16, 150, 0.00, 1.0), (0.10, 90, 0.45, 0.7), (0.24, 46, 0.75, 0.85))

    def __init__(self, animator: NeonAnimator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(8)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._attach(animator)

    def paintEvent(self, _event) -> None:  # noqa: N802
        c = self._anim.colors()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        y = h / 2
        base = QLinearGradient(0, 0, w, 0)
        base.setColorAt(0.0, qcolor(c["accent"], 40))
        base.setColorAt(0.35, qcolor(c["accent"], c["base_alpha"]))
        base.setColorAt(0.7, qcolor(c["line"], c["base_alpha"]))
        base.setColorAt(1.0, qcolor(c["line"], 30))
        p.fillRect(QRectF(0, y - 1, w, 2), base)
        if not self._anim.enabled:
            return
        t = self._anim.time()
        for speed, length, offset, k in self.STREAKS:
            x = ((t * speed + offset) % 1.0) * (w + length * 2) - length
            p.fillRect(QRectF(x, y - 3.5, length, 7),
                       _streak_gradient(x, x + length, qcolor(c["neon"], 60 * k)))
            p.fillRect(QRectF(x, y - 1.5, length, 3),
                       _streak_gradient(x, x + length, qcolor(c["neon"], 255 * k), qcolor("#FFFFFF", 200 * k)))


class NeonProgressBar(QProgressBar, _Animated):
    """Barra de progresso roxo→neon com um brilho percorrendo o preenchimento."""

    def __init__(self, animator: NeonAnimator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTextVisible(False)
        self.setFixedHeight(10)
        self._attach(animator)

    def paintEvent(self, event) -> None:  # noqa: N802
        if not self._anim.enabled:
            super().paintEvent(event)  # animação padrão do Qt (barra "ocupada")
            return
        c = self._anim.colors()
        t = self._anim.time()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        rad = r.height() / 2
        track = QPainterPath()
        track.addRoundedRect(r, rad, rad)
        p.fillPath(track, qcolor(c["track"]))
        p.setClipPath(track)
        span = self.maximum() - self.minimum()
        if span <= 0:  # indeterminado: segmento que vai e volta
            seg = r.width() * 0.32
            pos = (math.sin(t * 2.4) + 1) / 2
            x0 = r.left() + pos * (r.width() - seg)
            chunk = QRectF(x0, r.top(), seg, r.height())
        else:
            frac = (self.value() - self.minimum()) / span
            chunk = QRectF(r.left(), r.top(), max(r.height(), r.width() * frac), r.height())
        g = QLinearGradient(chunk.left(), 0, chunk.right(), 0)
        g.setColorAt(0.0, qcolor(c["accent"]))
        g.setColorAt(1.0, qcolor(c["line"]))
        cp = QPainterPath()
        cp.addRoundedRect(chunk, rad, rad)
        p.fillPath(cp, g)
        # brilho correndo dentro do preenchimento
        sw = max(30.0, chunk.width() * 0.25)
        x = chunk.left() - sw + ((t * 0.9) % 1.0) * (chunk.width() + sw * 2)
        p.setClipPath(cp)
        p.fillRect(QRectF(x, r.top(), sw, r.height()),
                   _streak_gradient(x, x + sw, qcolor("#FFFFFF", 150), qcolor(c["neon"], 230)))


class NeonButton(QPushButton, _Animated):
    """Botão principal com um reflexo neon que atravessa de tempos em tempos."""

    PERIOD = 4.5
    SWEEP = 1.1

    def __init__(self, animator: NeonAnimator, phase: float = 0.0, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._phase = phase
        self._sweeping = False
        self._attach(animator)

    def _progress(self, t: float) -> float:
        return ((t + self._phase) % self.PERIOD) / self.SWEEP

    def _on_tick(self, t: float) -> None:
        sweeping = self.isVisible() and self.isEnabled() and self._progress(t) < 1.0
        if sweeping or self._sweeping:  # redesenha durante o reflexo e uma vez para limpá-lo
            self.update()
        self._sweeping = sweeping

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        if not (self._anim.enabled and self.isEnabled()):
            return
        prog = self._progress(self._anim.time())
        if prog >= 1.0:
            return
        c = self._anim.colors()
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        clip = QPainterPath()
        clip.addRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), 9, 9)
        p.setClipPath(clip)
        ease = QEasingCurve(QEasingCurve.InOutCubic).valueForProgress(prog)
        band = r.width() * 0.28
        x = -band + ease * (r.width() + band * 2) - band / 2
        p.translate(x, 0)
        p.shear(-0.35, 0)
        p.fillRect(QRectF(0, 0, band, r.height()),
                   _streak_gradient(0, band, qcolor(c["neon"], 120), qcolor("#FFFFFF", 90)))


class NeonTabBar(QTabBar, _Animated):
    """Abas com sublinhado roxo→neon e uma faixa de luz correndo na aba ativa."""

    def __init__(self, animator: NeonAnimator, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDrawBase(False)
        self._attach(animator)

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        i = self.currentIndex()
        if i < 0:
            return
        c = self._anim.colors()
        r = QRectF(self.tabRect(i))
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        y = r.bottom() - 2
        line = QRectF(r.left() + 6, y, r.width() - 12, 2.5)
        g = QLinearGradient(line.left(), 0, line.right(), 0)
        g.setColorAt(0.0, qcolor(c["accent"]))
        g.setColorAt(1.0, qcolor(c["line"]))
        path = QPainterPath()
        path.addRoundedRect(line, 1.2, 1.2)
        p.fillPath(path, g)
        if not self._anim.enabled:
            return
        t = self._anim.time()
        sw = max(24.0, line.width() * 0.35)
        x = line.left() - sw + ((t * 0.55) % 1.0) * (line.width() + sw * 2)
        p.setClipRect(QRectF(line.left(), y - 4, line.width(), 10))
        p.fillRect(QRectF(x, y - 2.5, sw, 7.5), _streak_gradient(x, x + sw, qcolor(c["neon"], 70)))
        p.fillRect(QRectF(x, y, sw, 2.5), _streak_gradient(x, x + sw, qcolor("#FFFFFF", 230), qcolor(c["neon"])))


class HoverGlow(QObject):
    """Brilho neon suave (sombra colorida) que acende ao passar o mouse.

    O efeito só existe enquanto o mouse está sobre o widget (e durante o apagar),
    para não custar nada no resto do tempo.
    """

    def __init__(self, widget: QWidget, animator: NeonAnimator, radius: float = 26.0) -> None:
        super().__init__(widget)
        self._w = widget
        self._anim_clock = animator
        self._radius = radius
        self._effect: QGraphicsDropShadowEffect | None = None
        self._fade: QPropertyAnimation | None = None
        widget.setAttribute(Qt.WA_Hover, True)
        widget.installEventFilter(self)

    def _ensure(self) -> QGraphicsDropShadowEffect:
        if self._effect is None:
            eff = QGraphicsDropShadowEffect(self._w)
            eff.setOffset(0, 0)
            eff.setBlurRadius(0)
            eff.setColor(qcolor(NEON, self._anim_clock.colors()["glow_alpha"]))
            self._w.setGraphicsEffect(eff)  # o widget passa a ser dono do efeito
            self._effect = eff
        return self._effect

    def _drop(self) -> None:
        if self._effect is not None:
            self._w.setGraphicsEffect(None)
            self._effect = None
            self._fade = None

    def _animate(self, end: float) -> None:
        eff = self._ensure()
        if self._fade is not None:
            self._fade.stop()
        fade = QPropertyAnimation(eff, b"blurRadius", self)
        fade.setDuration(220 if end else 320)
        fade.setStartValue(eff.blurRadius())
        fade.setEndValue(end)
        fade.setEasingCurve(QEasingCurve.OutCubic)
        if not end:
            fade.finished.connect(self._drop)
        self._fade = fade
        fade.start()

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        et = event.type()
        if et == QEvent.Enter and self._w.isEnabled():
            if self._anim_clock.enabled:
                self._animate(self._radius)
        elif et in (QEvent.Leave, QEvent.Hide, QEvent.EnabledChange):
            if self._effect is not None:
                if self._anim_clock.enabled and et == QEvent.Leave:
                    self._animate(0)
                else:
                    self._drop()
        return False

