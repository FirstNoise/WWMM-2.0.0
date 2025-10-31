# utils/icon_button.py

import os
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QSize, QEvent
from PyQt5.QtGui import QColor

from utils.icon_color import colorized_icon

def IconButton(icon_name: str, size=30, obj_name="IconButton"):
    button = QPushButton()
    button.setObjectName(obj_name)

    svg_path = os.path.join("resources", "icons", icon_name)
    button.svg_path = svg_path

    WHITE = QColor("#FFFFFF")   # ← 여기서 색 고정

    # (1) 초기 아이콘 = 무조건 흰색
    button.setIcon(colorized_icon(svg_path, WHITE))
    button.setIconSize(QSize(size, size))
    button.setFlat(True)

    # (2) QSS 적용 이후에도 항상 흰색 유지
    def repaint_after_style(event):
        if event.type() == QEvent.Polish:
            button.setIcon(colorized_icon(button.svg_path, WHITE))
        return QPushButton.event(button, event)

    button.event = repaint_after_style

    return button
