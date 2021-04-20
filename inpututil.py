import ctypes
import random
import time

PUL = ctypes.POINTER(ctypes.c_ulong)

# ScanCode constants that I care about.
# NOTE: The scancodes should be the QWERTY key as they may to a DVORAK layout (e.g., S == ; scancode).
NEXT_TARGET = 0x3B       # F1
TARGET_MACRO = 0x3C      # F2
ATTACK = 0x3D            # F3
SEED = 0x3E              # F4
SPOIL_MACRO = 0x3F       # F5
HARVEST = 0x40           # F6
SWEEP = 0x41             # F7
LOOT_MACRO = 0x42        # F8
HEALING_POTION = 0x43    # F9
SOULSHOT = 0x44          # F10
SIT_MACRO = 0x57         # F11
STAND_MACRO = 0x58       # F12
CTRL = 0x1D
SHIFT = 0x2A
ALT = 0x38
CLEAR_TARGET = 0x01      # ESCAPE
MOVE_BACK = 0x27         # S (0x1F), ; (0x27)
FLIP_CAMERA = 0xCF + 1024  # END


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


def press_and_release_key(key, lower_bound_time=0.1, upper_bound_time=0.15):
  press_key(key)
  time.sleep(random.uniform(lower_bound_time, upper_bound_time))
  release_key(key)
