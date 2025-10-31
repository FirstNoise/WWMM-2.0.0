# ui/views/main_window.py

import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFileDialog, QDialog, QTreeWidgetItem
)
from PyQt5.QtGui import QIcon, QColor, QBrush, QPainter
from PyQt5.QtCore import QFileSystemWatcher, Qt
from PyQt5.QtWidgets import QSizeGrip

from utils.styled_widget import StyledWidget

# ✅ UI 구성 요소
from ui.components.topbar import TopBar
from ui.components.sidebar import SideBar
from ui.components.mod_cards import ModCardsContainer, EmptyModDropCard
from ui.components.mod_card import ModCard
from ui.dialogs.settings_dialog import SettingsDialog

# ✅ Controller
from controller.main_controller import MainController

# 투명 장벽을 세움으로서 클릭 이벤트 관통을 방지
class CentralSurface(StyledWidget):
    def paintEvent(self, event):
        # 여기에 "투명하지만 존재하는 픽셀" 장벽을 단 1회만 생성
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 1))  # 알파 1 = 육안에 안보이지만 존재

class MainWindow(QMainWindow):
    
    """ModsView 제거 후 완전 분리형 UI 구조 (조립 중심형)"""

    def _remember_tree_expansion(self):
        expanded = {}
        root = self.sidebar.tree.invisibleRootItem()
        stack = [root]
        while stack:
            item = stack.pop()
            expanded[item.text(0)] = item.isExpanded()
            for i in range(item.childCount()):
                stack.append(item.child(i))
        return expanded

    def _restore_tree_expansion(self, expanded):
        root = self.sidebar.tree.invisibleRootItem()
        stack = [root]
        while stack:
            item = stack.pop()
            name = item.text(0)
            if name in expanded:
                item.setExpanded(expanded[name])
            for i in range(item.childCount()):
                stack.append(item.child(i))

    def _expand_parent_of_character(self, char_name):
        root = self.sidebar.tree.invisibleRootItem()
        stack = [root]
        while stack:
            item = stack.pop()
            if item.text(0) == char_name and item.parent():
                item.parent().setExpanded(True)
                return
            for i in range(item.childCount()):
                stack.append(item.child(i))


    def __init__(self, controller: MainController):
        super().__init__()
        self.controller = controller
        self.current_character = None

        self.setMinimumSize(1280, 720)

        # ✅ 파일 변경 감시자 생성
        self.watcher = QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self._on_mods_directory_changed)

        # ✅ UI 구성
        self.topbar = TopBar(self)
        self.sidebar = SideBar(self)

        # (1) 모드 카드 UI 생성
        self.mod_cards = ModCardsContainer(self)
        self.mod_cards.controller = self.controller  # ✅ 이 한 줄

        # ✅ 레이아웃 조립
        central = CentralSurface()
        central.class_name = "CentralBackground"   # ✅ QSS `.CentralBackground` 와 매칭
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        content_layout = QHBoxLayout()

        # TopBar (상단 고정 UI)
        main_layout.addWidget(self.topbar)

        # 사이드바 + 드랍 가능 메인 영역
        # ✅ 비율 1 : 3 적용 (= 25:75 UI 균형)
        
        content_layout.addWidget(self.sidebar, 1)
        content_layout.addWidget(self.mod_cards, 3)  # ✅ 변경된 부분 (mod_cards X)

        main_layout.addLayout(content_layout)

        self._add_resize_handle()
        # 시그널 연결
        self._connect_signals()

        # 초기 실행
        self.initialize_app()


    # ---------------------------------------------------
    # 초기 실행
    # ---------------------------------------------------
    def initialize_app(self):
    # ✅ 캐릭터 메타 구조 불러오기
        ok, msg, payload = self.controller.get_character_data()
        if not ok:
            QMessageBox.warning(self, "오류", msg)
            return

        meta = payload.get("characters", {})
        self._meta = meta  # ✅ 저장한다 (이제 재사용 가능)
        self.build_sidebar(meta)  # ✅ 트리 생성은 1회만

        # ✅ 실제 설치된 캐릭터 필터링
        categories = meta.get("categories", {})
        ui_characters = [c for group in categories.values() for c in group] + meta.get("wanderer", [])
        ok, msg, payload = self.controller.load_characters(ui_characters)
        self.apply_payload(ok, msg, payload)

        # ✅ 감시자 연결 그대로 유지
        mods_root = self.controller.logic.wwmm_mods_path
        if os.path.isdir(mods_root):
            self.watcher.addPath(mods_root)
            self._refresh_mods_watch_targets()

        ok, msg, payload = self.controller.load_settings()
        self.apply_payload(ok, msg, payload)


    # ---------------------------------------------------
    # Sidebar 초기 생성 함수 추가
    # ---------------------------------------------------

    def build_sidebar(self, meta):
        categories = meta.get("categories", {})
        category_icons = meta.get("category_icons", {})
        category_colors = meta.get("category_colors", {})
        char_icons = meta.get("char_icons", {})
        wanderers = meta.get("wanderer", [])

        self.sidebar.tree.clear()

        # ✅ 방랑자 캐릭터
        for char in wanderers:
            item = QTreeWidgetItem([char])
            icon = char_icons.get(char)
            if icon and os.path.exists(icon):
                item.setIcon(0, QIcon(icon))
            self.sidebar.tree.insertTopLevelItem(0, item)

        # ✅ 카테고리/캐릭터 구조
        for category, chars in categories.items():
            parent = QTreeWidgetItem([category])

            if category in category_colors:
                parent.setForeground(0, QBrush(QColor(category_colors[category])))

            icon = category_icons.get(category)
            if icon and os.path.exists(icon):
                parent.setIcon(0, QIcon(icon))

            self.sidebar.tree.addTopLevelItem(parent)

            for char in chars:
                child = QTreeWidgetItem([char])
                icon = char_icons.get(char)
                if icon and os.path.exists(icon):
                    child.setIcon(0, QIcon(icon))
                parent.addChild(child)

    # ---------------------------------------------------
    # Sidebar 선택만 갱신
    # ---------------------------------------------------

    def update_sidebar_selection(self, character):
        item = self._find_tree_item(character)
        if item:
            self.sidebar.tree.setCurrentItem(item)
            self._expand_parent_of_character(character)

    # ---------------------------------------------------
    # 모드 카드 갱신 전용 함수
    # ---------------------------------------------------

    def update_mod_cards(self, mods, applied_mod, preview_map):
        self.mod_cards.clear_cards()

        if not mods:
            return

        for mod in mods:
            mod_folder = os.path.join(self.controller.logic.wwmm_mods_path, self.current_character, mod)
            preview = preview_map.get(mod)
            card = ModCard(mod, mod_folder, preview, applied=(mod == applied_mod))

            card.applyRequested.connect(self._handle_mod_apply)
            card.deleteRequested.connect(self._handle_mod_delete)
            card.previewRequested.connect(self._handle_preview_clicked)
            card.preview_label.previewDropped.connect(
                lambda folder, img, mod_name=mod: self._handle_preview_dropped(mod_name, img)
            )


            self.mod_cards.add_card(card)


    # ---------------------------------------------------
    # 현재 선택된 캐릭터 유지하며 UI만 갱신
    # ---------------------------------------------------

    def _on_mods_directory_changed(self, path):
        # ✅ 변경된 폴더가 생겼을 수 있으니 감시 목록 다시 갱신
        self._refresh_mods_watch_targets()

        # ✅ 캐릭터 선택 유지한 채 UI 갱신
        if not self.current_character:
            return

        ok, msg, payload = self.controller.select_character(self.current_character)
        self.apply_payload(ok, msg, payload)
        
    # ---------------------------------------------------
    # 재귀적으로 감시 대상 갱신하는 함수
    # ---------------------------------------------------

    def _refresh_mods_watch_targets(self):
        mods_root = self.controller.logic.wwmm_mods_path

        # ✅ 감시 목록 초기화
        old = self.watcher.directories()
        if old:
            self.watcher.removePaths(old)

        # ✅ mods 루트만 감시 (하위 폴더 전체 감시 금지)
        if os.path.isdir(mods_root):
            self.watcher.addPath(mods_root)

        # ✅ 현재 캐릭터 폴더도 감시
        if self.current_character:
            char_dir = os.path.join(mods_root, self.current_character)
            if os.path.isdir(char_dir):
                self.watcher.addPath(char_dir)



    # ---------------------------------------------------
    # payload 적용 (조립 완성형)
    # ---------------------------------------------------
    def apply_payload(self, ok, msg, payload):
        if not ok:
            QMessageBox.warning(self, "오류", msg)
            return

        if not payload:
            return

        lists = payload.get("lists", {})
        selected = payload.get("selected", {})

        # ✅ 캐릭터 변경 처리
        if "character" in selected:
            self.current_character = selected["character"]
            self.update_sidebar_selection(self.current_character)

        # ✅ 모드 목록 갱신
        if "mods" in lists and self.current_character:
            mods = lists["mods"]
            applied_mod = selected.get("applied_mod")
            preview_map = payload.get("preview_map", {})
            self.update_mod_cards(mods, applied_mod, preview_map)

    # ---------------------------------------------------
    # 트리 탐색
    # ---------------------------------------------------
    
    def _find_tree_item(self, name):
        root = self.sidebar.tree.invisibleRootItem()
        stack = [root]
        while stack:
            item = stack.pop()
            if item.text(0) == name:
                return item
            for i in range(item.childCount()):
                stack.append(item.child(i))
        return None

    # ---------------------------------------------------
    # 시그널 연결
    # ---------------------------------------------------
    def _handle_tree_item_clicked(self, item, column):
        # 부모가 None → 카테고리 → 클릭 무시
        #if item.parent() is None:
        #    return

        # ✅ Top-Level 이면서 자식이 없는 경우 → "방랑자" 같은 단일 캐릭터
        if item.parent() is None and item.childCount() == 0:
            char_name = item.text(0)
            ok, msg, payload = self.controller.select_character(char_name)
            self.apply_payload(ok, msg, payload)
            return

        # ✅ 카테고리 클릭 → 펼치기/접기 toggle
        if item.parent() is None:
            item.setExpanded(not item.isExpanded())
            return

        # 자식 노드 → 캐릭터
        char_name = item.text(0)
        ok, msg, payload = self.controller.select_character(char_name)
        self.apply_payload(ok, msg, payload)
        
    def _connect_signals(self):
        self.topbar.btn_settings.clicked.connect(self.open_settings_dialog)
        self.topbar.btn_start.clicked.connect(self.on_start_xmmi)
        self.sidebar.tree.itemClicked.connect(self._handle_tree_item_clicked)

    # ---------------------------------------------------
    # 캐릭터 클릭
    # ---------------------------------------------------
    def on_character_clicked(self, char_name: str):
        ok, msg, payload = self.controller.select_character(char_name)
        self.apply_payload(ok, msg, payload)

    # ---------------------------------------------------
    # 모드 추가 (드래그)
    # ---------------------------------------------------
    def _handle_mod_folder_dropped(self, folder_path: str):
        if not self.current_character:
            QMessageBox.warning(self, "캐릭터 필요", "캐릭터 먼저 선택해주세요.")
            return
        ok, msg, payload = self.controller.add_mod_folder(folder_path)
        self.apply_payload(ok, msg, payload)

    # ---------------------------------------------------
    # 모드 삭제
    # ---------------------------------------------------
    def _handle_mod_delete(self, mod_name: str):
        if not self.current_character:
            QMessageBox.warning(self, "캐릭터 필요", "캐릭터 먼저 선택해주세요.")
            return
        ok, msg, payload = self.controller.delete_mod(mod_name)
        self.apply_payload(ok, msg, payload)

    # ---------------------------------------------------
    # 모드 적용/해제
    # ---------------------------------------------------
    def _handle_mod_apply(self, mod_name: str):
        if not self.current_character:
            QMessageBox.warning(self, "캐릭터 필요", "캐릭터 먼저 선택해주세요.")
            return
        current_applied = self.controller.get_current_applied()
        apply_flag = not (current_applied == mod_name)
        ok, msg, payload = self.controller.toggle_mod(mod_name, apply_flag)
        self.apply_payload(ok, msg, payload)

    # ---------------------------------------------------
    # 프리뷰 선택 (수동)
    # ---------------------------------------------------
    def _handle_preview_clicked(self, folder_path: str):
        if not self.current_character:
            QMessageBox.warning(self, "캐릭터 필요", "캐릭터 선택 후 사용 가능합니다.")
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "미리보기 이미지 선택", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not file_path:
            return
        ok, msg, payload = self.controller.replace_preview_by_mod(
            self.current_character, os.path.basename(folder_path), file_path
        )
        self.apply_payload(ok, msg, payload)

    # ---------------------------------------------------
    # 프리뷰 드래그 교체
    # ---------------------------------------------------
    def _handle_preview_dropped(self, mod_name: str, image_path: str):
        if not self.current_character:
            QMessageBox.warning(self, "캐릭터 필요", "캐릭터 선택 후 사용 가능합니다.")
            return
        ok, msg, payload = self.controller.replace_preview_by_mod(
            self.current_character, mod_name, image_path
            )
        self.apply_payload(ok, msg, payload)

    # ---------------------------------------------------
    # 설정창
    # ---------------------------------------------------
    def open_settings_dialog(self):
        # ✅ Controller 로부터 현재 settings.json 값을 읽는다
        ok, msg, data = self.controller.load_settings()
        if not ok:
            QMessageBox.warning(self, "오류", msg)
            return

        settings = data.get("settings", {})
        wwmi_path = settings.get("wwmi_mods_path", "") or ""
        xxmi_path = settings.get("xxmi_launcher_path", "") or ""

        # ✅ 현재 설정값을 UI로 전달
        dialog = SettingsDialog(self, wwmi_path=wwmi_path, xxmi_path=xxmi_path)

        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()

            new_wwmi = data.get("wwmi_path")
            new_xxmi = data.get("xxmi_path")

            if new_wwmi:
                self.apply_payload(*self.controller.set_wwmi_path(new_wwmi))
            if new_xxmi:
                self.apply_payload(*self.controller.set_xxmi_launcher_path(new_xxmi))


    def _add_resize_handle(self):
        """오른쪽-하단 모서리에 투명 크기조절 핸들 추가"""
        self._grip = QSizeGrip(self)
        self._grip.setStyleSheet("QSizeGrip { background: transparent; }")
        self._grip.setFixedSize(20, 20)
        self._reposition_grip()

        # ✅ 항상 오른쪽 아래 위치 고정
    def _reposition_grip(self):
        self._grip.move(self.width() - self._grip.width(), self.height() - self._grip.height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_grip()

    # ---------------------------------------------------
    # XXMI 실행
    # ---------------------------------------------------
    def on_start_xmmi(self):
        ok, msg, _ = self.controller.launch_xxmi()
        if not ok:
            QMessageBox.warning(self, "실행 오류", msg)
