# ui/components/drop_overlay.py
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
import os

from utils.qss_loader import apply_qss

class DropOverlay(QFrame):
    """
    ✅ 모드 드래그 시 나타나는 오버레이 레이어
    - 평소에는 숨겨짐
    - dragEnter/drop 중에만 표시
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        apply_qss(self, "drop_overlay.qss") # qss 적용
        self.setAcceptDrops(True)
        self.hide()

        layout = QVBoxLayout(self)
        label = QLabel("여기에 모드 폴더를 드롭하세요")
        label.setAlignment(Qt.AlignCenter)
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()

    # ---------------------------------------------
    # Drag & Drop
    # ---------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.show()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.hide()

    def dropEvent(self, event):
      self.hide()
      urls = event.mimeData().urls()
      if not urls:
          return

      path = urls[0].toLocalFile()

      # ✅ 1) 이미지 파일일 경우 → 무시 (개별 프리뷰 라벨이 처리해야 함)
      if path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
          event.ignore()
          return

      # ✅ 2) 폴더인 경우만 카드 컨테이너로 전달
      if os.path.isdir(path):

          # 상위 트리를 따라 올라가면서 ModCardsContainer 찾기
          parent = self.parent()
          while parent and not hasattr(parent, "handle_drop"):
              parent = parent.parent()

          if parent and hasattr(parent, "handle_drop"):
              parent.handle_drop(path)
              event.acceptProposedAction()
          else:
              print("[경고] DropOverlay: handle_drop 을 처리할 컨테이너를 찾지 못했습니다.")
      else:
          event.ignore()

