# ui/components/topbar.py

from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QPoint

from utils.styled_widget import StyledWidget   # ✅ 변경됨

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

        # 앱 이름
        self.title = QLabel("Wuthering Waves Mod Manager")
        self.title.setObjectName("TitleLabel")

        # 실행 버튼
        self.btn_start = QPushButton("Launch XXMI")
        self.btn_settings = QPushButton("Settings")

        # 창 버튼들
        self.btn_min = QPushButton("—")
        self.btn_max = QPushButton("⬜")
        self.btn_close = QPushButton("✕")

        # ✅ 스타일 적용을 위한 ObjectName 유지
        self.btn_min.setObjectName("WindowButton")
        self.btn_max.setObjectName("WindowButton")
        self.btn_close.setObjectName("CloseButton")

        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_settings)
        layout.addSpacing(20)
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)

        # 창 제어 시그널 연결
        self.btn_min.clicked.connect(lambda: self.parent_window.showMinimized())
        self.btn_max.clicked.connect(lambda: (
            self.parent_window.showMaximized()
            if not self.parent_window.isMaximized()
            else self.parent_window.showNormal()
        ))
        self.btn_close.clicked.connect(self.parent_window.close)

        self._drag_pos = None

    # ✅ 창 드래그 이동 처리
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self._drag_pos:
            diff = event.globalPos() - self._drag_pos
            self.parent_window.move(self.parent_window.x() + diff.x(), self.parent_window.y() + diff.y())
            self._drag_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
