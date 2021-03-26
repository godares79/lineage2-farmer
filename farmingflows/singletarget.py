# Implementations of single target farming flow.
import threading
import random
import time
from threading import Thread

import inpututil
from actions import manoraction, spoilaction
import soundutil
from settings.soulshotsetting import SoulshotSetting


class SingleTargetFarm(Thread):

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
      itercount = 0
      while not self.screen_capture_thread.get_screen_object().has_target_spawned(self.args.target):
        if self.stop_event.is_set():
          return

        if itercount >= 45 and itercount % 5 == 0:
          # Send an audio alert if the target hasn't spawned for some time.
          print(f'\033[91m{self.args.target} has not spawned after {itercount} seconds!\033[0m')
          soundutil.play_alert()

        itercount += 1
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
        # Stand up just incase sitting.
        inpututil.press_and_release_key(inpututil.F12)
        time.sleep(random.uniform(1.0, 1.5))

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

        # Only use soulshot once when the mob health is lowish.
        if self.args.soulshot != SoulshotSetting.NEVER:
          if mob_health_percent < 70 and not used_soulshot:
            # Click on soulshot.
            inpututil.press_and_release_key(inpututil.F10)
            used_soulshot = True

        if mob_health_percent == 0:
          print(f'Mob Health:\033[91m {"0%": >3} \033[0m', end='\r')
          break
        else:
          print(f'Mob Health: {mob_health_percent: >3}%', end='\r')
          # Check every 1 second for mob health.
          time.sleep(1)

        index += 1

      # Just give it 1-2 seconds for things to clear out a bit.
      time.sleep(random.uniform(0.7, 1.5))

      if self.stop_event.is_set():
        return

      if self.args.manor:
        success = manoraction.harvest_corpse(self.screen_capture_thread)
        print('The harvest was a success? {0}'.format(success))

      if self.args.spoil:
        spoilaction.sweep()

      print('Looting...')
      # Use an ingame macro to loot and just pause for a while after before potentially sitting.
      inpututil.press_and_release_key(inpututil.F6)
      time.sleep(random.uniform(3.0, 5.0))

      if self.stop_event.is_set():
        return

      if self.args.sit:
        # Sit down.
        inpututil.press_and_release_key(inpututil.F11)
        time.sleep(random.uniform(1.0, 1.5))

      # Do not continue the loop until the current dead target has disappeared (in the event that spoiling failed).
      while self.screen_capture_thread.get_screen_object().has_selected_target(self.args.target):
        time.sleep(1)

      if self.stop_event.is_set():
        return

      # At this point, if health is low then wait until health is high again before continuing.
      # if self.resource_monitor_thread.has_low_health:
      #   while not self.resource_monitor_thread.has_high_health:
      #     time.sleep(5)

  def stop(self):
    self.stop_event.set()
