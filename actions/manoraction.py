# Manor System Management class
import random
import time

import inpututil
import soundutil


def plant_seed(screen_capture_thread, stop_event, monitor_if_attacked=False, attack_event=None):
  # Plant a seed. Seeding should always be successful. Do not return until seeding starts.
  # Play a sound alert if seeding doesn't start for some time.
  inpututil.press_and_release_key(inpututil.SEED)

  itercount = 0
  while True:
    if stop_event.is_set():
      return

    if monitor_if_attacked:
      if screen_capture_thread.get_screen_object().get_target_health < 100:
        # The target has been attacked by someone else. Stop running to the target if so.
        attack_event.set()
        return

    if itercount > 50 and itercount % 5 == 0:
      soundutil.warn()

    if screen_capture_thread.get_screen_object().has_started_sowing():
      return

    itercount += 1
    time.sleep(0.3)


def harvest_corpse(screen_capture_thread):
  # Use the harvester. Return true if harvesting was successful.
  inpututil.press_and_release_key(inpututil.HARVEST)
  time.sleep(random.uniform(1, 1.5))
  return screen_capture_thread.get_screen_object().was_harvest_successful()
