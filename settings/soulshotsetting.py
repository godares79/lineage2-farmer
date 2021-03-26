from enum import Enum


class SoulshotSetting(Enum):
  ALWAYS = 'ALWAYS'
  NEVER = 'NEVER'
  ONCE = 'ONCE'

  def __str__(self):
    return self.value