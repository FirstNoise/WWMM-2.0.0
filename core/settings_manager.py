# core/settings_manager.py

import os
import json

def load_settings(settings_file):
    """settings.json 파일을 읽어 프로그램 설정 반환"""
    wwmm_mods_path = None
    wwmi_mods_path = None
    character_order = []
    xxmi_launcher_path = None

    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                wwmm_mods_path = data.get("wwmm_mods_path")
                wwmi_mods_path = data.get("wwmi_mods_path")
                character_order = data.get("character_order", [])
                xxmi_launcher_path = data.get("xxmi_launcher_path")
        except Exception as e:
            print(f"[설정 로드 실패] {e}")

    return wwmm_mods_path, wwmi_mods_path, character_order, xxmi_launcher_path


def save_settings(settings_file, wwmm_mods_path, wwmi_mods_path, character_order, xxmi_launcher_path):
    try:
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump({
                "wwmm_mods_path": wwmm_mods_path,
                "wwmi_mods_path": wwmi_mods_path,
                "character_order": character_order,
                "xxmi_launcher_path": xxmi_launcher_path
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[설정 저장 실패] {e}")