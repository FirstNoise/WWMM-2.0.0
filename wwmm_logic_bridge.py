# wwmm_logic_bridge.py
# 역할: UI ↔ core 연결 전용 Bridge
# ✅ 경로(wwmm_mods_path, wwmi_mods_path)는 오직 여기에서만 사용/조립된다.

from typing import Optional, Tuple, Dict, Any, List
import os
import subprocess

# core import
from core.settings_manager import (
    load_settings as core_load_settings,
    save_settings as core_save_settings,
)
from core.mod_manager import (
    add_mod_folder as core_add_mod_folder,
    delete_mod_folder as core_delete_mod_folder,
    get_preview_image_path as core_get_preview_image_path,
    replace_preview_image as core_replace_preview_image,
)
from core.directory_link_manager import (
    create_junction,
    remove_junction,
    get_junction_target,
)
from core.instance_lock import (
    is_another_instance_running as core_is_another_instance_running,
    write_lock as core_write_lock,
    remove_lock as core_remove_lock,
    install_atexit as core_install_lock_atexit,
)
from core.system_manager import (
    is_admin as core_is_admin,
    run_as_admin as core_run_as_admin,
)

# ✅ 새로 추가된 import (UI가 직접 접근하지 않도록 Bridge가 대신 연결)
from core.character_manager import get_character_data as core_get_character_data


class WWMMLogic:
    def __init__(
        self,
        wwmm_mods_path: str,
        settings_file: Optional[str] = None,
        wwmi_mods_path: Optional[str] = None,
    ):
        self.wwmm_mods_path = os.path.abspath(wwmm_mods_path) if wwmm_mods_path else ""
        self.settings_file = settings_file
        self.wwmi_mods_path = (
            os.path.abspath(wwmi_mods_path) if wwmi_mods_path else None
        )
        self.character_order: List[str] = []
        self.xxmi_launcher_path: Optional[str] = None

    # ---------------- Settings ----------------
    def load_settings(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.settings_file:
            return False, "settings_file 미지정", None

        wmm, wmi, order, launcher = core_load_settings(self.settings_file)

        # ✅ 실행 시 계산된 wwmm_mods_path 를 우선으로 유지
        if wmm:
            self.wwmm_mods_path = os.path.abspath(wmm)

        if wmi:
            self.wwmi_mods_path = os.path.abspath(wmi)
        
        self.character_order = order or []
        self.xxmi_launcher_path = launcher

        return True, "OK", {
            "wwmm_mods_path": self.wwmm_mods_path,
            "wwmi_mods_path": self.wwmi_mods_path,
            "character_order": self.character_order,
            "xxmi_launcher_path": self.xxmi_launcher_path,
        }

    def save_settings(self) -> Tuple[bool, str, None]:
        if not self.settings_file:
            return False, "settings_file 미지정", None
        try:
            core_save_settings(
                self.settings_file,
                self.wwmm_mods_path,    # ✅ 첫 번째는 무조건 wwmm 경로
                self.wwmi_mods_path,    # ✅ 두 번째가 wwmi 경로
                self.character_order,    # ✅ 순서 리스트
                self.xxmi_launcher_path, # ✅ 런처 경로
            )
            return True, "OK", None
        except Exception as e:
            return False, f"설정 저장 실패: {e}", None

    def set_wwmi_path(self, path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not path:
            return False, "경로 비어 있음", None
        self.wwmi_mods_path = os.path.abspath(path)
        if self.settings_file:
            core_save_settings(
                self.settings_file,
                self.wwmm_mods_path,
                self.wwmi_mods_path,
                self.character_order,
                self.xxmi_launcher_path,
            )
        return True, "OK", {"wwmi_mods_path": self.wwmi_mods_path}

    def set_xxmi_launcher_path(self, path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not path:
            return False, "경로 비어 있음", None
        self.xxmi_launcher_path = path
        if self.settings_file:
            core_save_settings(
                self.settings_file,
                self.wwmm_mods_path,
                self.wwmi_mods_path,
                self.character_order,
                self.xxmi_launcher_path,
            )
        return True, "OK", {"xxmi_launcher_path": self.xxmi_launcher_path}

    def launch_xxmi(self) -> Tuple[bool, str, None]:
        if not self.xxmi_launcher_path:
            return False, "XXMI 런처 경로가 설정되지 않았습니다.", None

        exe = os.path.abspath(self.xxmi_launcher_path)
        if not os.path.isfile(exe):
            return False, f"런처 실행 파일이 존재하지 않습니다: {exe}", None
        try:
            if core_is_admin():
                subprocess.Popen([exe], cwd=os.path.dirname(exe), shell=False)
            else:
                core_run_as_admin(exe, [])
            return True, "OK", None
        except Exception as e:
            return False, f"런처 실행 실패: {e}", None

    # ---------------- Characters ----------------
    # ✅ UI에서 캐릭터 데이터 요청 시 호출됨
    def get_character_data(self) -> Dict[str, Any]:
        return core_get_character_data()

    def list_available_characters(self) -> Tuple[bool, str, Dict[str, Any]]:
        if not self.wwmm_mods_path or not os.path.isdir(self.wwmm_mods_path):
            return False, "WWMM Mods 경로가 유효하지 않음", {"characters": []}
        try:
            chars = [
                d for d in os.listdir(self.wwmm_mods_path)
                if os.path.isdir(os.path.join(self.wwmm_mods_path, d))
            ]
            return True, "OK", {"characters": chars}
        except Exception as e:
            return False, f"캐릭터 목록 조회 실패: {e}", {"characters": []}

    # ---------------- Mods ----------------
    def list_mods(self, character_name: str) -> Tuple[bool, str, Dict[str, Any]]:
        if not character_name or not self.wwmm_mods_path:
            return False, "캐릭터 또는 WWMM 경로 누락", {"mods": [], "applied": None}

        char_path = os.path.join(self.wwmm_mods_path, character_name)
        if not os.path.isdir(char_path):
            return True, "캐릭터 폴더 없음", {"mods": [], "applied": None}

        try:
            mods = sorted([
                d for d in os.listdir(char_path)
                if os.path.isdir(os.path.join(char_path, d))
            ])
        except Exception as e:
            return False, f"모드 목록 조회 실패: {e}", {"mods": [], "applied": None}

        applied = self.get_applied_mod_name(character_name)
        return True, "OK", {
            "mods": mods,
            "applied": applied,
            "preview_map": {
                m: self.get_preview_image_path(os.path.join(char_path, m)) for m in mods
            }
        }

    def get_applied_mod_name(self, character_name: str) -> Optional[str]:
        if not self.wwmi_mods_path:
            return None

        dst = os.path.join(self.wwmi_mods_path, character_name)
        target = get_junction_target(dst)

        # ✅ 정션이 존재하면 → 적용된 모드명 반환
        if target:
            return os.path.basename(os.path.normpath(target))

        # ✅ 정션이 없다 → 적용된 모드 없음
        return None

    def toggle_mod(self, character_name: str, mod_name: str, apply: bool) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not (self.wwmi_mods_path and self.wwmm_mods_path):
            return False, "경로 미설정", None

        src = os.path.join(self.wwmm_mods_path, character_name, mod_name)
        dst = os.path.join(self.wwmi_mods_path, character_name)
        if not os.path.isdir(src):
            return False, "모드 폴더 없음", None

        if apply:
            ok, msg = create_junction(src, dst)
        else:
            ok, msg = remove_junction(dst)

        return (ok, msg, {"character": character_name}) if ok else (False, msg, None)

    def add_mod_from_folder(self, character_name: str, src_folder_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not character_name or not self.wwmm_mods_path:
            return False, "전제 조건 부족", None
        ok, msg = core_add_mod_folder(character_name, src_folder_path, self.wwmm_mods_path)
        return (ok, msg, {"character": character_name}) if ok else (False, msg, None)

    def delete_mod(self, character_name: str, mod_name: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not character_name or not self.wwmm_mods_path:
            return False, "전제 조건 부족", None
        ok, msg = core_delete_mod_folder(character_name, mod_name, self.wwmm_mods_path)
        return (ok, msg, {"character": character_name}) if ok else (False, msg, None)

    # ---------------- Preview ----------------
    def get_preview_image_path(self, mod_path: str) -> Optional[str]:
        return core_get_preview_image_path(mod_path)

    def replace_preview(self, mod_folder_path: str, new_image_path: str) -> Tuple[bool, str, None]:
        ok, msg = core_replace_preview_image(mod_folder_path, new_image_path)
        return (ok, msg, None) if ok else (False, msg, None)

    def replace_preview_by_mod(self, character_name: str, mod_name: str, new_image_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not character_name or not mod_name:
            return False, "전제 조건 부족", None

        mod_folder = os.path.join(self.wwmm_mods_path, character_name, mod_name)
        if not os.path.isdir(mod_folder):
            return False, "모드 폴더 없음", None

        ok, msg = core_replace_preview_image(mod_folder, new_image_path)
        return (ok, msg, {"character": character_name}) if ok else (False, msg, None)

    # ---------------- Instance Lock ----------------
    def is_another_instance_running(self) -> bool:
        return core_is_another_instance_running()

    def write_instance_lock(self) -> None:
        core_write_lock()

    def remove_instance_lock(self) -> None:
        core_remove_lock()

    def install_instance_lock_atexit(self) -> None:
        core_install_lock_atexit()
