# utils/blur_helper.py
import ctypes
from ctypes import wintypes

# Windows API 구조체 정의
class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_int)
    ]

class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t)
    ]

# 상수 값
WCA_ACCENT_POLICY = 19
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4    # Acrylic Blur
ACCENT_ENABLE_BLURBEHIND = 3          # Normal Blur

def apply_acrylic_blur(hwnd, acrylic=True):
    # ✅ PyQt → Win32 HWND 변환
    hwnd = int(hwnd)
    accent = ACCENT_POLICY()
    accent.AccentState = ACCENT_ENABLE_ACRYLICBLURBEHIND if acrylic else ACCENT_ENABLE_BLURBEHIND
    accent.GradientColor = 0x60282828  # AARRGGBB (투명도 + 색상)

    data = WINDOWCOMPOSITIONATTRIBDATA()
    data.Attribute = WCA_ACCENT_POLICY
    data.SizeOfData = ctypes.sizeof(accent)
    data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)

    set_attr = ctypes.windll.user32.SetWindowCompositionAttribute
    set_attr(ctypes.c_void_p(hwnd), ctypes.byref(data))
