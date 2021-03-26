from enum import Enum
from collections import namedtuple

TargetProperties = namedtuple(
  'TargetProperties',
  ['spawn_timeout', 'ocr_text', 'name_bitmap'])


def _properties_map():
  return {
    IntendedTarget.SPORE_FUNGUS: TargetProperties(
      spawn_timeout=30, ocr_text='fungus', name_bitmap='spore_fungus.bmp'),
    IntendedTarget.GRIZZLY: TargetProperties(
      spawn_timeout=45, ocr_text='grizzly', name_bitmap='grizzly.bmp'),
    IntendedTarget.SHIELD_SKELETON: TargetProperties(
      spawn_timeout=60, ocr_text='shield', name_bitmap='shield_skeleton.bmp'),
    IntendedTarget.MONSTER_EYE_SEARCHER: TargetProperties(
      spawn_timeout=75, ocr_text='searcher', name_bitmap='monster_eye_searcher.bmp')
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

  def ocr_text(self):
    return _properties_map()[self].ocr_text

  def name_bitmap(self):
    return _properties_map()[self].name_bitmap
