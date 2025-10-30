import sys
import ctypes
import os
import shutil
import subprocess
import psutil

LOCK_FILE = os.path.join(os.path.expanduser("~"), ".wwmm.lock")

def is_another_instance_running():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, "r") as f:
                old_pid = int(f.read())
            if psutil.pid_exists(old_pid):
                print(f"이미 실행중: pid={old_pid}")
                return True
            else:
                print("이전 인스턴스는 죽어있음. lock 파일 삭제")
                os.remove(LOCK_FILE)
                return False
        except Exception as e:
            print(f"lock 파일 읽기 오류: {e}")
            return True
    return False

def write_lock():
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        print(f"lock 파일 생성: {LOCK_FILE} pid={os.getpid()}")
    except Exception as e:
        print(f"lock 파일 생성 실패: {e}")

def create_lock():
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

def remove_lock():
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
        except Exception:
            pass
if __name__ == "__main__":
    if is_another_instance_running():
        from PyQt5.QtWidgets import QApplication, QMessageBox
        app = QApplication(sys.argv)
        QMessageBox.warning(None, "WWMM", "이미 실행 중입니다.")
        sys.exit(0)
write_lock()
import atexit
atexit.register(remove_lock)

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QScrollArea, QFrame, QGridLayout,
    QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtGui import QPixmap, QPalette, QColor, QIcon, QFont, QBrush
from PyQt5.QtCore import Qt, QSize, QEvent
from wwmm_mod_utils import add_mod_folder, delete_mod, get_preview_image_path
from wwmm_symlink import create_symlink_windows_compatible
from wwmm_settings import load_settings, save_settings
from wwmm_mod_utils import is_admin, run_as_admin
print(run_as_admin.__module__, run_as_admin.__name__)

class ModCardsContainer(QWidget):
    def __init__(self, parent, wwmm_window):
        super().__init__(parent)
        self.wwmm_window = wwmm_window
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        # 폴더만 허용
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                local_path = url.toLocalFile()
                if os.path.isdir(local_path):  # 폴더만 허용
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        # 현재 선택 캐릭터 없으면 무시
        if not self.wwmm_window.current_character:
            self.show_topmost_message("오류", "먼저 캐릭터를 선택하세요!")
            return
        # 여러 폴더 드롭도 지원
        for url in event.mimeData().urls():
            folder_path = url.toLocalFile()
            if os.path.isdir(folder_path):
                add_mod_folder(
                    self.wwmm_window.current_character,
                    folder_path,
                    self.wwmm_window.wwmm_mods_path,
                    self.wwmm_window.on_character_selected,
                    self.wwmm_window.find_character_item,
                    self.wwmm_window
                )

class EmptyModDropCard(QFrame):
    def __init__(self, wwmm_window):
        super().__init__()
        self.wwmm_window = wwmm_window
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                background-color: #2c2c2c;
                border: 1px solid #444;
                border-radius: 10px;
                padding: 10px;
                color: #aaa;
            }
        """)
        layout = QVBoxLayout()
        msg = QLabel("아직 추가된 모드가 없습니다.\n폴더를 드래그하거나\n위의 +모드 추가 버튼을 눌러주세요!")
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet("font-size: 18px; color: #aaa;")
        layout.addStretch()
        layout.addWidget(msg)
        layout.addStretch()
        self.setLayout(layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                local_path = url.toLocalFile()
                if os.path.isdir(local_path):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        # 캐릭터 선택되어 있을 때만 동작
        if not self.wwmm_window.current_character:
            self.wwmm_window.show_topmost_message("오류", "먼저 캐릭터를 선택하세요!")
            return
        for url in event.mimeData().urls():
            folder_path = url.toLocalFile()
            if os.path.isdir(folder_path):
                add_mod_folder(
                    self.wwmm_window.current_character,
                    folder_path,
                    self.wwmm_window.wwmm_mods_path,
                    self.wwmm_window.on_character_selected,
                    self.wwmm_window.find_character_item,
                    self.wwmm_window
                )

class PreviewLabel(QLabel):
    def __init__(self, mod_folder_path, wwmm_window, parent=None):
        super().__init__(parent)
        self.mod_folder_path = mod_folder_path
        self.wwmm_window = wwmm_window  # <-- 명확하게!
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self.wwmm_window.handle_preview_image_replace(self.mod_folder_path, file_path)
                break

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.wwmm_window.open_preview_file_dialog(self.mod_folder_path)
    
    def enterEvent(self, event):
        self.setCursor(Qt.PointingHandCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)


class WWMM(QWidget):

    def show_topmost_message(self, title, message, icon=QMessageBox.Information):
        msgbox = QMessageBox(self)
        msgbox.setIcon(icon)
        msgbox.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        msgbox.setWindowTitle(title)
        msgbox.setText(message)
        msgbox.exec_()
    def show_topmost_question(self, title, message):
        msgbox = QMessageBox(self)
        msgbox.setIcon(QMessageBox.Question)
        msgbox.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        msgbox.setWindowTitle(title)
        msgbox.setText(message)
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setDefaultButton(QMessageBox.No)
        reply = msgbox.exec_()
        return reply

    def toggle_maximize_restore(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

    def __init__(self):
        super().__init__()
        # [핵심] 아이콘 경로 계산: 빌드환경과 개발환경 모두 대응
        if getattr(sys, 'frozen', False):
            # 배포(EXE) 환경
            base_dir = os.path.dirname(sys.executable)
        else:
            # 개발(스크립트) 환경
            base_dir = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(base_dir, "wwmm_icon.ico")
        self.setWindowTitle("WWMM - Wuthering Waves Mod Manager.1.03")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon(icon_path))  # ← 이렇게 변경!
        self.resize(1200, 700)

        self.wwmm_mods_path = os.path.join(base_dir, "Mods")
        self.wwmi_mods_path = None
        self.settings_file = os.path.join(base_dir, "settings.json")

        self.current_character = None
        self.character_order = []

        self.init_ui()
        self.load_settings()
        self.load_characters()
        self.old_pos = None
        self.show_empty_card()
    
    
    def show_empty_card(self):
        """캐릭터 미선택시 안내 카드 표시"""
        self.clear_mod_cards()  # 기존 카드 영역 비우기

        card = QFrame()
        card_layout = QVBoxLayout()
        card.setLayout(card_layout)
        card.setFrameShape(QFrame.Box)
        card.setLineWidth(1)
        card.setStyleSheet("""
            QFrame {
                background-color: #2c2c2c;
                border: 1px solid #333;
                border-radius: 10px;
                padding: 10px;
                color: #aaa;
            }
        """)

        msg = QLabel("캐릭터를 선택해 주세요")
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet("font-size: 20px; color: #aaa;")
        card_layout.addStretch()
        card_layout.addWidget(msg)
        card_layout.addStretch()

        # 한가운데만
        self.mod_cards_layout.addWidget(card, 0, 0, 1, 2)

        # +모드추가 버튼 숨기기
        self.add_mod_button.setVisible(False)

    def init_ui(self):
        self.setAutoFillBackground(True)
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        self.setPalette(palette)

        main_layout = QVBoxLayout()
        title_bar = QHBoxLayout()
        title_bar_widget = QWidget()
        title_bar_widget.setFixedHeight(53)
        title_bar_widget.setLayout(title_bar)
        title_bar_widget.setStyleSheet("background-color: #2e2e2e;")
        self.title_bar_widget = title_bar_widget
        self.title_bar_widget.mousePressEvent = self.title_bar_mousePressEvent
        self.title_bar_widget.mouseMoveEvent = self.title_bar_mouseMoveEvent

        title = QLabel("WWMM - Wuthering Waves Mod Manager.1.03")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 20px; padding-left: 8px;")
        title.setContentsMargins(0, -2, 0, 0)
        title.setFixedHeight(36)
        title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.minimize_button = QPushButton("―")
        self.minimize_button.setFixedSize(36, 36)
        self.minimize_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                font-size: 20px;
                border: none;
                padding: -1px;
            }
            QPushButton:pressed {
                background-color: #2A292D
            }
        """)
        self.minimize_button.clicked.connect(self.showMinimized)

        self.maximize_button = QPushButton("□")
        self.maximize_button.setFixedSize(36, 36)
        self.maximize_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                font-size: 20px;
                border: none;
                padding: -1px;
            }
            QPushButton:pressed {
                background-color: #2A292D
            }
        """)
        self.maximize_button.clicked.connect(self.toggle_maximize_restore)

        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(36, 36)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                font-size: 20px;
                border: none;
                padding: -1px;
            }
            QPushButton:pressed {
                background-color: #2A292D
            }
        """)
        self.close_button.clicked.connect(self.close)

        self.minimize_button.installEventFilter(self)
        self.maximize_button.installEventFilter(self)
        self.close_button.installEventFilter(self)

        title_bar.addWidget(title, alignment=Qt.AlignVCenter)
        title_bar.addStretch()
        title_bar.addWidget(self.minimize_button, alignment=Qt.AlignVCenter)
        title_bar.addWidget(self.maximize_button, alignment=Qt.AlignVCenter)
        title_bar.addWidget(self.close_button, alignment=Qt.AlignVCenter)


        top_bar = QHBoxLayout()
        content_layout = QHBoxLayout()

        self.path_label = QLabel("WWMI Path: (미설정)")
        self.path_label.setStyleSheet("color: white;")
        self.set_path_button = QPushButton("WWMI Route Setting")
        self.set_path_button.setCursor(Qt.PointingHandCursor)
        self.set_path_button.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #666;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #5c5c5c;
            }
            QPushButton:pressed {
                background-color: #2c2c2c;
            }
        """)

        top_bar.addWidget(self.path_label)
        top_bar.addWidget(self.set_path_button)
        self.set_path_button.clicked.connect(self.set_wwmi_path)

        self.character_list = QTreeWidget()
        self.character_list.setHeaderHidden(True)
        self.character_list.setIconSize(QSize(45, 45))
        self.character_list.setStyleSheet("""
            QTreeWidget {
                background-color: #2e2e2e;
                color: white;
                border: none;
            }
            QTreeWidget::item:selected {
                background-color: #444;
                color: white;
            }
        """)
        self.character_list.itemClicked.connect(self.on_character_selected)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.mod_cards_container = ModCardsContainer(self, self)
        self.mod_cards_layout = QGridLayout()
        self.mod_cards_vbox = QVBoxLayout()
        self.add_mod_button = QPushButton("＋ 모드 추가")
        self.add_mod_button.setCursor(Qt.PointingHandCursor) 
        self.add_mod_button.setFixedHeight(34)
        self.add_mod_button.setStyleSheet("""
            QPushButton {
                background-color: #33333c;
                color: #fff;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                margin-bottom: 8px;
            }
            QPushButton:hover {
                background-color: #47535f;
            }
        """)
        self.add_mod_button.clicked.connect(lambda: add_mod_folder(
        self.current_character,  # 캐릭터 이름
        QFileDialog.getExistingDirectory(self, "추가할 모드 폴더를 선택하세요."),  # 폴더 선택
        self.wwmm_mods_path,  # Mods 경로
        self.on_character_selected,  # 캐릭터 선택 후 새로고침 콜백
        self.find_character_item,    # 캐릭터 아이템 찾기 콜백
        self  # parent_widget (메시지박스용)
        ))
        self.mod_cards_vbox.addWidget(self.add_mod_button)
        self.mod_cards_vbox.addLayout(self.mod_cards_layout)
        self.mod_cards_container.setLayout(self.mod_cards_vbox)
        self.scroll_area.setWidget(self.mod_cards_container)
        self.scroll_area.setStyleSheet("background-color: #1e1e1e;")

        content_layout.addWidget(self.character_list, 2)
        content_layout.addWidget(self.scroll_area, 5)

        main_layout.addWidget(title_bar_widget)
        main_layout.addLayout(top_bar)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        self.launch_xxmi_button = QPushButton("Run XXMI Launcher")
        self.launch_xxmi_button.setCursor(Qt.PointingHandCursor)
        self.launch_xxmi_button.setStyleSheet("""
            QPushButton {
                background-color: #4a69bd;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e3799;
            }
        """)
        self.launch_xxmi_button.clicked.connect(self.launch_xxmi_launcher)
        top_bar.addWidget(self.launch_xxmi_button)
    
    def eventFilter(self, obj, event):
        # 버튼 위에서만 드래그 시그널이 타지 않게 하고, 이벤트 자체는 Qt로 보내자!
        if obj in [self.minimize_button, self.maximize_button, self.close_button]:
            # 버튼 위에서는 타이틀바 드래그 관련 변수 초기화만 해준다.
            if event.type() == QEvent.MouseButtonPress:
                self.old_pos = None  # 타이틀바 드래그 변수 리셋
            # 이벤트는 그냥 Qt로 보내자
            return False  # 절대 True를 반환하지 말 것!
        return super().eventFilter(obj, event)

    def title_bar_mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            child = self.title_bar_widget.childAt(event.pos())
            if isinstance(child, QPushButton):
                self.old_pos = None
            else:
                self.old_pos = event.globalPos()

    def title_bar_mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.old_pos is not None:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def title_bar_mouseReleaseEvent(self, event):
        self.old_pos = None

    def launch_xxmi_launcher(self):
        if not hasattr(self, "xxmi_launcher_path") or not self.xxmi_launcher_path or not os.path.exists(self.xxmi_launcher_path):
            self.show_topmost_message("경로 오류", "XXMI Launcher 실행 파일 경로를 먼저 설정해주세요.")
            self.set_xxmi_launcher_path()
            if hasattr(self, "xxmi_launcher_path") and self.xxmi_launcher_path and os.path.exists(self.xxmi_launcher_path):
                try:
                    run_as_admin(self.xxmi_launcher_path, [])  # 여기서 관리자 권한 실행!
                except Exception as e:
                    self.show_topmost_message("실행 실패", f"XXMI Launcher 실행 중 오류:\n{e}")
            return
        try:
            run_as_admin(self.xxmi_launcher_path, [])  # 여기서 관리자 권한 실행!
        except Exception as e:
            self.show_topmost_message("실행 실패", f"XXMI Launcher 실행 중 오류:\n{e}")
        

    def set_xxmi_launcher_path(self):
        path, _ = QFileDialog.getOpenFileName(self, "XXMI Launcher 실행파일 선택", "", "실행 파일 (*.exe)")
        if path:
            self.xxmi_launcher_path = path
            save_settings(
            self.settings_file,
            self.wwmi_mods_path,
            self.character_order,
            self.xxmi_launcher_path
        )

    def set_wwmi_path(self):
        path = QFileDialog.getExistingDirectory(self, "WWMI의 Mods 폴더 선택")
        if path:
            self.wwmi_mods_path = os.path.abspath(path)
            self.path_label.setText(f"WWMI Path: {self.wwmi_mods_path}")
            save_settings(
            self.settings_file,
            self.wwmi_mods_path,
            self.character_order,
            getattr(self, 'xxmi_launcher_path', None)  # 없으면 None 넘기기
        )

    def load_settings(self):
        self.wwmi_mods_path, self.character_order, self.xxmi_launcher_path = load_settings(self.settings_file)
        if self.wwmi_mods_path:
            self.path_label.setText(f"WWMI Path: {self.wwmi_mods_path}")

    def load_characters(self):
        self.character_list.clear()
        if not os.path.isdir(self.wwmm_mods_path):
            self.show_topmost_message("오류", f"WWMM의 Mods 폴더가 없습니다:\n{self.wwmm_mods_path}")
            return
        all_char_dirs = [
            d for d in os.listdir(self.wwmm_mods_path)
            if os.path.isdir(os.path.join(self.wwmm_mods_path, d))
        ]

        categories = {
            "기류": ["유노", "카르티시아", "샤콘", "감심", "양양", "기염", "알토"],
            "용융": ["갈브레나", "루파", "장리", "앙코", "치샤", "브렌트", "모르테피"],
            "인멸": ["플로로", "칸타렐라", "로코코", "카멜리아", "도기", "단근"],
            "회절": ["젠니", "페비", "파수인", "금희", "벨리나"],
            "응결": ["카를로타", "절지", "유호", "산화", "설지", "능양"],
            "전도": ["아우구스타", "음림", "상리요", "카카루", "루미", "연무"],
        }
        wanderer = ["방랑자"]

        category_icons = {
            "기류": "./icons/ic_기류.png",
            "용융": "./icons/ic_용융.png",
            "인멸": "./icons/ic_인멸.png",
            "회절": "./icons/ic_회절.png",
            "응결": "./icons/ic_응결.png",
            "전도": "./icons/ic_전도.png",
        }
        char_icons = {
            "방랑자": "./icons/char_방랑자.png",
            "갈브레나": "./icons/char_갈브레나.png",
            "유노": "./icons/char_유노.png",
            "아우구스타": "./icons/char_아우구스타.png",
            "플로로": "./icons/char_플로로.png",
            "루파": "./icons/char_루파.png",
            "카르티시아": "./icons/char_카르티시아.png",
            "샤콘": "./icons/char_샤콘.png",
            "젠니": "./icons/char_젠니.png",
            "칸타렐라": "./icons/char_칸타렐라.png",
            "페비": "./icons/char_페비.png",
            "로코코": "./icons/char_로코코.png",
            "카를로타": "./icons/char_카를로타.png",
            "카멜리아": "./icons/char_카멜리아.png",
            "파수인": "./icons/char_파수인.png",
            "절지": "./icons/char_절지.png",
            "장리": "./icons/char_장리.png",
            "금희": "./icons/char_금희.png",
            "음림": "./icons/char_음림.png",
            "벨리나": "./icons/char_벨리나.png",
            "앙코": "./icons/char_앙코.png",
            "감심": "./icons/char_감심.png",
            "브렌트": "./icons/char_브렌트.png",
            "상리요": "./icons/char_상리요.png",
            "기염": "./icons/char_기염.png",
            "카카루": "./icons/char_카카루.png",
            "능양": "./icons/char_능양.png",
            "루미": "./icons/char_루미.png",
            "유호": "./icons/char_유호.png",
            "양양": "./icons/char_양양.png",
            "산화": "./icons/char_산화.png",
            "설지": "./icons/char_설지.png",
            "치샤": "./icons/char_치샤.png",
            "단근": "./icons/char_단근.png",
            "도기": "./icons/char_도기.png",
            "모르테피": "./icons/char_모르테피.png",
            "연무": "./icons/char_연무.png",
            "알토": "./icons/char_알토.png",
        }

        category_colors = {
            "기류": "#00b894",
            "용융": "#e17055",
            "인멸": "#6c3483",
            "회절": "#fdcb6e",
            "응결": "#5e8ca6",
            "전도": "#a29bfe",
        }

        category_font = QFont(); category_font.setPointSize(15); category_font.setBold(True)
        char_font = QFont(); char_font.setPointSize(11)
        for char in wanderer:
            if char in all_char_dirs:
                item = QTreeWidgetItem(self.character_list, [char])
                if char in char_icons:
                    item.setIcon(0, QIcon(char_icons[char]))
                item.setFont(0, char_font)
        for category, char_list in categories.items():
            cat_item = QTreeWidgetItem([category])
            if category in category_icons:
                cat_item.setIcon(0, QIcon(category_icons[category]))
            cat_item.setFont(0, category_font)
            if category in category_colors:
                cat_item.setForeground(0, QBrush(QColor(category_colors[category])))
            has_child = False
            for char in char_list:
                if char in all_char_dirs:
                    child_item = QTreeWidgetItem(cat_item, [char])
                    if char in char_icons:
                        child_item.setIcon(0, QIcon(char_icons[char]))
                    child_item.setFont(0, char_font)
                    has_child = True
            if has_child:
                self.character_list.addTopLevelItem(cat_item)

    def clear_mod_cards(self):
        while self.mod_cards_layout.count():
            item = self.mod_cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def on_character_selected(self, item, _=None):
        if item.childCount() > 0:
            return
        char_name = item.text(0)
        self.current_character = char_name
        self.add_mod_button.setVisible(True)
        char_mod_path = os.path.join(self.wwmm_mods_path, char_name)
        applied_mod = self.get_applied_mod_name(char_name)
        self.clear_mod_cards()
        if not os.path.isdir(char_mod_path):
            return
        mod_folders = [
            d for d in os.listdir(char_mod_path)
            if os.path.isdir(os.path.join(char_mod_path, d))
        ]
        if not mod_folders:
            empty_card = EmptyModDropCard(self)
            self.mod_cards_layout.addWidget(empty_card, 0, 0, 1, 2)
            self.add_mod_button.setVisible(True)
            return
        for idx, mod_name in enumerate(sorted(mod_folders)):
            mod_path = os.path.join(char_mod_path, mod_name)
            preview_path = get_preview_image_path(mod_path)
            is_applied = (mod_name == applied_mod)
            row, col = divmod(idx, 2)
            self.add_mod_card(mod_name, preview_path, is_applied, True, row, col, mod_path)


    def add_mod_card(self, mod_name, image_path, is_applied, can_apply, row, col, mod_path):
        card = QFrame()
        card_layout = QVBoxLayout()
        card.setLayout(card_layout)
        card.setFrameShape(QFrame.Box)
        card.setLineWidth(1)
        card.setStyleSheet("""
            QFrame {
                background-color: #2c2c2c;
                border: 1px solid #444;
                border-radius: 10px;
                padding: 10px;
                color: white;
            }
        """)

        # 타이틀
        title = QLabel(f"모드 이름: {mod_name}" + (" ✅ 적용됨" if is_applied else ""))
        title.setAlignment(Qt.AlignCenter)

        # 미리보기
        preview = PreviewLabel(mod_path, wwmm_window=self, parent=card)
        preview.setAlignment(Qt.AlignCenter)
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                preview.setText("이미지 로딩 실패")
                preview.setFixedSize(300, 200)
            else:
                preview.setPixmap(pixmap.scaled(QSize(300, 200), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            preview.setText("미리보기 없음")
            preview.setFixedSize(300, 200)

        card_layout.addWidget(title)
        card_layout.addWidget(preview)

        # 적용/해제 버튼
        if can_apply:
            apply_btn = QPushButton("해제하기" if is_applied else "적용하기")
            apply_btn.setCursor(Qt.PointingHandCursor)  # 포인터 커서 추가!
            apply_btn.setStyleSheet("""
                QPushButton {
                    background-color: #47535f;
                    color: white;
                    border-radius: 8px;
                    font-weight: bold;
                    padding: 6px 0px;
                    font-size: 16px;
                    margin-top: 6px;
                    margin-bottom: 3px;
                }
                QPushButton:hover {
                    background-color: #5c8ef7;   /* 밝은 파랑계열로 강조 */
                    color: #fff;
                }
            """)
            def on_apply():
                action = "해제" if is_applied else "적용"
                reply = self.show_topmost_question(
                    f"모드 {action} 확인", f"정말 '{mod_name}' 모드를 {action}하시겠습니까?"
                )
                if reply == QMessageBox.Yes:
                    self.toggle_mod(mod_name, is_applied)
            apply_btn.clicked.connect(on_apply)
            card_layout.addWidget(apply_btn)

            # --- 삭제하기 버튼 추가 ---
            del_btn = QPushButton("삭제하기")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #b33939;
                    color: white;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: bold;
                    margin-top: 5px;
                }
                QPushButton:hover {
                    background-color: #e55039;
                }
            """)
            def on_delete():
                reply = self.show_topmost_question(
                    "모드 삭제", f"정말 '{mod_name}' 모드를 삭제하시겠습니까?"
                )
                if reply == QMessageBox.Yes:
                    delete_mod(
                        self.current_character, mod_name,
                        self.wwmm_mods_path, self.on_character_selected,
                        self.find_character_item, self
                    )
            del_btn.clicked.connect(on_delete)
            card_layout.addWidget(del_btn)

        self.mod_cards_layout.addWidget(card, row, col)

    def handle_preview_image_replace(self, mod_folder_path, new_image_path):
        ext = os.path.splitext(new_image_path)[1].lower()
        if ext not in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            self.show_topmost_message("지원하지 않는 확장자", "이미지 파일만 가능합니다.")
            return
        preview_path = os.path.join(mod_folder_path, f'preview{ext}')  # ★수정★

        # 기존 preview 있는지 체크
        existing = False
        for ex in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            p = os.path.join(mod_folder_path, f'preview{ex}')  # ★수정★
            if os.path.exists(p):
                preview_path = p
                existing = True
                break

        if existing:
            reply = self.show_topmost_question(
                "미리보기 이미지 변경",
                "이미 미리보기가 설정되어 있습니다. 미리보기를 변경하시겠습니까?"
            )
            if reply != QMessageBox.Yes:
                return

        # 이미지 복사(덮어쓰기)
        try:
            shutil.copyfile(new_image_path, preview_path)
            self.show_topmost_message("완료", "미리보기 이미지가 변경되었습니다.")
            # 새로고침
            self.on_character_selected(self.find_character_item(self.current_character))
        except Exception as e:
            self.show_topmost_message("오류", f"이미지 복사 실패: {e}")

    def open_preview_file_dialog(self, mod_folder_path):
        fname, _ = QFileDialog.getOpenFileName(self, "미리보기 이미지 선택", "", "이미지 파일 (*.png *.jpg *.jpeg *.bmp *.gif)")
        if fname:
            self.handle_preview_image_replace(mod_folder_path, fname)

    def find_character_item(self, char_name):
        for i in range(self.character_list.topLevelItemCount()):
            item = self.character_list.topLevelItem(i)
            for j in range(item.childCount()):
                child = item.child(j)
                if child.text(0) == char_name:
                    return child
            if item.childCount() == 0 and item.text(0) == char_name:
                return item
        return None

    def toggle_mod(self, mod_name, is_applied):

        if not self.wwmi_mods_path:
            self.show_topmost_message("경로 오류", "WWMI Mods 폴더 경로를 먼저 설정해주세요!")
            return
        
        char_name = self.current_character
        char_mod_path = os.path.join(self.wwmm_mods_path, char_name, mod_name)
        target_path = os.path.join(self.wwmi_mods_path, char_name)

        if is_applied:
            # 해제: 관리자 권한으로 helper 실행 ("remove")
            self.call_symlink_helper_as_admin("remove", "", target_path)
        else:
            # 적용: 관리자 권한으로 helper 실행 ("apply")
            self.call_symlink_helper_as_admin("apply", char_mod_path, target_path)

    def get_applied_mod_name(self, character_name):
        if not self.wwmi_mods_path:
            return None
        target_path = os.path.join(self.wwmi_mods_path, character_name)
        if os.path.islink(target_path):
            linked_path = os.readlink(target_path)
            return os.path.basename(os.path.normpath(linked_path))
        return None
    
    def call_symlink_helper_as_admin(self, mode, src, dst):
        import sys
        import os
        from wwmm_mod_utils import run_as_admin

        if getattr(sys, 'frozen', False):
            # 배포(EXE) 환경
            helper_path = os.path.join(os.path.dirname(sys.executable), "wwmm_symlink_helper.exe")
            if mode == "apply":
                params = [mode, src, dst]
            elif mode == "remove":
                params = [mode, dst]
            else:
                return False
            run_as_admin(helper_path, params)
        else:
            # 개발(스크립트) 환경
            helper_path = os.path.join(os.path.dirname(__file__), "wwmm_symlink_helper.py")
            if mode == "apply":
                params = [helper_path, mode, src, dst]
            elif mode == "remove":
                params = [helper_path, mode, dst]
            else:
                return False
            run_as_admin(sys.executable, params)

        # 권한 상승된 새 프로세스에서 작업을 하므로, 여기서는 바로 성공여부 판단 X
        # 약간의 딜레이 후 상태를 새로고침(예: 1~2초 뒤 refresh)
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self.on_character_selected(self.find_character_item(self.current_character)))

