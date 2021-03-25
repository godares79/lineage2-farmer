import ctypes
import random
import time

PUL = ctypes.POINTER(ctypes.c_ulong)

# ScanCode constants that I care about.
F1 = 0x3B
F2 = 0x3C
F3 = 0x3D
F4 = 0x3E
F5 = 0x3F
F6 = 0x40
F7 = 0x41
F8 = 0x42
F9 = 0x43
F10 = 0x44
F11 = 0x57
F12 = 0x58
CTRL = 0x1D
SHIFT = 0x2A
ALT = 0x38


class KeyBdInput(ctypes.Structure):
  # Keyboard input class. Use ScanCodes that are compatible with DirectX.
   _fields_ = [("wVk", ctypes.c_ushort),
               ("wScan", ctypes.c_ushort),
               ("dwFlags", ctypes.c_ulong),
               ("time", ctypes.c_ulong),
               ("dwExtraInfo", PUL)]


class HardwareInput(ctypes.Structure):
  _fields_ = [("uMsg", ctypes.c_ulong),
              ("wParamL", ctypes.c_short),
              ("wParamH", ctypes.c_ushort)]


class MouseInput(ctypes.Structure):
  _fields_ = [("dx", ctypes.c_long),
              ("dy", ctypes.c_long),
              ("mouseData", ctypes.c_ulong),
              ("dwFlags", ctypes.c_ulong),
              ("time", ctypes.c_ulong),
              ("dwExtraInfo", PUL)]


class Input_I(ctypes.Union):
  _fields_ = [("ki", KeyBdInput),
              ("mi", MouseInput),
              ("hi", HardwareInput)]


class Input(ctypes.Structure):
  _fields_ = [("type", ctypes.c_ulong),
              ("ii", Input_I)]


def press_key(key):
  extra = ctypes.c_ulong(0)
  ii_ = Input_I()

  flags = 0x0008

  ii_.ki = KeyBdInput(0, key, flags, 0, ctypes.pointer(extra))
  x = Input(ctypes.c_ulong(1), ii_)
  ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def release_key(key):
  extra = ctypes.c_ulong(0)
  ii_ = Input_I()

  flags = 0x0008 | 0x0002

  ii_.ki = KeyBdInput(0, key, flags, 0, ctypes.pointer(extra))
  x = Input(ctypes.c_ulong(1), ii_)
  ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))


def press_and_release_key(key):
  press_key(key)
  time.sleep(random.uniform(0.1, 0.15))
  release_key(key)
