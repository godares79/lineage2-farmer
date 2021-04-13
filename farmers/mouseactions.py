# Actions that are performed primarily using the mouse.
import collections
import random
import time
from math import sqrt

import numpy as np
import pyautogui as pyautogui
import pyclick as pyclick
from scipy import interpolate

import inpututil

DistanceBucket = collections.namedtuple(
  'DistanceBucket',
  ['distance_upper_bound', 'minimum_duration', 'offset_boundary'])
DISTANCE_TO_TIME_BUCKETS = (
  DistanceBucket(distance_upper_bound=250, minimum_duration=0.30, offset_boundary=15),
  DistanceBucket(distance_upper_bound=500, minimum_duration=0.32, offset_boundary=20),
  DistanceBucket(distance_upper_bound=750, minimum_duration=0.34, offset_boundary=25),
  DistanceBucket(distance_upper_bound=1000, minimum_duration=0.40, offset_boundary=30),
  DistanceBucket(distance_upper_bound=2000, minimum_duration=0.40, offset_boundary=35)
)


def select_target_with_mouse(screen_monitor, intended_target_enum):
  # Returns True if a valid target is selected. False if not.
  # TODO: This only works for fullscreen currently. Need to get windowed mode working eventually.
  for next_location in next(_cycle_to_next_valid_target(screen_monitor, intended_target_enum)):
    # Move the mouse cursor and click on the next target. If it is valid (present, not being attacked, etc.) then return
    # True.

    # TODO: Only use a randomized location if using L2Reborn as we can't zoom out as far.
    # randomized_next_location = (next_location[0] + random.randint(-10, 10), next_location[1] + random.randint(-10, 10))
    randomized_next_location = (next_location[0], next_location[1])
    frompoint = pyautogui.position()
    humanclicker = pyclick.HumanClicker()
    pyautogui.PAUSE = 0

    distance = _calculate_distance_between_two_points(frompoint, randomized_next_location)

    # Do not bother to click on a target that is too close as it is probably the dead mob.
    if _calculate_distance_from_center(next_location) < 100:
      continue

    for distance_bucket in DISTANCE_TO_TIME_BUCKETS:
      if distance < distance_bucket.distance_upper_bound:
        humancurve = pyclick.HumanCurve(frompoint, randomized_next_location,
                                        offsetBoundaryX=distance_bucket.offset_boundary, offsetBoundaryY=distance_bucket.offset_boundary, targetPoints=25)
        humanclicker.move(randomized_next_location, duration=random.uniform(distance_bucket.minimum_duration, distance_bucket.minimum_duration+0.05), humanCurve=humancurve)
        break
    pyautogui.mouseDown()
    time.sleep(random.uniform(0.1, 0.15))
    pyautogui.mouseUp()

    time.sleep(0.4)

    selected_and_valid = (screen_monitor.get_screen_object().has_selected_target(intended_target_enum.ocr_text())
                          and screen_monitor.get_screen_object().get_target_health() >= 100)
    if not selected_and_valid:
      # Stop and then restart the entire loop with recursion.
      inpututil.press_and_release_key(inpututil.MOVE_BACK, lower_bound_time=0.30, upper_bound_time=0.5)
      time.sleep(0.4)
      return select_target_with_mouse(screen_monitor, intended_target_enum)
    else:
      return True

  return False


def _cycle_to_next_valid_target(screen_monitor, intended_target_enum):
  match_locations = screen_monitor.get_on_demand_screenshot(0, 0, 1910, 850).locate_target_screen_coordinates(
    intended_target_enum.name_bitmap(), intended_target_enum.selection_offset())
  if not match_locations: yield []

  # Cycle outwards from the center of the screen to select the next target.
  match_locations.sort(key=_calculate_distance_from_center)
  yield match_locations


def _calculate_distance_from_center(point):
  center_point = (960, 540)  # Assuming 1920x1080 screen.
  return _calculate_distance_between_two_points(point, center_point)


def _calculate_distance_between_two_points(fromPoint, toPoint):
  return sqrt(((toPoint[0]-fromPoint[0])**2)+((toPoint[1]-fromPoint[1])**2))
