from enum import Enum


class ValidTargets(Enum):
  MONSTER_EYE_SEARCHER = ('MONSTER_EYE_SEARCHER', 60)
  SHIELD_SKELETON = ('SHIELD_SKELETON', 50)
  GRIZZLY = ('GRIZZLY', 40)

  def __str__(self):
    return self.value[0]

  def spawn_timeout_seconds(self):
    return self.value[1]
