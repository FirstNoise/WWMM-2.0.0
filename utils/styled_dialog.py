from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt
from utils.qss_loader import apply_qss

class StyledDialog(QDialog):
    qss = None
    class_name = None

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

        if self.class_name:
            self.setProperty("class", self.class_name)

        # ✅ 다이얼로그도 배경 스타일 적용 가능하도록
        self.setAttribute(Qt.WA_StyledBackground, True)

        if self.qss:
            apply_qss(self, self.qss)

    def set_state(self, name, value):
        self.setProperty(name, value)
        self.style().unpolish(self)
        self.style().polish(self)
