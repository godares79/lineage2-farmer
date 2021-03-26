# Single target farm but permits breaking out normal flow if a new target is manually selected.
# Otherwise, will default to the regular single target farming flow where we wait for a target to spawn.
# Very similar to singletarget and I'm sure much can be refactored into common functions.
import random
import threading
import time
from threading import Thread

import inpututil
from actions import manoraction, spoilaction
import soundutil
from farmers import actions
from settings.soulshotsetting import SoulshotSetting


class HybridSingleTargetFarm(Thread):

  def __init__(self, args, screen_capture_thread, resource_monitor_thread):
    Thread.__init__(self)
    self.stop_event = threading.Event()
    self.args = args
    self.screen_capture_thread = screen_capture_thread
    self.resource_monitor_thread = resource_monitor_thread  # Not used currently.

  def run(self):
    random.seed()

    while not self.screen_capture_thread.get_screen_object():
      # Hack. Waiting for the screen capture thread to begin capturing stuff.
      # I don't know why this has just started now...
      time.sleep(1)

    while not self.stop_event.is_set():
      spawn_timeout_counter = 0
      spawn_timeout_limit = 40  # 0.25s * 40 = 10 seconds
      target_selected = False  # By default, expect no target to be already selected.

      # Wait for spawn_timeout_limit/4 seconds to see if a target is manually selected (a target that is not dead).
      # If not selected in the limit, go into regular farm mode.
      while not target_selected and spawn_timeout_counter < spawn_timeout_limit:
        if self.stop_event.is_set():
          return

        if self.screen_capture_thread.get_screen_object().has_selected_target(self.args.target):
          mob_health_percent = self.screen_capture_thread.get_screen_object().get_target_health()
          if mob_health_percent and mob_health_percent > 0:
            target_selected = True
            break
        spawn_timeout_counter += 1
        time.sleep(0.25)

      if not target_selected:
        spawn_timeout_counter = 0
        while not self.screen_capture_thread.get_screen_object().has_target_spawned(self.args.target):
          if self.stop_event.is_set():
            return

          if spawn_timeout_counter >= 55 and spawn_timeout_counter % 5 == 0:
            # Send an audio alert if the target hasn't spawned for some time.
            print(f'\033[91m{self.args.target} has not spawned after {spawn_timeout_counter} seconds!\033[0m')
            soundutil.play_alert()

          spawn_timeout_counter += 1
          time.sleep(1)

        print(f'{self.args.target} has spawned.')

        while True:
          if self.stop_event.is_set():
            return

          # Press the F1 key to select the target.
          inpututil.press_and_release_key(inpututil.F1)
          time.sleep(random.uniform(0.8, 1.0))

          if self.screen_capture_thread.get_screen_object().has_selected_target(self.args.target):
            print(f'{self.args.target} is selected.')
            break
          else:
            print(f'\033[91mFailed to cycle to target: {self.args.target}!\033[0m')
            soundutil.play_alert()
            time.sleep(5)

      if self.args.sit:
        actions.stand()

      if self.stop_event.is_set():
        return

      if self.args.manor:
        manoraction.plant_seed(self.screen_capture_thread, self.stop_event)

      if self.stop_event.is_set():
        return

      if self.args.spoil:
        spoilaction.spoil(self.screen_capture_thread, self.stop_event)

      if self.stop_event.is_set(): return
      actions.attack_mob(self.screen_capture_thread, self.stop_event, soulshot_setting=self.args.soulshot)

      if self.stop_event.is_set(): return
      actions.perform_closing_actions(
        self.screen_capture_thread, self.stop_event,
        should_harvest=self.args.manor, should_sweep=self.args.spoil, should_loot=True, should_sit=self.args.sit)

  def should_stop(self):
    self.stop_event.set()
