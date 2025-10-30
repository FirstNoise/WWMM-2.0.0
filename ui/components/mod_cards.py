# ui/components/mod_cards.py

from PyQt5.QtWidgets import (
    QGridLayout, QVBoxLayout, QStackedLayout,
    QSizePolicy, QLabel, QFrame, QWidget
)
from PyQt5.QtCore import Qt
import os

from utils.styled_widget import StyledWidget   # ✅ 변경
from .drop_overlay import DropOverlay

CARD_WIDTH = 280
H_GAP = 16
V_GAP = 20
OUTER_MARGIN = 24


class ModCardsContainer(StyledWidget):   # ✅ QWidget → StyledWidget
    object_name = "ModCardsContainer"    # ✅ 자동 setObjectName
    qss = "mod_cards.qss"                # ✅ 자동 QSS 적용

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumSize(400, 300)

        self._cards = []

        # ✅ 실제 카드 배치 영역
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(H_GAP)
        self.grid.setVerticalSpacing(V_GAP)
        self.grid.setContentsMargins(OUTER_MARGIN, OUTER_MARGIN, OUTER_MARGIN, OUTER_MARGIN)

        self.inner = QWidget()
        self.inner.setLayout(self.grid)

        # ✅ 오버레이 (위에 겹침)
        self.overlay = DropOverlay(self)
        self.overlay.hide()

        # ✅ 겹쳐 배치
        self.stack = QStackedLayout(self)
        self.stack.setStackingMode(QStackedLayout.StackAll)
        self.stack.addWidget(self.inner)
        self.stack.addWidget(self.overlay)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAcceptDrops(True)

    # ---- 카드 관리 ----
    def clear_cards(self):
        self._cards.clear()
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def add_card(self, card_widget):
        self._cards.append(card_widget)
        self._relayout()

    def _calc_columns(self) -> int:
        w = max(0, self.width() - OUTER_MARGIN * 2)
        return max(1, (w + H_GAP) // (CARD_WIDTH + H_GAP))

    def _relayout(self):
        while self.grid.count():
            self.grid.takeAt(0)

        cols = self._calc_columns()
        for idx, card in enumerate(self._cards):
            r = idx // cols
            c = idx % cols
            self.grid.addWidget(card, r, c, Qt.AlignTop)

        # ✅ 카드가 없으면 안내 카드 표시
        if not self._cards:
            self.grid.addWidget(EmptyModDropCard(self), 0, 0, Qt.AlignCenter)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.resize(self.size())
        self._relayout()

    # ---- 드래그 앤 드롭 ----
    def handle_drop(self, folder_path: str):
        parent = self.parent()
        while parent and not hasattr(parent, "_handle_mod_folder_dropped"):
            parent = parent.parent()
        if parent:
            parent._handle_mod_folder_dropped(folder_path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.overlay.show()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.overlay.hide()

    def dropEvent(self, event):
        self.overlay.hide()
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()

        # ✅ 이미지 → 무시 (ModCard 내부가 처리)
        if path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
            event.ignore()
            return

        # ✅ 폴더일 때만 처리
        if os.path.isdir(path):
            self.handle_drop(path)
            event.acceptProposedAction()
        else:
            event.ignore()


class EmptyModDropCard(StyledWidget):   # ✅ 변경
    object_name = "EmptyModDropCard"
    qss = "mod_cards.qss"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        msg = QLabel("모드가 없습니다.\n+ 버튼 또는 드래그 영역을 사용하세요.")
        msg.setAlignment(Qt.AlignCenter)
        layout.addStretch()
        layout.addWidget(msg)
        layout.addStretch()
