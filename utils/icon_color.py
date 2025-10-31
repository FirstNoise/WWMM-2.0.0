# utils/icon_color.py

from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtCore import Qt

def colorized_icon(svg_path: str, color: QColor):
    renderer = QSvgRenderer(svg_path)
    size = renderer.defaultSize()

    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)

    # 1) SVG를 원본 형태 그대로 렌더
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    # 2) 색 덮어씌우기 (핵심!!)
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()

    return QIcon(pixmap)
