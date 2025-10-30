# ui/dialogs/settings_dialog.py
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from utils.styled_dialog import StyledDialog


class SettingsDialog(StyledDialog):
    # ✅ QSS와 스타일 클래스 이름 지정 (StyledDialog에서 자동 로딩됨)
    class_name = "SettingsDialog"
    qss = "settings_dialog.qss"

    def __init__(self, parent=None, wwmi_path="", xxmi_path=""):
        super().__init__(parent)

        # ✅ 테두리 없는 프레임 + 모달 다이얼로그
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)

        # ✅ 크기 제약 설정
        self.setMinimumWidth(720)
        self.setSizeGripEnabled(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ✅ 메인 레이아웃
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # ----------------------------------------------------
        # Header (제목 + 닫기 버튼)
        # ----------------------------------------------------
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 6)

        title = QLabel("Settings")
        title.setObjectName("DialogTitle")  # QSS에서 스타일 지정

        btn_close = QPushButton("✕")
        btn_close.setObjectName("CloseButton")  # QSS에서 스타일 지정
        btn_close.clicked.connect(self.close)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(btn_close)
        layout.addLayout(header)

        # ----------------------------------------------------
        # WWMI Path 입력 필드
        # ----------------------------------------------------
        wwmi_layout = QHBoxLayout()
        wwmi_layout.setSpacing(8)

        label_wwmi = QLabel("WWMI Path:")
        self.path_edit = QLineEdit(self)
        self.path_edit.setText(wwmi_path)
        self.path_edit.textChanged.connect(self.update_dialog_width)

        btn_browse_wwmi = QPushButton("Browse...")
        btn_browse_wwmi.clicked.connect(self.select_wwmi_folder)

        wwmi_layout.addWidget(label_wwmi)
        wwmi_layout.addWidget(self.path_edit, 1)
        wwmi_layout.addWidget(btn_browse_wwmi)
        layout.addLayout(wwmi_layout)

        layout.addSpacing(10)

        # ----------------------------------------------------
        # XXMI Launcher Path 입력 필드
        # ----------------------------------------------------
        xxmi_layout = QHBoxLayout()
        xxmi_layout.setSpacing(8)

        label_xxmi = QLabel("XXMI Launcher (.exe):")
        self.xxmi_edit = QLineEdit(self)
        self.xxmi_edit.setText(xxmi_path)
        self.xxmi_edit.textChanged.connect(self.update_dialog_width)

        btn_browse_xxmi = QPushButton("Browse...")
        btn_browse_xxmi.clicked.connect(self.select_xxmi_exe)

        xxmi_layout.addWidget(label_xxmi)
        xxmi_layout.addWidget(self.xxmi_edit, 1)
        xxmi_layout.addWidget(btn_browse_xxmi)
        layout.addLayout(xxmi_layout)

        layout.addSpacing(16)

        # ----------------------------------------------------
        # OK / Cancel 버튼
        # ----------------------------------------------------
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

        # ----------------------------------------------------
        # 창 / 부모창 동시 드래그 이동 처리용
        # ----------------------------------------------------
        self._drag_pos = None

    # ==================== 드래그 이동 이벤트 ====================

    def mousePressEvent(self, e):
        # 클릭 위치 기록 + 부모 위치 기록
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos()
            self._parent_start_pos = self.parent().frameGeometry().topLeft()
            self._self_offset = self.frameGeometry().topLeft() - self._parent_start_pos

    def mouseMoveEvent(self, e):
        # 드래그 중일 때 부모와 자신을 동일하게 이동
        if self._drag_pos and e.buttons() & Qt.LeftButton:
            diff = e.globalPos() - self._drag_pos

            new_parent_pos = self._parent_start_pos + diff
            self.parent().move(new_parent_pos)

            new_self_pos = new_parent_pos + self._self_offset
            self.move(new_self_pos)

    # ==================== 길이에 따른 자동 width 증가 ====================

    def update_dialog_width(self):
        fm = QFontMetrics(self.path_edit.font())
        content_px = max(fm.horizontalAdvance(self.path_edit.text()), fm.horizontalAdvance(self.xxmi_edit.text()))
        label_px = max(self.fontMetrics().horizontalAdvance("WWMI Path:"), self.fontMetrics().horizontalAdvance("XXMI Launcher (.exe):"))
        button_px = 120
        required_width = label_px + content_px + button_px + 60

        if required_width > self.width():
            self.setMinimumWidth(required_width)
            self.resize(required_width, self.height())

    # ==================== 파일 탐색기 ====================

    def select_wwmi_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select WWMI Folder")
        if folder:
            self.path_edit.setText(folder)

    def select_xxmi_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select XXMI Launcher", filter="Executable Files (*.exe)")
        if file_path:
            self.xxmi_edit.setText(file_path)

    # ==================== 값 반환 ====================

    def get_data(self):
        return {
            "wwmi_path": self.path_edit.text().strip(),
            "xxmi_path": self.xxmi_edit.text().strip(),
        }

    # ==================== 표시 시 중앙 정렬 ====================

    def showEvent(self, event):
        super().showEvent(event)
        self.update_dialog_width()

        if self.parent():
            parent_rect = self.parent().frameGeometry()
            dialog_rect = self.frameGeometry()
            x = parent_rect.center().x() - dialog_rect.width() // 2
            y = parent_rect.center().y() - dialog_rect.height() // 2
            self.move(x, y)
