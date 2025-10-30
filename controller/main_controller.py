# controller/main_controller.py
from __future__ import annotations
from typing import Optional, Tuple, Dict, Any
import os

from wwmm_logic_bridge import WWMMLogic

Ok = bool
Msg = str
Payload = Dict[str, Any]
Result = Tuple[Ok, Msg, Payload]


class MainController:
    def __init__(self, logic: WWMMLogic):
        self.logic = logic
        self._current_character: Optional[str] = None

    # --------------------- 내부 공통 처리 ---------------------
    def _standard_ok(self, msg="OK", payload=None) -> Result:
        return True, msg, payload or {}

    def _standard_fail(self, msg="오류", payload=None) -> Result:
        return False, msg, payload or {}

    # --------------------- Settings ---------------------
    def load_settings(self) -> Result:
        ok, msg, data = self.logic.load_settings()
        if not ok or not data:
            return self._standard_fail(msg or "설정 로드 실패")

        current_applied = None
        if self._current_character:
            current_applied = self.get_current_applied()

        wwmm_path = (
            data.get("wwmm_mods_path")
            if "wwmm_mods_path" in data
            else getattr(self.logic, "wwmm_mods_path", None)
        )
        wwmi_path = data.get("wwmi_mods_path", self.logic.wwmi_mods_path)

        payload = {
            "flags": {
                "can_launch_xxmi": bool(
                    data.get("xxmi_launcher_path")
                    and os.path.isfile(data.get("xxmi_launcher_path"))
                )
            },
            "settings": {
                "wwmm_mods_path": wwmm_path,
                "wwmi_mods_path": wwmi_path,
                "character_order": data.get("character_order"),
                "xxmi_launcher_path": data.get("xxmi_launcher_path"),
            }
        }
        return self._standard_ok("OK", payload)

    def set_wwmi_path(self, path: str) -> Result:
        if not path:
            return self._standard_fail("경로 비어 있음")
        ok, msg, data = self.logic.set_wwmi_path(path)
        if not ok:
            return self._standard_fail(msg or "WWMI 경로 설정 실패")

        payload = {"settings": {"wwmi_mods_path": data.get("wwmi_mods_path", path)}}
        return self._standard_ok("OK", payload)

    def set_xxmi_launcher_path(self, exe_path: str) -> Result:
        if not exe_path:
            return self._standard_fail("경로 비어 있음")
        ok, msg, data = self.logic.set_xxmi_launcher_path(exe_path)
        if not ok:
            return self._standard_fail(msg or "런처 경로 설정 실패")

        xxmi = data.get("xxmi_launcher_path", exe_path)
        payload = {
            "flags": {"can_launch_xxmi": bool(xxmi and os.path.isfile(xxmi))},
            "settings": {"xxmi_launcher_path": xxmi}
        }
        return self._standard_ok("OK", payload)

    def launch_xxmi(self) -> Result:
        ok, msg, _ = self.logic.launch_xxmi()
        if not ok:
            return self._standard_fail(msg or "런처 실행 실패")
        return self._standard_ok(msg or "OK")

    # --------------------- Characters ---------------------

    # ✅ 새로 추가된 부분: Core의 캐릭터 데이터 반환
    def get_character_data(self) -> Result:
        """
        UI가 캐릭터/속성/아이콘/색상 정의 데이터를 요청할 때 사용.
        UI는 데이터의 의미를 해석하지 않고 그대로 사용한다.
        """
        data = self.logic.get_character_data()
        return self._standard_ok("OK", {"characters": data})

    def load_characters(self, ui_character_list: list[str]) -> Result:
        if not ui_character_list:
            return self._standard_fail("UI 캐릭터 목록이 비어있습니다.")

        ok, msg, data = self.logic.list_available_characters()
        if not ok or not data:
            return self._standard_fail(msg or "캐릭터 조회 실패")

        installed_characters = data.get("characters", [])

        # ✅ 여기까지
        valid_characters = [c for c in ui_character_list if c in installed_characters]

        payload = {"lists": {"characters": valid_characters}}
        return self._standard_ok("OK", payload)

    def select_character(self, name: str) -> Result:
        if not name:
            return self._standard_fail("캐릭터 이름이 비어있습니다.")
        self._current_character = name

        ok, msg, data = self.logic.list_mods(name)
        if not ok or not data:
            return self._standard_fail(msg or "모드 목록 조회 실패")

        mods = data.get("mods", [])
        applied = data.get("applied")

        payload = {
            "selected": {"character": name, "applied_mod": applied},
            "lists": {"characters": [name], "mods": mods},
            "preview_map": data.get("preview_map", {}),
        }
        return self._standard_ok("OK", payload)

    def get_current_character(self) -> Optional[str]:
        return self._current_character

    def get_current_applied(self) -> Optional[str]:
        if not self._current_character:
            return None
        ok, _, data = self.logic.list_mods(self._current_character)
        return data.get("applied") if ok and data else None

    # --------------------- Mods ---------------------
    def add_mod_folder(self, folder_path: str) -> Result:
        if not self._current_character:
            return self._standard_fail("먼저 캐릭터를 선택하세요.")
        if not folder_path or not os.path.isdir(folder_path):
            return self._standard_fail("유효한 폴더가 아닙니다.")

        ok, msg, _ = self.logic.add_mod_from_folder(self._current_character, folder_path)
        if not ok:
            return self._standard_fail(msg or "모드 추가 실패")

        return self.select_character(self._current_character)

    def delete_mod(self, mod_name: str) -> Result:
        if not self._current_character:
            return self._standard_fail("먼저 캐릭터를 선택하세요.")
        if not mod_name:
            return self._standard_fail("모드명이 비어있습니다.")

        ok, msg, _ = self.logic.delete_mod(self._current_character, mod_name)
        if not ok:
            return self._standard_fail(msg or "모드 삭제 실패")

        return self.select_character(self._current_character)

    def toggle_mod(self, mod_name: str, apply: bool) -> Result:
        if not self._current_character:
            return self._standard_fail("먼저 캐릭터를 선택하세요.")
        if not mod_name:
            return self._standard_fail("모드명이 비어있습니다.")

        ok, msg, _ = self.logic.toggle_mod(self._current_character, mod_name, apply)
        if not ok:
            return self._standard_fail(msg or "모드 적용/해제 실패")

        return self.select_character(self._current_character)

    # --------------------- Preview ---------------------
    def replace_preview_by_mod(self, character_name: str, mod_name: str, new_image_path: str) -> Result:
        if not self._current_character:
            return self._standard_fail("먼저 캐릭터를 선택하세요.")
        if not mod_name or not new_image_path:
            return self._standard_fail("모드명 또는 이미지 경로가 비어있습니다.")

        ok, msg, _ = self.logic.replace_preview_by_mod(
            character_name, mod_name, new_image_path
        )
        if not ok:
            return self._standard_fail(msg or "프리뷰 교체 실패")

        return self.select_character(character_name)
