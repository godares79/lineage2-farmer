from enum import Enum


class LineageApplication(Enum):
  REBORN = 'REBORN'
  HELLSCAPE = 'HELLSCAPE'

  def __str__(self):
    return self.value