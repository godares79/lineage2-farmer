# Actions that are performed primarily using the mouse.
import random
from math import sqrt

import pyautogui as pyautogui


def select_target_with_mouse(screen_monitor, intended_target_enum):
  # Returns True if a valid target is selected. False if not.
  # TODO: This only works for fullscreen currently. Need to get windowed mode working eventually.
  # TODO: Use a Bezier curve to make mouse movement more human like.
  for next_location in next(_cycle_to_next_valid_target(screen_monitor, intended_target_enum)):
    # Move the mouse cursor and click on the next target. If it is valid (present, not being attacked, etc.) then return
    # True.
    pyautogui.moveTo(next_location[0], next_location[1], duration=random.uniform(0.35, 0.45))
    pyautogui.click()
  return False


def _cycle_to_next_valid_target(screen_monitor, intended_target_enum):
  match_locations = screen_monitor.get_screen_object().locate_target_screen_coordinates(
    intended_target_enum.name_bitmap(), intended_target_enum.selection_offset())
  if not match_locations: yield []

  # Cycle outwards from the center of the screen to select the next target.
  match_locations.sort(key=_calculate_distance_from_center)
  yield match_locations


def _calculate_distance_from_center(point):
  center_point = (960, 540)  # Assuming 1920x1080 screen.
  return sqrt(((center_point[0]-point[0])**2)+((center_point[1]-point[1])**2))
