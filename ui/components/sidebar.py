# ui/components/sidebar.py

from PyQt5.QtWidgets import QVBoxLayout, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import pyqtSignal, QSize
from PyQt5.QtGui import QIcon

from utils.styled_widget import StyledWidget  # ✅ 변경

class SideBar(StyledWidget):  # ✅ QWidget → StyledWidget
    object_name = "SideBar"   # ✅ 자동 setObjectName
    qss = "sidebar.qss"       # ✅ 자동 apply_qss

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIconSize(QSize(38, 38))
        layout.addWidget(self.tree)

    def set_character_data(self, categories, category_icons, char_icons):
        self.tree.clear()

        for category, characters in categories.items():
            parent = QTreeWidgetItem(self.tree)
            parent.setText(0, category)

            if category in category_icons:
                parent.setIcon(0, QIcon(category_icons[category]))

            for char in characters:
                child = QTreeWidgetItem(parent)
                child.setText(0, char)

                if char in char_icons:
                    child.setIcon(0, QIcon(char_icons[char]))

        self.tree.expandAll()
