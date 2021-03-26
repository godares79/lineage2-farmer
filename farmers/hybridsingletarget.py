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

      if self.stop_event.is_set():
        return

      if self.args.manor:
        manoraction.plant_seed(self.screen_capture_thread, self.stop_event)

      if self.stop_event.is_set():
        return

      if self.args.spoil:
        spoilaction.spoil(self.screen_capture_thread, self.stop_event)

      if self.stop_event.is_set():
        return

      mob_health_percent = 100
      index = 0
      used_soulshot = False
      while mob_health_percent > 0:
        if self.stop_event.is_set():
          return

        mob_health_percent = self.screen_capture_thread.get_screen_object().get_target_health()

        # Use a soulshot one time after we have already started attacking the mob a bit.
        # That way our pet is not targetted.
        if self.args.soulshot != SoulshotSetting.NEVER:
          if mob_health_percent < 80 and not used_soulshot:
            # Click on soulshot.
            used_soulshot = True
            inpututil.press_and_release_key(inpututil.F10)

        if mob_health_percent == 0:
          print(f'Mob Health:\033[91m {"0%": >3} \033[0m', end='\r')
          break
        else:
          print(f'Mob Health: {mob_health_percent: >3}%', end='\r')
          # Check every 1 second for mob health.
          time.sleep(1)

        index += 1

      # Just give it about 0.5 second for things to clear out a bit.
      time.sleep(random.uniform(0.6, 0.9))

      if self.stop_event.is_set():
        return

      if self.args.manor:
        success = manoraction.harvest_corpse(self.screen_capture_thread)
        print('The harvest was a success? {0}'.format(success))

      if self.args.spoil:
        spoilaction.sweep()

      print('Looting...')
      # I'm using a macro ingame that will loot several times in a row.
      inpututil.press_and_release_key(inpututil.F6)

  def stop(self):
    self.stop_event.set()
