# utils/qss_loader.py
import os

def apply_qss(widget, filename):
    """
    widget: QSS를 적용할 QWidget
    filename: styles/ 안에 있는 qss 파일 이름 (예: "mod_card.qss")
    """
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    qss_path = os.path.join(base, "styles", filename)

    if not os.path.exists(qss_path):
        print(f"[QSS] 파일을 찾을 수 없음: {qss_path}")
        return

    with open(qss_path, "r", encoding="utf-8") as f:
        qss = f.read()
        widget.setStyleSheet(widget.styleSheet() + "\n" + qss)
