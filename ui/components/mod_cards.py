# ui/components/mod_cards.py

import os

from PyQt5.QtWidgets import (
    QGridLayout, QVBoxLayout, QStackedLayout,
    QSizePolicy, QLabel, QWidget, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from .no_character_card import NoCharacterSelectedCard
from .drop_overlay import DropOverlay

from utils.styled_widget import StyledWidget


HORIZONTAL_SPACING = 16
VERTICAL_SPACING = 20
OUTER_MARGIN = 24


class ModCardsContainer(StyledWidget):
    modFolderDropped = pyqtSignal(str)
    current_character = None  # ✅ 상태 저장 필드 추가
    object_name = "ModCardsContainer"
    qss = "mod_cards.qss"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setMinimumSize(400, 300)

        self.cards = []
        self.reposition_pending_flag = False

        # 내부 카드 레이아웃
        self.grid_layout = QGridLayout()
        self.grid_layout.setHorizontalSpacing(HORIZONTAL_SPACING)
        self.grid_layout.setVerticalSpacing(VERTICAL_SPACING)
        self.grid_layout.setContentsMargins(OUTER_MARGIN, OUTER_MARGIN, OUTER_MARGIN, OUTER_MARGIN)

        self.inner_widget = QWidget()
        self.inner_widget.setLayout(self.grid_layout)

        # ✅ inner_widget 을 감싸는 스크롤
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self.inner_widget)

        # ✅ 흰 배경 제거 핵심
        self.scroll.viewport().setAttribute(Qt.WA_StyledBackground, False)
        self.scroll.viewport().setStyleSheet("background: transparent;")

        # 오버레이 (겹쳐보이게)
        self.overlay_widget = DropOverlay(self)
        self.overlay_widget.hide()

        # ✅ 레이아웃 소유권 문제 해결 (self 에 직접 전달 금지)
        self.stacked_layout = QStackedLayout()
        self.stacked_layout.setStackingMode(QStackedLayout.StackAll)
        self.stacked_layout.addWidget(self.scroll)          # 스크롤이 아래
        self.stacked_layout.addWidget(self.overlay_widget)  # 오버레이는 위

        self.setLayout(self.stacked_layout)  # ✅ 여기서 attach

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAcceptDrops(True)

    def set_character(self, character_name):
        self.current_character = character_name
        self.request_reposition_layout()  # ✅ 화면 다시 배치

    # ==============================
    # 상태에 따른 빈 화면 분기 로직
    # ==============================

    def reposition_cards_in_layout(self):
        self.reposition_pending_flag = False

        # 기존 카드 제거
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        # ✅ 상태 1: 캐릭터 미선택
        if self.current_character is None:
            placeholder = NoCharacterSelectedCard(self.inner_widget)
            self.grid_layout.addWidget(placeholder, 0, 0, Qt.AlignCenter)
            return

        # ✅ 상태 2: 캐릭터 선택 + 모드 없음
        if not self.cards:
            placeholder = EmptyModDropCard(self.inner_widget)
            self.grid_layout.addWidget(placeholder, 0, 0, Qt.AlignCenter)
            return

        # ✅ 상태 3: 캐릭터 선택 + 모드 있음 → 기존 로직 유지
        column_count = self.calculate_column_count()
        for index, card_widget in enumerate(self.cards):
            row = index // column_count
            col = index % column_count
            self.grid_layout.addWidget(card_widget, row, col, Qt.AlignTop)


    # ==============================
    # 카드 관리
    # ==============================
    def clear_cards(self):
        self.cards.clear()

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.request_reposition_layout()

    def add_card(self, card_widget):
        card_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.cards.append(card_widget)
        self.request_reposition_layout()

    # ==============================
    # 재배치 예약
    # ==============================
    def request_reposition_layout(self):
        if self.reposition_pending_flag:
            return
        self.reposition_pending_flag = True
        QTimer.singleShot(0, self.reposition_cards_in_layout)

    # ==============================
    # 열 수 계산
    # ==============================
    def calculate_column_count(self) -> int:
        if not self.cards:
            return 1

        # ✅ 스크롤 영역(viewport)의 실제 표시 가능한 너비 사용
        available_width = self.scroll.viewport().width() - (OUTER_MARGIN * 2)

        if available_width <= 0:
            return 1

        card_width = 400
        spacing = HORIZONTAL_SPACING

        columns = (available_width + spacing) // (card_width + spacing)
        columns = max(1, int(columns))

        while columns > 1:
            required_width = (columns * card_width) + ((columns - 1) * spacing)
            if required_width <= available_width:
                break
            columns -= 1

        return columns

    # ==============================
    # 재배치 실제 수행
    # ==============================
    # def reposition_cards_in_layout(self):
    #     self.reposition_pending_flag = False

    #     while self.grid_layout.count():
    #         item = self.grid_layout.takeAt(0)
    #         widget = item.widget()
    #         if widget:
    #             widget.setParent(None)

    #     column_count = self.calculate_column_count()

    #     for index, card_widget in enumerate(self.cards):
    #         row = index // column_count
    #         col = index % column_count
    #         self.grid_layout.addWidget(card_widget, row, col, Qt.AlignTop)

    #     if not self.cards:
    #         placeholder = EmptyModDropCard(self.inner_widget)
    #         self.grid_layout.addWidget(placeholder, 0, 0, Qt.AlignCenter)

    # ==============================
    # 리사이즈
    # ==============================
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay_widget.resize(self.size())
        self.request_reposition_layout()

    # ==============================
    # Drag & Drop Entry Point
    # ==============================
    def dragEnterEvent(self, event):
        # ✅ 캐릭터 없을 때 드롭 관련 UI/이벤트 전부 무시
        if self.current_character is None:
            event.ignore()
            return

        if event.mimeData().hasUrls():
            self.overlay_widget.show()
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        # ✅ 캐릭터 없을 때 완전 무시
        if self.current_character is None:
            event.ignore()
            return
        
        event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.overlay_widget.hide()
        event.accept()

    def dropEvent(self, event):
        self.overlay_widget.hide()

        # ✅ 캐릭터 없을 때 드랍 완전 차단
        if self.current_character is None:
            event.ignore()
            return

        urls = event.mimeData().urls()
        if not urls:
            return

        path = urls[0].toLocalFile()

        # 이미지 파일이면 DropOverlay 에서 처리해야 하므로 여기서는 무시
        if path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
            return

        if os.path.isdir(path):
            self.modFolderDropped.emit(path)

class EmptyModDropCard(StyledWidget):
    object_name = "EmptyModDropCard"
    qss = "mod_cards.qss"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout(self)
        label = QLabel("모드가 없습니다.\n+ 버튼 혹은 폴더를 드래그 해주세요.")
        label.setAlignment(Qt.AlignCenter)
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()

