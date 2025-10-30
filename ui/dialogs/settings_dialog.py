# ui/dialogs/settings_dialog.py
import os
from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QSizePolicy
)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFontMetrics
from utils.styled_dialog import StyledDialog   # ✅

class SettingsDialog(StyledDialog):
    class_name = "SettingsDialog"
    qss = "settings_dialog.qss"

    def __init__(self, parent=None, wwmi_path="", xxmi_path=""):
        super().__init__(parent)

        # ✅ 프레임 제거 + 화면 정중앙 표시
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)

        self.setMinimumWidth(720)
        self.setSizeGripEnabled(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)

        # ---------------- 상단 닫기 버튼 ----------------
        header = QHBoxLayout()
        header.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setObjectName("CloseButton")
        btn_close.clicked.connect(self.close)
        header.addWidget(btn_close)

        layout.addLayout(header)

        # ---------------- WWMI Path ----------------
        self.path_edit = QLineEdit(self)
        self.path_edit.setText(wwmi_path)
        self.path_edit.textChanged.connect(self.update_dialog_width)

        btn_browse_wwmi = QPushButton("Browse...")
        btn_browse_wwmi.clicked.connect(self.select_wwmi_folder)

        wwmi_layout = QHBoxLayout()
        wwmi_layout.addWidget(QLabel("WWMI Path:"))
        wwmi_layout.addWidget(self.path_edit, 1)
        wwmi_layout.addWidget(btn_browse_wwmi)

        # ---------------- XXMI Path ----------------
        self.xxmi_edit = QLineEdit(self)
        self.xxmi_edit.setText(xxmi_path)
        self.xxmi_edit.textChanged.connect(self.update_dialog_width)

        btn_browse_xxmi = QPushButton("Browse...")
        btn_browse_xxmi.clicked.connect(self.select_xxmi_exe)

        xxmi_layout = QHBoxLayout()
        xxmi_layout.addWidget(QLabel("XXMI Launcher (.exe):"))
        xxmi_layout.addWidget(self.xxmi_edit, 1)
        xxmi_layout.addWidget(btn_browse_xxmi)

        # ---------------- OK / Cancel ----------------
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancel")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(wwmi_layout)
        layout.addLayout(xxmi_layout)
        layout.addLayout(btn_layout)

        # ✅ 드래그 가능하도록 상태 저장
        self._drag_pos = None

    # ------------- 창 드래그 이동 -------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() & Qt.LeftButton:
            self.move(e.globalPos() - self._drag_pos)

    # ------------- 텍스트 길이에 따른 자동 크기조절 -------------
    def update_dialog_width(self):
        fm = QFontMetrics(self.path_edit.font())
        content_px = max(fm.horizontalAdvance(self.path_edit.text()), fm.horizontalAdvance(self.xxmi_edit.text()))
        label_px = max(self.fontMetrics().horizontalAdvance("WWMI Path:"), self.fontMetrics().horizontalAdvance("XXMI Launcher (.exe):"))
        button_px = 120
        required_width = label_px + content_px + button_px + 60

        if required_width > self.width():
            self.setMinimumWidth(required_width)
            self.resize(required_width, self.height())

    def select_wwmi_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select WWMI Folder")
        if folder:
            self.path_edit.setText(folder)

    def select_xxmi_exe(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select XXMI Launcher", filter="Executable Files (*.exe)")
        if file_path:
            self.xxmi_edit.setText(file_path)

    def get_data(self):
        return {
            "wwmi_path": self.path_edit.text().strip(),
            "xxmi_path": self.xxmi_edit.text().strip(),
        }

    def showEvent(self, event):
        super().showEvent(event)
        self.update_dialog_width()
