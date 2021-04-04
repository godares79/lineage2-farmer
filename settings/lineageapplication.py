from enum import Enum


class LineageApplication(Enum):
  REBORN = 'REBORN'
  HELLFORGE = 'HELLFORGE'

  def __str__(self):
    return self.value