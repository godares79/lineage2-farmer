# Spoil implementation class
# Should spin off a thread to do the initial spoil. If the spoil fails, should keep the thread running and try
# one more time.
import random
import time
from threading import Thread

import inpututil


def spoil(screen_monitor_thread, stop_event, monitor_if_attacked=False, attack_event=None):
  spoil_thread = SpoilThread(screen_monitor_thread, stop_event, monitor_if_attacked, attack_event)
  spoil_thread.daemon = True
  spoil_thread.start()


def sweep():
  # Use the sweeper skill. Always succeeds if there is anything to be swept.
  inpututil.press_and_release_key(inpututil.SWEEP)
  time.sleep(random.uniform(0.5, 1.0))


class SpoilThread(Thread):

  def __init__(self, screen_monitor_thread, stop_event, monitor_if_attacked, attack_event):
    Thread.__init__(self)
    self.screen_monitor_thread = screen_monitor_thread
    self.stop_event = stop_event
    self.monitor_if_attacked = monitor_if_attacked
    self.attack_event = attack_event

  def run(self):
    # TODO: With L2OFF (hellscape) need to check for a target out of range alert and re-do spoil if it happens.
    while True:
      if self.stop_event.is_set():
        return

      inpututil.press_and_release_key(inpututil.SPOIL_MACRO)

      # Wait for the spoil to apply. It may take some time to reach the target and start spoiling.
      while not self.screen_monitor_thread.get_screen_object().is_spoil_applied():
        if self.monitor_if_attacked:
          if self.screen_monitor_thread.get_screen_object().get_target_health() < 100:
            # That target has been attacked. Return if that is the case.
            self.attack_event.set()
            return
        time.sleep(0.3)

      spoil_status = self.screen_monitor_thread.get_screen_object().get_spoil_status()
      index = 0
      while not spoil_status:
        index += 1
        if index > 10:
          break

        time.sleep(0.3)
        spoil_status = self.screen_monitor_thread.get_screen_object().get_spoil_status()

      if spoil_status:
        return

      if not spoil_status:
        time.sleep(6)
        if self.screen_monitor_thread.get_screen_object().get_target_health() == 0:
          return
