# ui/components/no_character_card.py

from PyQt5.QtWidgets import QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from utils.styled_widget import StyledWidget

class NoCharacterSelectedCard(StyledWidget):
    object_name = "NoCharacterSelectedCard"
    qss = "mod_cards.qss"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        label = QLabel("캐릭터를 선택해주세요.")
        label.setAlignment(Qt.AlignCenter)
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()
