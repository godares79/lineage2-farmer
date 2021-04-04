# Actions that are performed primarily using the mouse.
import random
import time
from math import sqrt

import numpy as np
import pyautogui as pyautogui
from scipy import interpolate


def select_target_with_mouse(screen_monitor, intended_target_enum):
  # Returns True if a valid target is selected. False if not.
  # TODO: This only works for fullscreen currently. Need to get windowed mode working eventually.
  for next_location in next(_cycle_to_next_valid_target(screen_monitor, intended_target_enum)):
    # Move the mouse cursor and click on the next target. If it is valid (present, not being attacked, etc.) then return
    # True.
    _move_along_bezier_curve(next_location)
    pyautogui.click()
  return False


def _move_along_bezier_curve(end_location):
  def point_dist(x1, y1, x2, y2):
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

  cp = random.randint(3, 5)  # Number of control points. Must be at least 2.
  x1, y1 = pyautogui.position()  # Starting position

  # Distribute control points between start and destination evenly.
  x = np.linspace(x1, end_location[0], num=cp, dtype='int')
  y = np.linspace(y1, end_location[1], num=cp, dtype='int')

  # Randomise inner points a bit (+-RND at most).
  RND = 10
  xr = [random.randint(-RND, RND) for k in range(cp)]
  yr = [random.randint(-RND, RND) for k in range(cp)]
  xr[0] = yr[0] = xr[-1] = yr[-1] = 0
  x += xr
  y += yr

  # Approximate using Bezier spline.
  degree = 3 if cp > 3 else cp - 1  # Degree of b-spline. 3 is recommended.
  # Must be less than number of control points.
  tck, u = interpolate.splprep([x, y], k=degree)
  # Move upto a certain number of points
  u = np.linspace(0, 1, num=2 + int(point_dist(x1, y1, end_location[0], end_location[1]) / 50.0))
  points = interpolate.splev(u, tck)

  # Move mouse.
  pyautogui.MINIMUM_DURATION = 0
  pyautogui.MINIMUM_SLEEP = 0
  pyautogui.PAUSE = 0

  duration = 0.1
  timeout = duration / len(points[0])
  point_list = zip(*(i.astype(int) for i in points))
  for point in point_list:
    pyautogui.moveTo(*point)
    time.sleep(timeout)


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
