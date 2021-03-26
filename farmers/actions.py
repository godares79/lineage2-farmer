# Common functions that are used across multiple farming algorithms.
import random
import time

import inpututil
from actions import manoraction, spoilaction


def perform_closing_actions(screen_monitor_thread,
                            stop_event,
                            should_harvest=False,
                            should_sweep=False,
                            should_loot=False,
                            should_sit=False):
  if stop_event.is_set(): return
  if should_harvest:
    harvest(screen_monitor_thread)

  if stop_event.is_set(): return
  if should_sweep:
    sweep()

  if stop_event.is_set(): return
  if should_loot:
    loot(block=should_sit)

  if stop_event.is_set(): return
  if should_sit:
    sit()


def harvest(screen_monitor_thread):
  manoraction.harvest_corpse(screen_monitor_thread)


def sweep():
  spoilaction.sweep()


def loot(block=False):
  print('Looting...')

  # The loot macro is expected to be present at F6.
  inpututil.press_and_release_key(inpututil.F6)

  if block:
    time.sleep(random.uniform(3.0, 5.0))


def sit():
  # The sit macro is expected to be present at F11.
  inpututil.press_and_release_key(inpututil.F11)
  time.sleep(random.uniform(1.0, 1.5))


def stand():
  # The stand macro is expected to be present at F12.
  inpututil.press_and_release_key(inpututil.F12)
  time.sleep(random.uniform(1.0, 1.5))
