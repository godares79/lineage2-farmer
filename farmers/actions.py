# Common functions that are used across multiple farming algorithms.
import random
import time

import inpututil


def loot(block=False):
  print('Looting...')

  # The loot macro is expected to be present at F6.
  inpututil.press_and_release_key(inpututil.F6)

  if block:
    time.sleep(random.uniform(3.0, 5.0))
