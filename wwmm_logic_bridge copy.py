# wwmm_logic_bridge.py
# 역할: UI ↔ core 연결 전용 Bridge. UI 상태를 가지지 않으며 core 기능만 호출한다.
# - UI는 core를 직접 import/호출하지 않는다.
# - 파일시스템 접근/비즈니스 로직은 core로 위임한다.
# - Bridge는 필요한 데이터를 메서드로 반환해 UI가 그대로 표시하도록 한다.

# NOTE: core.system_manager는 향후 관리자 권한 실행 기능을 위한 확장 포인트로 core에만 보존한다.
#       현재 릴리스 경로(Bridge/UI)에서는 사용하지 않는다.

from typing import Optional, Tuple, Dict, Any, List
import os

# ✅ core 기능만 import
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
from core.character_manager import get_character_data as core_get_character_data

# ➕ 추가: core의 나머지 유틸도 Bridge에서 감싸서 UI가 직접 접근하지 않도록 한다.
from core.instance_lock import (
    is_another_instance_running as core_is_another_instance_running,
    write_lock as core_write_lock,
    remove_lock as core_remove_lock,
    install_atexit as core_install_lock_atexit,
)

# from core.system_manager import (
#     is_admin as core_is_admin,
#     run_as_admin as core_run_as_admin,
# )


class WWMMLogic:
    def __init__(
        self,
        wwmm_mods_path: str,
        settings_file: Optional[str] = None,
        wwmi_mods_path: Optional[str] = None
    ):
        """
        Bridge는 오직 환경값(경로, 설정파일)만 가진다.
        UI 상태(QTreeWidgetItem 등)는 절대 저장하지 않는다.
        """
        self.wwmm_mods_path = os.path.abspath(wwmm_mods_path) if wwmm_mods_path else ""
        self.settings_file = settings_file
        self.wwmi_mods_path = wwmi_mods_path
        self.character_order: List[str] = []
        self.xxmi_launcher_path: Optional[str] = None

    # ---------------- Settings ----------------
    def load_settings(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """settings.json을 core로부터 읽고 Bridge 내부 상태에 반영."""
        if not self.settings_file:
            return False, "settings_file 미지정", None

        wwmi_mods_path, character_order, xxmi_launcher_path = core_load_settings(self.settings_file)
        self.wwmi_mods_path = wwmi_mods_path
        self.character_order = character_order or []
        self.xxmi_launcher_path = xxmi_launcher_path

        return True, "OK", {
            "wwmi_mods_path": self.wwmi_mods_path,
            "character_order": self.character_order,
            "xxmi_launcher_path": self.xxmi_launcher_path,
        }

    def save_settings(self) -> Tuple[bool, str, None]:
        """현재 Bridge 내부 상태를 settings.json에 저장."""
        if not self.settings_file:
            return False, "settings_file 미지정", None
        try:
            core_save_settings(self.settings_file, self.wwmi_mods_path, self.character_order, self.xxmi_launcher_path)
            return True, "OK", None
        except Exception as e:
            return False, f"설정 저장 실패: {e}", None

    def set_wwmi_path(self, path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """WWMI 경로 설정 후 저장."""
        if not path:
            return False, "경로 비어 있음", None
        self.wwmi_mods_path = os.path.abspath(path)
        if self.settings_file:
            core_save_settings(self.settings_file, self.wwmi_mods_path, self.character_order, self.xxmi_launcher_path)
        return True, "OK", {"wwmi_mods_path": self.wwmi_mods_path}

    def set_xxmi_launcher_path(self, path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """XXMI 실행 파일 경로 설정 후 저장."""
        if not path:
            return False, "경로 비어 있음", None
        self.xxmi_launcher_path = path
        if self.settings_file:
            core_save_settings(self.settings_file, self.wwmi_mods_path, self.character_order, self.xxmi_launcher_path)
        return True, "OK", {"xxmi_launcher_path": self.xxmi_launcher_path}

    # ---------------- Character Data (from core) ----------------
    def get_character_data(self) -> Dict[str, Any]:
        """
        core/character_manager.py가 제공하는 캐릭터 메타정보(카테고리, 아이콘, 컬러 등)를 반환.
        UI는 이 dict 기반으로 트리를 구성한다.
        """
        return core_get_character_data()

    def list_available_characters(self) -> Tuple[bool, str, Dict[str, Any]]:
        """
        WWMM(Mods 저장소)에서 실제 디렉터리가 존재하는 캐릭터 목록만 반환.
        UI는 os.listdir을 직접 쓰지 않고 이 메서드만 호출한다.
        """
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

    # ---------------- Mod List / Applied Info ----------------
    def list_mods(self, character_name: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        특정 캐릭터의 모드 목록 + 적용중 모드명을 반환.
        UI는 이 결과로만 적용여부를 판단하고 렌더링한다.
        """
        if not self.wwmm_mods_path or not character_name:
            return False, "캐릭터 또는 WWMM 경로 누락", {"mods": [], "applied": None}

        char_mod_path = os.path.join(self.wwmm_mods_path, character_name)
        if not os.path.isdir(char_mod_path):
            return True, "캐릭터 폴더 없음", {"mods": [], "applied": None}

        try:
            mods = sorted([
                d for d in os.listdir(char_mod_path)
                if os.path.isdir(os.path.join(char_mod_path, d))
            ])
        except Exception as e:
            return False, f"모드 목록 조회 실패: {e}", {"mods": [], "applied": None}

        applied = self.get_applied_mod_name(character_name)
        return True, "OK", {"mods": mods, "applied": applied}

    # ---------------- Mod Apply / Remove via Junction ----------------
    def toggle_mod(self, character_name: str, mod_name: str, is_applied: bool) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        junction(정션)을 통해 모드를 적용/해제한다.
        적용:  create_junction(src, dst)
        해제:  remove_junction(dst)
        """
        if not (self.wwmm_mods_path and self.wwmi_mods_path and character_name and mod_name):
            return False, "전제 조건 부족(경로/캐릭터/모드)", None

        src = os.path.join(self.wwmm_mods_path, character_name, mod_name)
        dst = os.path.join(self.wwmi_mods_path, character_name)

        if is_applied:
            ok, msg = remove_junction(dst)
        else:
            ok, msg = create_junction(src, dst)

        return (ok, msg, {"refresh_character": character_name}) if ok else (False, msg, None)

    def get_applied_mod_name(self, character_name: str) -> Optional[str]:
        """현재 WWMI/<캐릭터> 정션이 가리키는 실제 모드 폴더명을 반환. 없으면 None."""
        if not (self.wwmi_mods_path and character_name):
            return None
        dst = os.path.join(self.wwmi_mods_path, character_name)
        target = get_junction_target(dst)
        if not target:
            return None
        return os.path.basename(os.path.normpath(target))

    # ---------------- Mod Add / Delete ----------------
    def add_mod_from_folder(self, char_name: str, src_folder_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """외부 폴더를 WWMM/<캐릭터>/<모드>로 복사한다."""
        if not (char_name and src_folder_path and self.wwmm_mods_path):
            return False, "전제 조건 부족(캐릭터/경로/WWMM 경로)", None
        ok, msg = core_add_mod_folder(char_name, src_folder_path, self.wwmm_mods_path)
        return (ok, msg, {"refresh_character": char_name}) if ok else (False, msg, None)

    def delete_mod(self, char_name: str, mod_name: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """WWMM/<캐릭터>/<모드> 폴더를 삭제한다."""
        if not (char_name and mod_name and self.wwmm_mods_path):
            return False, "전제 조건 부족(캐릭터/모드/WWMM 경로)", None
        ok, msg = core_delete_mod_folder(char_name, mod_name, self.wwmm_mods_path)
        return (ok, msg, {"refresh_character": char_name}) if ok else (False, msg, None)

    # ---------------- Preview Image ----------------
    def replace_preview(self, mod_folder_path: str, new_image_path: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """mod_folder 내 preview.* 파일을 교체/생성한다."""
        ok, msg = core_replace_preview_image(mod_folder_path, new_image_path)
        return (ok, msg, None) if ok else (False, msg, None)

    @staticmethod
    def get_preview_image_path(mod_path: str) -> Optional[str]:
        """preview.* 경로를 반환 (없으면 None)."""
        return core_get_preview_image_path(mod_path)

    # ---------------- Instance Lock (single instance) ----------------
    def is_another_instance_running(self) -> bool:
        """다른 인스턴스가 실행 중인지 여부."""
        return core_is_another_instance_running()

    def write_instance_lock(self) -> None:
        """현재 프로세스 PID를 lock 파일에 기록."""
        core_write_lock()

    def remove_instance_lock(self) -> None:
        """lock 파일 제거."""
        core_remove_lock()

    def install_instance_lock_atexit(self) -> None:
        """프로세스 종료 시 lock 자동 제거."""
        core_install_lock_atexit()

    # ---------------- System utilities ----------------
    # def is_admin(self) -> bool:
    #     """관리자 권한 여부(Windows 전용)."""
    #     return core_is_admin()

    # def run_as_admin(self, exe_path: str, params: List[str]):
    #     """
    #     관리자 권한으로 프로그램 실행.
    #     exe_path: 실행 파일 경로
    #     params: 인자 리스트
    #     반환값: ShellExecuteW 반환값
    #     """
    #     return core_run_as_admin(exe_path, params)
