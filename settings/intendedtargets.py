from enum import Enum
from collections import namedtuple

# The selection offset is an (x, y) pixel tuple that is the offset from the template location to where the click
# should be done to select the monster. The template match location is at the top left of the match location, so the
# offset should start from there.
TargetProperties = namedtuple(
  'TargetProperties',
  ['spawn_timeout', 'ocr_text', 'name_bitmap', 'full_name', 'selection_offset'])


def _properties_map():
  return {
    IntendedTarget.SPORE_FUNGUS: TargetProperties(
      spawn_timeout=30, ocr_text='fungus', name_bitmap='spore_fungus.bmp', full_name='Spore Fungus',
      selection_offset=(37, 31)),
    IntendedTarget.GRIZZLY: TargetProperties(
      spawn_timeout=45, ocr_text='grizzly', name_bitmap='grizzly.bmp', full_name='Grizzly',
      selection_offset=(0, 10)),
    IntendedTarget.SHIELD_SKELETON: TargetProperties(
      spawn_timeout=60, ocr_text='shield', name_bitmap='shield_skeleton.bmp', full_name='Shield Skeleton',
      selection_offset=(0, 10)),
    IntendedTarget.MONSTER_EYE_SEARCHER: TargetProperties(
      spawn_timeout=75, ocr_text='searcher', name_bitmap='monster_eye_searcher.bmp', full_name='Monster Eye Searcher',
      selection_offset=(0, 10))
  }


class IntendedTarget(Enum):
  SPORE_FUNGUS = 'SPORE_FUNGUS'
  GRIZZLY = 'GRIZZLY'
  SHIELD_SKELETON = 'SHIELD_SKELETON'
  MONSTER_EYE_SEARCHER = 'MONSTER_EYE_SEARCHER'
  OL_MAHUM_RAIDER = 'OL_MAHUM_RAIDER'
  TUREK_ORC_FOOTMAN = 'TUREK_ORC_FOOTMAN'
  TUREK_ORC_SHAMAN = 'TUREK_ORC_SHAMAN'
  ANT_WARRIOR_CAPTAIN = 'ANT_WARRIOR_CAPTAIN'

  def __str__(self):
    return self.value

  def spawn_timeout(self):
    return _properties_map()[self].spawn_timeout

  def ocr_text(self):
    return _properties_map()[self].ocr_text

  def name_bitmap(self):
    return _properties_map()[self].name_bitmap

  def full_name(self):
    return _properties_map()[self].full_name

  def selection_offset(self):
    return _properties_map()[self].selection_offset
