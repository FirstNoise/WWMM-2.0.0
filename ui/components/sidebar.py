# ui/components/sidebar.py

from PyQt5.QtWidgets import QVBoxLayout, QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import pyqtSignal, QSize
from PyQt5.QtGui import QIcon

from utils.styled_widget import StyledWidget  # ✅ 변경

class SideBar(StyledWidget):  # ✅ QWidget → StyledWidget
    object_name = "SideBar"   # ✅ 자동 setObjectName
    qss = "sidebar.qss"       # ✅ 자동 apply_qss

    characterSelected = pyqtSignal(str)   # ✅ 추가

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIconSize(QSize(38, 38))
        layout.addWidget(self.tree)

        self.tree.itemClicked.connect(self._on_item_clicked)   # ✅ 연결

    def _on_item_clicked(self, item, column):
        # ✅ 카테고리는 클릭해도 동작하지 않도록 처리
        if item.parent() is None and item.childCount() > 0:
            item.setExpanded(not item.isExpanded())
            return
        
        char_name = item.text(0)
        self.characterSelected.emit(char_name)   # ✅ 외부에 신호만 보냄

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

        
