# utils/styled_widget.py
from PyQt5.QtWidgets import QFrame
from utils.qss_loader import apply_qss
from PyQt5.QtCore import Qt

class StyledWidget(QFrame):   # ✅ QWidget → QFrame
    qss = None
    object_name = None
    class_name = None

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

        if self.object_name:
            self.setObjectName(self.object_name)

        if self.class_name:
            self.setProperty("class", self.class_name)

        # ✅ 배경 칠할 수 있게 필수
        self.setAttribute(Qt.WA_StyledBackground, True)

        if self.qss:
            apply_qss(self, self.qss)

    def set_state(self, name, value):
        self.setProperty(name, value)
        self.style().unpolish(self)
        self.style().polish(self)
