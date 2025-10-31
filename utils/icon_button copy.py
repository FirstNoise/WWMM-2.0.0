# utils/icon_button.py

import os
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QSize, QEvent
from PyQt5.QtGui import QPalette

from utils.icon_color import colorized_icon   # ← 기존과 동일하게 사용

def IconButton(icon_name: str, size=30, obj_name="IconButton"):
    button = QPushButton()
    button.setObjectName(obj_name)

    svg_path = os.path.join("resources", "icons", icon_name)
    button.svg_path = svg_path  # ← 나중에 다시 칠하기 위해 저장

    # (1) 초기 아이콘 설정
    initial_color = button.palette().color(QPalette.ButtonText)
    button.setIcon(colorized_icon(svg_path, initial_color))
    button.setIconSize(QSize(size, size))
    button.setFlat(True)

    # (2) QSS 스타일 적용 이후에 아이콘을 다시 칠하도록 event 재정의
    def repaint_after_style(event):
        if event.type() == QEvent.Polish:  # ← 스타일 적용 완료 시점
            new_color = button.palette().color(QPalette.ButtonText)
            button.setIcon(colorized_icon(button.svg_path, new_color))
        return QPushButton.event(button, event)

    button.event = repaint_after_style

    return button
