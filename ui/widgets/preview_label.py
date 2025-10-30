# ui/widgets/preview_label.py

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, pyqtSignal
import os

class PreviewLabel(QLabel):
    """
    ✅ 프리뷰 이미지 위젯 (완전 버전)
    - 클릭 시 → previewClicked(mod_folder_path)
    - 이미지 드래그&드랍 시 → previewDropped(mod_folder_path, image_file_path)
    - UI 전용: 파일 복사/교체는 MainWindow → Controller가 담당
    """

    # ▶ 클릭: 모드 폴더 경로 전달
    previewClicked = pyqtSignal(str)

    # ▶ 드롭: (모드 폴더 경로, 드롭된 이미지 경로) 전달
    previewDropped = pyqtSignal(str, str)

    # 허용하는 이미지 확장자
    ALLOWED_EXT = (".png", ".jpg", ".jpeg", ".bmp", ".gif")

    def __init__(self, mod_folder_path: str, parent=None):
        super().__init__(parent)
        self.mod_folder_path = mod_folder_path  # 이 Label이 어떤 모드 폴더에 연결되는지
        self.setAcceptDrops(True)               # ✅ 드래그 & 드롭 허용
        self.setAlignment(Qt.AlignCenter)       # 기본 정렬

    # --------------------------------------------------
    # ✅ 클릭 이벤트
    # --------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.mod_folder_path:
            self.previewClicked.emit(self.mod_folder_path)
        super().mousePressEvent(event)

    # --------------------------------------------------
    # ✅ 마우스 커서 변경 (UX 향상)
    # --------------------------------------------------
    def enterEvent(self, event):
        self.setCursor(Qt.PointingHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    # --------------------------------------------------
    # ✅ 드래그 → 이미지 파일이 들어왔는지 확인
    # --------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if self._is_image_file(url.toLocalFile()):
                    event.acceptProposedAction()
                    return
        event.ignore()

    # --------------------------------------------------
    # ✅ 드롭 시 → 이미지 경로 + mod_folder_path 전달
    # --------------------------------------------------
    def dropEvent(self, event):
        if not self.mod_folder_path:
            event.ignore()
            return

        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                image_path = url.toLocalFile()
                if self._is_image_file(image_path):
                    # (mod_folder_path, image_path) 전달
                    self.previewDropped.emit(self.mod_folder_path, image_path)
                    event.acceptProposedAction()
                    return
        event.ignore()

    # --------------------------------------------------
    # ✅ 내부 함수: 이미지 확장자 판별
    # --------------------------------------------------
    def _is_image_file(self, path: str) -> bool:
        return str(path).lower().endswith(self.ALLOWED_EXT)
