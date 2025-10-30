# ui/components/mod_card.py

from PyQt5.QtWidgets import (
    QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtCore import QSize

from utils.styled_widget import StyledWidget   # ✅ 변경
from ui.widgets.preview_label import PreviewLabel


class ModCard(StyledWidget):   # ✅ QFrame → StyledWidget
    """
    ✅ 단일 모드 카드 (UI 전용)
    - MainWindow/Controller 직접 접근 금지
    - 모든 동작은 Signal로만 외부에 전달
    """

    class_name = "ModCard"     # ✅ QSS `.ModCard` 매칭용
    qss = "mod_card.qss"       # ✅ 자동 스타일 적용

    # 📌 MainWindow에서 연결해서 사용하게 될 시그널
    applyRequested = pyqtSignal(str)
    deleteRequested = pyqtSignal(str)
    previewRequested = pyqtSignal(str)

    def __init__(self, mod_name: str, mod_folder_path: str,
                 preview_path: str = None, applied: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedSize(400, 270)
        self.mod_name = mod_name
        self.mod_folder_path = mod_folder_path
        self.preview_path = preview_path
        self.applied = applied

        self._init_ui()
        self.set_state("applied", "true" if self.applied else "false")  # ✅ 상태 반영

    # ---------------------------------------
    # ✅ UI 구성만 담당
    # ---------------------------------------
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        # 1) 모드 이름
        lbl_name = QLabel(self.mod_name)
        lbl_name.setObjectName("ModName")
        lbl_name.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_name)

        # 2) 프리뷰 이미지
        self.preview_label = PreviewLabel(self.mod_folder_path)
        self.preview_label.setObjectName("PreviewImage")
        self.preview_label.setAlignment(Qt.AlignCenter)
        

        if self.preview_path:
            pixmap = QPixmap(self.preview_path).scaled(
                QSize(361, 180), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(pixmap)
        else:
            self.preview_label.setFixedSize(361, 180)  # ✅ 박스 크기 고정
            self.preview_label.setText("미리보기 없음")
            self.preview_label.setAlignment(Qt.AlignCenter)  # ✅ 중앙 정렬 추천

        layout.addWidget(self.preview_label)

        self.preview_label.previewClicked.connect(self._emit_preview_request)

        # ✅ 여기 추가 → 이미지와 버튼 사이에 여유 공간 넣기
        layout.addStretch(1)

        # 3) 버튼 영역
        self.btn_apply = QPushButton()
        self.btn_apply.setObjectName("ApplyButton")

        self.btn_delete = QPushButton("삭제")
        self.btn_delete.setObjectName("DeleteButton")

        self._update_button_text()

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_apply)
        btn_layout.addWidget(self.btn_delete)

        # ✅ 버튼은 항상 맨 아래 배치
        layout.addLayout(btn_layout)

        self.btn_apply.clicked.connect(self._emit_apply_request)
        self.btn_delete.clicked.connect(self._emit_delete_request)

        self.setCursor(QCursor(Qt.ArrowCursor))


    # ---------------------------------------
    # ✅ 신호 Emit 함수
    # ---------------------------------------
    def _emit_apply_request(self):
        self.applyRequested.emit(self.mod_name)

    def _emit_delete_request(self):
        self.deleteRequested.emit(self.mod_name)

    def _emit_preview_request(self):
        self.previewRequested.emit(self.mod_folder_path)

    # ---------------------------------------
    # ✅ 상태 변경 시 버튼/스타일 갱신
    # ---------------------------------------
    def set_applied(self, applied: bool):
        self.applied = applied
        self._update_button_text()
        self.set_state("applied", "true" if applied else "false")  # ✅ StyledWidget 방식 적용

    def _update_button_text(self):
        self.btn_apply.setText("적용 해제" if self.applied else "적용하기")
