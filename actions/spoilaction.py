# Spoil implementation class
# Should spin off a thread to do the initial spoil. If the spoil fails, should keep the thread running and try
# one more time.
import random
import time
from threading import Thread

import inpututil
import soundutil
from screenmanagement import ScreenObject


def spoil(screen_monitor_thread, stop_event):
  spoil_thread = SpoilThread(screen_monitor_thread, stop_event)
  spoil_thread.daemon = True
  spoil_thread.start()


def sweep():
  # Use the sweeper skill. Always succeeds if there is anything to be swept.
  inpututil.press_and_release_key(inpututil.F5)
  time.sleep(random.uniform(0.5, 1.0))


class SpoilThread(Thread):

  def __init__(self, screen_monitor_thread, stop_event):
    Thread.__init__(self)
    self.screen_monitor_thread = screen_monitor_thread
    self.stop_event = stop_event

  def run(self):
    # Use the spoil skill. Verify that spoiling was successful. Keep trying while mob is still alive.
    # TODO: There might be a race condition I can exploit to sweep multiple times.... Need to press the button very
    # very fast in succession and can sweep twice. Does lag play a role? I'm not sure. But something to try eventually.

    # TODO: With L2OFF (hellscape) need to check for a target out of range alert and re-do spoil if it happens.
    while True:
      if self.stop_event.is_set():
        return

      inpututil.press_and_release_key(inpututil.F3)

      # Wait for the spoil to apply. It may take some time to reach the target and start spoiling.
      while not self.screen_monitor_thread.get_screen_object().is_spoil_applied():
        time.sleep(0.3)

      spoil_status = self.screen_monitor_thread.get_screen_object().get_spoil_status()
      index = 0
      while not spoil_status:
        index += 1
        if index > 10:
          break

        time.sleep(0.5)
        spoil_status = self.screen_monitor_thread.get_screen_object().get_spoil_status()

      if spoil_status:
        print('Spoil succeeded.')
        return

      if not spoil_status:
        print('Spoil failed. Retrying...')
        time.sleep(6)
        if self.screen_monitor_thread.get_screen_object().get_target_health() == 0:
          return
