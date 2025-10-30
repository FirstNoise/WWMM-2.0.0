# ui/views/mods_view.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt
from ui.widgets.preview_label import PreviewLabel


class ModsView(QWidget):
    """
    ✅ 역할 정리:
    - 현재 선택된 캐릭터의 '모드 리스트' + '프리뷰 이미지'를 보여주는 화면
    - 아래 2개의 Signal만 MainWindow로 전달 (UI는 직접 Controller 호출 ❌)

        ▷ modApplyRequested(str)     # 적용/해제 요청
        ▷ modDeleteRequested(str)    # 삭제 요청
        ▷ previewRequested(str, str) # (mod_name, folder_path) 프리뷰 클릭
        ▷ previewDropped(str, str)   # (mod_name, new_image_path) 프리뷰로 이미지 드롭됨

    - 프리뷰 교체는 2가지 방식 모두 지원:
        1) PreviewLabel 클릭 → 파일 선택창
        2) 이미지 파일 드래그 → PreviewLabel 위에 드롭
    """

    modApplyRequested = pyqtSignal(str)            # 모드 적용/해제
    modDeleteRequested = pyqtSignal(str)           # 모드 삭제
    previewRequested = pyqtSignal(str, str)        # (mod_name, folder_path)
    previewDropped = pyqtSignal(str, str)          # (mod_name, image_file_path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_character = None
        self.mods = []
        self.applied_mod = None
        self.preview_map = {}      # mod_name → mod_folder_path

        # 레이아웃
        self.layout = QVBoxLayout(self)
        self.title = QLabel("Mods")
        self.grid = QGridLayout()  # 모드 카드가 배치되는 레이아웃

        self.layout.addWidget(self.title)
        self.layout.addLayout(self.grid)

    # ------------------------------------------------------------------
    # ✅ UI 갱신
    # ------------------------------------------------------------------
    def refresh(self, character: str, mods: list, applied_mod: str, preview_map: dict):
        """
        MainWindow.apply_payload()에서 호출되는 갱신 함수.
        """
        self.current_character = character
        self.mods = mods
        self.applied_mod = applied_mod
        self.preview_map = preview_map or {}

        # 기존 위젯 제거
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 모드별 카드 UI 생성
        for row, mod_name in enumerate(self.mods):
            folder_path = self.preview_map.get(mod_name, "")

            # ① 모드 이름 라벨
            mod_label = QLabel(mod_name)
            self.grid.addWidget(mod_label, row, 0)

            # ② 프리뷰 이미지
            preview = PreviewLabel(folder_path)
            preview.setText("[이미지 없음]" if not folder_path else "")
            preview.setFixedSize(100, 100)
            preview.setStyleSheet("border: 1px solid gray;")
            preview.previewClicked.connect(lambda fp=folder_path, mn=mod_name: self.previewRequested.emit(mn, fp))
            # 드래그 & 드롭 허용
            preview.setAcceptDrops(True)
            preview.dragEnterEvent = self._make_drag_enter(preview)
            preview.dropEvent = self._make_drop_event(preview, mod_name)

            self.grid.addWidget(preview, row, 1)

            # ③ 적용 버튼
            btn_apply = QPushButton("적용" if mod_name != applied_mod else "해제")
            btn_apply.clicked.connect(lambda checked, mn=mod_name: self.modApplyRequested.emit(mn))
            self.grid.addWidget(btn_apply, row, 2)

            # ④ 삭제 버튼
            btn_delete = QPushButton("삭제")
            btn_delete.clicked.connect(lambda checked, mn=mod_name: self.modDeleteRequested.emit(mn))
            self.grid.addWidget(btn_delete, row, 3)

    # ------------------------------------------------------------------
    # ✅ 드래그 & 드롭 (프리뷰 이미지 교체)
    # ------------------------------------------------------------------
    def _make_drag_enter(self, widget):
        """
        PreviewLabel 영역에 '이미지 파일'이 들어오면 accept 처리
        """
        def dragEnterEvent(event):
            if event.mimeData().hasUrls():
                for url in event.mimeData().urls():
                    if str(url.toLocalFile()).lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
                        event.acceptProposedAction()
                        return
            event.ignore()
        return dragEnterEvent

    def _make_drop_event(self, widget, mod_name: str):
        """
        이미지 드롭 시 → previewDropped(mod_name, 이미지경로) signal 호출
        """
        def dropEvent(event):
            if event.mimeData().hasUrls():
                for url in event.mimeData().urls():
                    image_path = url.toLocalFile()
                    if image_path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
                        self.previewDropped.emit(mod_name, image_path)
                        event.acceptProposedAction()
                        return
            event.ignore()
        return dropEvent
