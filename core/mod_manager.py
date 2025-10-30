# core/mod_manager.py
import os
import shutil
from typing import Tuple, Optional

_SUPPORTED_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".gif")

def add_mod_folder(char_name: str, src_folder_path: str, wwmm_mods_path: str) -> Tuple[bool, str]:
    """
    wwmm_mods_path/<char_name>/<mod_folder> 으로 소스 폴더를 복사합니다.
    반환: (성공여부, 메시지)
    """
    if not char_name or not src_folder_path or not wwmm_mods_path:
        return False, "캐릭터명, 소스 폴더 또는 WWMM 경로가 비어있습니다."

    src_folder_path = os.path.abspath(src_folder_path)
    wwmm_mods_path = os.path.abspath(wwmm_mods_path)

    if not os.path.isdir(src_folder_path):
        return False, f"복사할 폴더가 존재하지 않습니다: {src_folder_path}"

    mod_folder_name = os.path.basename(src_folder_path.rstrip("/\\"))
    dst = os.path.join(wwmm_mods_path, char_name, mod_folder_name)

    if os.path.exists(dst):
        return False, f"이미 동일한 모드 폴더가 존재합니다: {dst}"

    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(src_folder_path, dst)
        return True, "OK"
    except Exception as e:
        return False, f"모드 복사 실패: {e}"

def delete_mod_folder(char_name: str, mod_name: str, wwmm_mods_path: str) -> Tuple[bool, str]:
    """
    wwmm_mods_path/<char_name>/<mod_name> 폴더를 삭제합니다.
    반환: (성공여부, 메시지)
    """
    if not char_name or not mod_name or not wwmm_mods_path:
        return False, "캐릭터명, 모드명 또는 WWMM 경로가 비어있습니다."

    target = os.path.join(os.path.abspath(wwmm_mods_path), char_name, mod_name)

    if not os.path.exists(target):
        return False, f"대상 폴더가 존재하지 않습니다: {target}"

    try:
        # 안전을 위해 파일 권한 문제 등으로 삭제가 실패할 수 있으므로 예외 처리
        shutil.rmtree(target)
        return True, "OK"
    except Exception as e:
        return False, f"모드 삭제 실패: {e}"

def get_preview_image_path(mod_path: str) -> Optional[str]:
    """
    모드 폴더 내부에서 preview.<ext> 파일을 찾아 절대 경로로 반환합니다.
    없으면 None 반환.
    """
    if not mod_path:
        return None
    mod_path = os.path.abspath(mod_path)
    for ext in _SUPPORTED_EXTS:
        preview_path = os.path.join(mod_path, f"preview{ext}")
        if os.path.isfile(preview_path):
            return preview_path
    return None

def replace_preview_image(mod_folder: str, new_image: str) -> Tuple[bool, str]:
    """
    mod_folder 내부의 preview.* 파일을 new_image로 교체하거나 새로 생성합니다.
    동작:
      - new_image가 존재하고 지원 확장자여야 함.
      - 기존 preview.* 파일이 있으면 그 파일 경로에 덮어씀.
      - 기존 preview.* 파일이 없으면 new_image 확장자로 preview.<ext> 생성.
    반환: (성공여부, 메시지)
    """
    if not mod_folder or not new_image:
        return False, "모드 폴더 또는 이미지 경로가 비어있습니다."

    mod_folder = os.path.abspath(mod_folder)
    new_image = os.path.abspath(new_image)

    if not os.path.isdir(mod_folder):
        return False, "모드 폴더 경로가 유효하지 않습니다."

    if not os.path.isfile(new_image):
        return False, "지정한 이미지 파일이 존재하지 않습니다."

    ext = os.path.splitext(new_image)[1].lower()
    if ext not in _SUPPORTED_EXTS:
        return False, f"지원하지 않는 확장자입니다: {ext}"

    preview_path = os.path.join(mod_folder, f"preview{ext}")

    # 기존 preview.* 파일이 있으면 그 파일 경로를 사용
    for ex in _SUPPORTED_EXTS:
        p = os.path.join(mod_folder, f"preview{ex}")
        if os.path.exists(p):
            preview_path = p
            break

    try:
        shutil.copyfile(new_image, preview_path)
        return True, "미리보기 이미지가 변경되었습니다."
    except Exception as e:
        return False, f"이미지 복사 실패: {e}"
