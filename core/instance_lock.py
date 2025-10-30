# core/instance_lock.py
# Windows 전역 Named Mutex 기반 싱글 인스턴스 락
# 기존 API 호환:
#   - is_another_instance_running() -> bool
#   - write_lock() -> None
#   - remove_lock() -> None
#   - install_atexit() -> None

import atexit
import os

# 비-Windows 환경(개발용)에서는 간단한 파일락으로 폴백
_IS_WIN = (os.name == "nt")

# -----------------------------
# Windows: Named Mutex 구현
# -----------------------------
if _IS_WIN:
    import ctypes
    from ctypes import wintypes

    # 앱 고유 뮤텍스 이름 (Global\ 시도 → 권한 문제면 Local\ 폴백)
    _APP_ID = "WWMM.ModManager.SingleInstance"
    _MUTEX_NAME_GLOBAL = f"Global\\{_APP_ID}"
    _MUTEX_NAME_LOCAL  = f"Local\\{_APP_ID}"

    # WinAPI 바인딩
    CreateMutexW   = ctypes.windll.kernel32.CreateMutexW
    CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    CreateMutexW.restype  = wintypes.HANDLE

    OpenMutexW     = ctypes.windll.kernel32.OpenMutexW
    OpenMutexW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    OpenMutexW.restype  = wintypes.HANDLE

    ReleaseMutex   = ctypes.windll.kernel32.ReleaseMutex
    ReleaseMutex.argtypes = [wintypes.HANDLE]
    ReleaseMutex.restype  = wintypes.BOOL

    CloseHandle    = ctypes.windll.kernel32.CloseHandle
    CloseHandle.argtypes = [wintypes.HANDLE]
    CloseHandle.restype  = wintypes.BOOL

    GetLastError   = ctypes.windll.kernel32.GetLastError

    # 권한: 존재 여부 확인용
    SYNCHRONIZE = 0x00100000
    ERROR_ALREADY_EXISTS = 183
    ERROR_ACCESS_DENIED  = 5

    _mutex_handle = None
    _mutex_name_in_use = None  # "Global\..." 또는 "Local\..."

    def _close_handle_safe(h):
        if h:
            try:
                CloseHandle(h)
            except Exception:
                pass

    def _try_open(name: str):
        h = OpenMutexW(SYNCHRONIZE, False, name)
        if h:
            _close_handle_safe(h)
            return True
        return False

    def is_another_instance_running() -> bool:
        """
        기존 인스턴스가 있으면 True.
        단순 존재 확인(OpenMutex)만 수행.
        """
        # Global 먼저 확인, 실패시 Local 확인
        if _try_open(_MUTEX_NAME_GLOBAL):
            return True
        if _try_open(_MUTEX_NAME_LOCAL):
            return True
        return False

    def write_lock() -> None:
        """
        현재 프로세스가 전역 뮤텍스를 획득한다.
        이미 실행 중이면 내부적으로 즉시 핸들을 닫고 반환(상위에서 is_another_instance_running으로 걸러짐).
        """
        global _mutex_handle, _mutex_name_in_use

        if _mutex_handle:
            return  # 이미 보유

        # 1) Global 시도
        h = CreateMutexW(None, True, _MUTEX_NAME_GLOBAL)
        if h:
            last_err = GetLastError()
            if last_err == ERROR_ALREADY_EXISTS:
                # 이미 다른 인스턴스가 보유 → 닫고 종료
                _close_handle_safe(h)
                _mutex_handle = None
                _mutex_name_in_use = None
                return
            # 성공
            _mutex_handle = h
            _mutex_name_in_use = _MUTEX_NAME_GLOBAL
            return

        # 2) 권한 문제 등으로 실패하면 Local 시도
        h = CreateMutexW(None, True, _MUTEX_NAME_LOCAL)
        if h:
            last_err = GetLastError()
            if last_err == ERROR_ALREADY_EXISTS:
                _close_handle_safe(h)
                _mutex_handle = None
                _mutex_name_in_use = None
                return
            _mutex_handle = h
            _mutex_name_in_use = _MUTEX_NAME_LOCAL
            return

        # 둘 다 실패시 그냥 보유 못한 상태로 둔다(상위에서 is_another...로 이미 거름)

    def remove_lock() -> None:
        """획득한 뮤텍스 해제 및 핸들 정리."""
        global _mutex_handle, _mutex_name_in_use
        if _mutex_handle:
            try:
                # ReleaseMutex는 현재 소유자일 때만 유효
                ReleaseMutex(_mutex_handle)
            except Exception:
                pass
            _close_handle_safe(_mutex_handle)
            _mutex_handle = None
            _mutex_name_in_use = None

    def install_atexit() -> None:
        atexit.register(remove_lock)

# -----------------------------
# Non-Windows: 간단 파일락 폴백
# -----------------------------
else:
    # psutil 의존성 제거. 유닉스 계열에선 os.kill(pid, 0)로 생존 확인.
    import errno

    LOCK_FILE = os.path.join(os.path.expanduser("~"), ".wwmm.lock")

    def _read_pid(path: str) -> int:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except Exception:
            return -1

    def _pid_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            # 시그널 0: 존재/권한만 체크
            os.kill(pid, 0)
        except OSError as e:
            return not (e.errno == errno.ESRCH)  # No such process면 False
        return True

    def is_another_instance_running() -> bool:
        if not os.path.exists(LOCK_FILE):
            return False
        old = _read_pid(LOCK_FILE)
        if _pid_alive(old):
            return True
        try:
            os.remove(LOCK_FILE)
        except Exception:
            pass
        return False

    def write_lock() -> None:
        os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
        with open(LOCK_FILE, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))

    def remove_lock() -> None:
        try:
            if os.path.exists(LOCK_FILE):
                os.remove(LOCK_FILE)
        except Exception:
            pass

    def install_atexit() -> None:
        atexit.register(remove_lock)
