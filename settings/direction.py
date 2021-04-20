from enum import Enum


class Direction(Enum):
  N = 'N'
  S = 'S'
  W = 'W'
  E = 'E'

  def __str__(self):
    return self.value
