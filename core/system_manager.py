# core/system_manager.py

import ctypes

def is_admin():
    """현재 프로세스가 관리자 권한인지 반환 (Windows 전용)"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin(exe_path, params):
    """
    exe_path: 실행할 프로그램 (python.exe 또는 .exe)
    params: 리스트 형태여야 함
    """
    if isinstance(params, list):
        params = " ".join([f'"{arg}"' for arg in params])  # 공백 포함 대비

    return ctypes.windll.shell32.ShellExecuteW(
        None, "runas", exe_path, params, None, 1
    )
