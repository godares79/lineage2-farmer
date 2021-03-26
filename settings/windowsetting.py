from enum import Enum


class WindowSetting(Enum):
  FULLSCREEN = 'FULLSCREEN'
  WINDOWED = 'WINDOWED'

  def __str__(self):
    return self.value