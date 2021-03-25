from enum import Enum


class FarmingAlgorithm(Enum):
  SINGLE_TARGET = 'SINGLE_TARGET'
  HYBRID_SINGLE_TARGET = 'HYBRID_SINGLE_TARGET'
  MULTI_TARGET = 'MULTI_TARGET'

  def __str__(self):
    return self.value