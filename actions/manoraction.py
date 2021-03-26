# Manor System Management class
import random
import time

import inpututil
import soundutil


def plant_seed(screen_capture_thread, stop_event):
  # Plant a seed. Seeding should always be successful. Do not return until seeding starts.
  # Play a sound alert if seeding doesn't start for some time.
  inpututil.press_and_release_key(inpututil.F2)

  itercount = 0
  while True:
    if stop_event.is_set():
      return

    if itercount > 50 and itercount % 5 == 0:
      soundutil.play_alert()

    if screen_capture_thread.get_screen_object().has_started_sowing():
      print('Planted seed.')
      return

    itercount += 1
    time.sleep(0.3)


def harvest_corpse(screen_capture_thread):
  # Use the harvester. Return true if harvesting was successful.
  inpututil.press_and_release_key(inpututil.F4)
  time.sleep(random.uniform(1, 1.5))
  return screen_capture_thread.get_screen_object().was_harvest_successful()
