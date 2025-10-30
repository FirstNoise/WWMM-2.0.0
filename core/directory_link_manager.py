# core/directory_link_manager.py
# 목적: Windows에서 정션(Junction) 생성/제거/조회 기능 제공
# - 디렉터리 정션(/J)은 일반적으로 관리자 권한이 필요하지 않음
# - NTFS/권한/조직 정책/기존 경로 상태 등에 따라 실패 가능
# - UI/Bridge는 이 모듈의 함수만 호출

import os
import subprocess
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# ----------------------------------------------------
# 내부 유틸
# ----------------------------------------------------
def _abs(path: str) -> str:
    return os.path.abspath(path)

def _is_junction(path: str) -> bool:
    """
    정션(디렉터리 링크) 여부 판별.
    - os.path.islink()는 Windows 정션에서 False가 될 수 있음
    - ReparsePoint + 디렉터리 조합으로 판단
    """
    try:
        st = os.lstat(path)
        attrs = getattr(st, "st_file_attributes", 0)
        FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
        return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT) and os.path.isdir(path)
    except Exception:
        return False

def _win_long(path: str) -> str:
    """
    Windows 긴 경로(>260자) 지원 프리픽스
    UNC: \\server\\share -> \\\\?\\UNC\\server\\share
    """
    if path.startswith("\\\\?\\") or path.startswith("\\??\\"):
        return path
    if path.startswith("\\\\"):
        return "\\\\?\\UNC\\" + path.lstrip("\\")
    return "\\\\?\\" + path

def _remove_junction_only(path: str) -> None:
    """
    정션/심볼릭 링크만 제거.
    - 정션: os.rmdir(링크 경로)
    - 심볼릭 링크: os.unlink()
    - 일반 폴더/파일이면 예외(데이터 보호)
    """
    path = _abs(path)
    if not os.path.exists(path):
        return

    if os.path.islink(path):
        os.unlink(path)
        return

    if _is_junction(path):
        os.rmdir(path)
        return

    raise RuntimeError("정션/심볼릭 링크가 아닌 경로는 제거하지 않습니다.")

# ----------------------------------------------------
# 정션 타깃 조회 (WinAPI, 서브프로세스 미사용)
# ----------------------------------------------------
def _query_junction_target(path: str) -> Optional[str]:
    """
    FSCTL_GET_REPARSE_POINT로 정션의 SubstituteName을 읽어온다.
    """
    import ctypes
    from ctypes import wintypes

    path = _abs(path)
    if not (os.name == "nt" and os.path.exists(path) and _is_junction(path)):
        return None

    GENERIC_READ = 0x80000000
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    FILE_FLAG_BACKUP_SEMANTICS   = 0x02000000
    OPEN_EXISTING = 3

    FSCTL_GET_REPARSE_POINT = 0x000900A8
    IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003

    class REPARSE_DATA_BUFFER(ctypes.Structure):
        _fields_ = [
            ("ReparseTag", wintypes.DWORD),
            ("ReparseDataLength", wintypes.USHORT),
            ("Reserved", wintypes.USHORT),
            ("SubstituteNameOffset", wintypes.USHORT),
            ("SubstituteNameLength", wintypes.USHORT),
            ("PrintNameOffset", wintypes.USHORT),
            ("PrintNameLength", wintypes.USHORT),
            ("PathBuffer", wintypes.WCHAR * 0x3FF0),
        ]

    CreateFileW = ctypes.windll.kernel32.CreateFileW
    CreateFileW.restype = wintypes.HANDLE
    CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
        wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE
    ]

    DeviceIoControl = ctypes.windll.kernel32.DeviceIoControl
    DeviceIoControl.restype = wintypes.BOOL
    DeviceIoControl.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
        wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID
    ]

    CloseHandle = ctypes.windll.kernel32.CloseHandle

    h = CreateFileW(
        _win_long(path),
        GENERIC_READ,
        0,
        None,
        OPEN_EXISTING,
        FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS,
        None
    )
    if h == wintypes.HANDLE(-1).value:
        return None

    try:
        out = REPARSE_DATA_BUFFER()
        bytes_ret = wintypes.DWORD(0)
        ok = DeviceIoControl(
            h, FSCTL_GET_REPARSE_POINT,
            None, 0,
            ctypes.byref(out), ctypes.sizeof(out),
            ctypes.byref(bytes_ret), None
        )
        if not ok or out.ReparseTag != IO_REPARSE_TAG_MOUNT_POINT:
            return None

        start = out.SubstituteNameOffset // 2
        length = out.SubstituteNameLength // 2
        target = out.PathBuffer[start:start+length]

        if target.startswith("\\??\\"):
            target = target[4:]
        elif target.startswith("\\\\??\\"):
            target = target[5:]

        return os.path.normpath(target)
    finally:
        CloseHandle(h)

# ----------------------------------------------------
# 외부 호출 API
# ----------------------------------------------------
def create_junction(src: str, dst: str) -> Tuple[bool, str]:
    """
    정션 생성: 안정성을 위해 서브프로세스 mklink /J만 사용 (UI 프리즈는 상위에서 QThread로 해결)
    """
    src = _abs(src)
    dst = _abs(dst)

    if os.name != "nt":
        return False, "정션은 Windows에서만 지원됩니다."
    if not os.path.isdir(src):
        return False, f"원본 경로가 디렉터리가 아닙니다: {src}"

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    # dst가 존재하면 정리
    if os.path.exists(dst):
        try:
            if os.path.islink(dst) or _is_junction(dst):
                _remove_junction_only(dst)
            else:
                return False, f"대상 경로가 이미 존재하며 정션이 아닙니다: {dst}"
        except Exception as e:
            return False, str(e)

    try:
        p_dst, p_src = _win_long(dst), _win_long(src)
        proc = subprocess.run(
            ["cmd", "/c", "mklink", "/J", p_dst, p_src],
            capture_output=True, text=True, shell=False
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            return False, f"mklink /J 실패 (코드 {proc.returncode}) {err}"
        return True, "OK"
    except Exception as e:
        return False, f"정션 생성 예외: {e}"

def remove_junction(dst: str) -> Tuple[bool, str]:
    """
    정션 제거 (링크만 제거)
    """
    dst = _abs(dst)

    if os.name != "nt":
        return False, "정션은 Windows에서만 지원됩니다."
    if not os.path.exists(dst):
        return True, "OK (이미 제거됨)"

    try:
        _remove_junction_only(dst)
        return True, "OK"
    except Exception as e:
        return False, f"정션 제거 실패: {e}"

def get_junction_target(path: str) -> Optional[str]:
    """
    정션의 실제 연결 대상 경로 반환. 실패/비정션이면 None.
    """
    try:
        return _query_junction_target(path)
    except Exception:
        logger.exception("get_junction_target exception: path=%s", path)
        return None
