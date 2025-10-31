from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon
from PyQt5.QtCore import Qt

def white_svg_icon(path: str, size: int = 18) -> QIcon:
    renderer = QSvgRenderer(path)

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()

    # 색 덮어씌우기 (흰색)
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor("#FFFFFF"))
    painter.end()

    return QIcon(pixmap)
