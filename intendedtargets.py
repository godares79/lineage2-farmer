from enum import Enum
from collections import namedtuple


TargetProperties = namedtuple('TargetProperties', ['spawn_timeout'])


def _properties_map():
  return {
    IntendedTarget.SPORE_FUNGUS: TargetProperties(spawn_timeout=30),
    IntendedTarget.GRIZZLY: TargetProperties(spawn_timeout=45),
    IntendedTarget.SHIELD_SKELETON: TargetProperties(spawn_timeout=60),
    IntendedTarget.MONSTER_EYE_SEARCHER: TargetProperties(spawn_timeout=75)
  }


class IntendedTarget(Enum):
  SPORE_FUNGUS = 'SPORE_FUNGUS'
  GRIZZLY = 'GRIZZLY'
  SHIELD_SKELETON = 'SHIELD_SKELETON'
  MONSTER_EYE_SEARCHER = 'MONSTER_EYE_SEARCHER'

  def __str__(self):
    return self.value

  def spawn_timeout(self):
    return _properties_map()[self].spawn_timeout
