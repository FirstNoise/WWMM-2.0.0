# ui/components/topbar.py
import os

from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QIcon

from utils.styled_widget import StyledWidget   # ✅ 변경됨
from utils.svg_icon import white_svg_icon
from utils.icon_button import IconButton


ICON = lambda name: QIcon(os.path.join("resources", "icons", name))

class TopBar(StyledWidget):  # ✅ QWidget → StyledWidget
    qss = "topbar.qss"       # ✅ QSS 자동 적용
    object_name = "TopBar"   # ✅ ObjectName 자동 적용
    
    """
    ✅ 이제 이 TopBar 는 진짜 TitleBar 로 동작
    - 창 이동
    - 최소화 / 최대화 / 닫기 버튼 포함
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        # 제목
        self.title = QLabel("WWWMM - Wuthering Waves Mod Manager 2.0.0")
        self.title.setObjectName("TitleLabel")

        # ✅ 주요 기능 버튼 (IconButton 사용)
        self.btn_start = IconButton("start.svg")
        self.btn_settings = IconButton("settings.svg")
        self.btn_add_mod = IconButton("add.svg")
        self.btn_unapply_all = IconButton("link_disconnect.svg")

        # ✅ 창 버튼들 (obj_name 변경 적용)
        self.btn_min = IconButton("subtract.svg", obj_name="WindowButton")
        self.btn_max = IconButton("square.svg", obj_name="WindowButton")
        self.btn_close = IconButton("close.svg", obj_name="CloseButton")

        # 레이아웃 구성
        layout.addWidget(self.title)
        layout.addStretch()

        layout.addWidget(self.btn_add_mod)
        layout.addWidget(self.btn_unapply_all)
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_settings)

        layout.addSpacing(16)
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

        # 창 동작 연결
        self.btn_min.clicked.connect(lambda: self.parent_window.showMinimized())
        self.btn_max.clicked.connect(
            lambda: self.parent_window.showNormal()
            if self.parent_window.isMaximized()
            else self.parent_window.showMaximized()
        )
        self.btn_close.clicked.connect(self.parent_window.close)

        self._drag_pos = None

    # 창 드래그 이동
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.pos()
            self._drag_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return

        # _drag_pos 초기화 안되었으면 그냥 return
        if self._drag_pos is None:
            return

        if self.parent_window.isMaximized():
            ratio = event.x() / self.width()
            new_width = self.parent_window.normalGeometry().width()
            
            self.parent_window.showNormal()

            new_x = int(event.globalX() - new_width * ratio)
            new_y = event.globalY() - self._drag_offset.y()

            self.parent_window.move(new_x, new_y)
            self._drag_pos = event.globalPos()
        else:
            diff = event.globalPos() - self._drag_pos
            self.parent_window.move(self.parent_window.pos() + diff)
            self._drag_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.parent_window.isMaximized():
                self.parent_window.showNormal()
            else:
                self.parent_window.showMaximized()