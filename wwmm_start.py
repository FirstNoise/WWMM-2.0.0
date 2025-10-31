# wwmm_start.py
import sys, os, ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor, QFontDatabase, QFont, QIcon
from PyQt5.QtCore import Qt

from wwmm_logic_bridge import WWMMLogic
from controller.main_controller import MainController
from ui.views.main_window import MainWindow


APP_TITLE = "WWMM - Wuthering Waves Mod Manager 2.0.0"


# ✅ PyInstaller 환경/개발 환경 모두 대응하는 리소스 경로 반환
def resource_path(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base, rel)


def main():
    # ✅ Windows 작업 표시줄 AppUserModelID 지정 (아이콘/제목 정상 표시 위함)
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("wwmm.modmanager")
    except Exception:
        pass

    # ✅ 앱 실행 경로 기반으로 "mods" 폴더를 무조건 이 위치로 고정
    #    → 이 디렉터리가 WWMM 전역 mod 저장소의 유일한 Root가 됨
    exe_dir = os.path.abspath(os.path.dirname(__file__))
    wwmm_mods_path = os.path.join(exe_dir, "mods")
    os.makedirs(wwmm_mods_path, exist_ok=True)

    # ✅ settings.json 파일 위치도 여기서만 정의
    #    (PyInstaller 환경에서는 /resources/config/settings.json 내부로부터)
    settings_file = resource_path("resources/config/settings.json")

    # ✅ High DPI 옵션 적용 (PyQt5는 QApplication 생성 전에 필요)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # ✅ QApplication 실행
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)

    # ✅ Logic 생성 (경로는 UI/Controller가 아닌 여기서만 주입)
    logic = WWMMLogic(wwmm_mods_path, settings_file)
    controller = MainController(logic)
    win = MainWindow(controller)

    win.setWindowFlag(Qt.FramelessWindowHint)           # ✅ 타이틀바 제거
    win.setAttribute(Qt.WA_TranslucentBackground, True) # ✅ 배경을 투명하게 만들기

    from utils.blur_helper import apply_acrylic_blur
    apply_acrylic_blur(win.winId())                     # ✅ 블러 효과 적용

    # ✅ Fallback 처리 (Windows 10 이하)
    import platform
    try:
        build_number = int(platform.version().split('.')[2])
        #build_number = 19045   # Windows 10 값 (임시)
    except:
        build_number = 0  # 안전 대비

    if build_number < 22000:  # Windows 10 이하
        win.setStyleSheet(win.styleSheet() + """
        #TopBar,
        #SideBar,
        #CentralBackground {
            background: rgba(25,25,30,0.92); /* Windows 10용 불투명 다크 */
            backdrop-filter: none;
        }
        """)

    # ✅ 싱글 인스턴스 (중복 실행 차단)
    logic.install_instance_lock_atexit()
    if logic.is_another_instance_running():
        ctypes.windll.user32.MessageBoxW(None, "이미 실행 중입니다.", APP_TITLE, 0x40)
        sys.exit(0)
    logic.write_instance_lock()


    # ✅ 앱 아이콘
    icon_path = resource_path("resources/Wuthering_Waves/wwmm_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # ✅ 폰트 (선택사항)
    font_path = resource_path("resources/font/AstaSans-Regular.ttf")
    fid = QFontDatabase.addApplicationFont(font_path)
    if fid != -1:
        family = QFontDatabase.applicationFontFamilies(fid)[0]
        app.setFont(QFont(family, 13))

    # ✅ 메인 윈도우 실행
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
