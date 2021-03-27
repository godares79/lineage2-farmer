# Common functions that are used across multiple farming algorithms.
import random
import time

import inpututil
from actions import manoraction, spoilaction
from settings.soulshotsetting import SoulshotSetting


def wait_for_manually_selected_target(screen_monitor_thread, stop_event, target):
  # Waits up to 10 seconds for a target to be manually selected.
  # Returns True if a target is selected. Returns false if not.
  spawn_timeout_counter = 0
  sleep_increment_seconds = 0.25
  spawn_timeout_limit = 40  # 0.25s * 40 = 10 seconds
  target_selected = False

  while not target_selected and spawn_timeout_counter < spawn_timeout_limit:
    if stop_event.is_set(): return False

    if screen_monitor_thread.get_screen_object().has_selected_target(target):
      mob_health_percent = screen_monitor_thread.get_screen_object().get_target_health()
      if mob_health_percent and mob_health_percent > 0:
        return True

    spawn_timeout_counter += 1
    time.sleep(sleep_increment_seconds)

  return False


def perform_starting_actions(screen_monitor_thread,
                             stop_event,
                             should_stand=False,
                             should_seed=False,
                             should_spoil=False):
  if stop_event.is_set(): return
  if should_stand:
    stand()

  if stop_event.is_set(): return
  if should_seed:
    seed(screen_monitor_thread, stop_event)

  if stop_event.is_set(): return
  if should_spoil:
    spoil(screen_monitor_thread, stop_event)


def seed(screen_monitor_thread, stop_event):
  manoraction.plant_seed(screen_monitor_thread, stop_event)


def spoil(screen_monitor_thread, stop_event):
  spoilaction.spoil(screen_monitor_thread, stop_event)


def attack_mob(screen_monitor_thread, stop_event, soulshot_setting):
  mob_health_percent = 100
  used_soulshot = False

  while mob_health_percent > 0:
    if stop_event.is_set(): return
    mob_health_percent = screen_monitor_thread.get_screen_object().get_target_health()

    if soulshot_setting == SoulshotSetting.ONCE:
      if mob_health_percent < 70 and not used_soulshot:
        used_soulshot = True
        inpututil.press_and_release_key(inpututil.SOULSHOT)

    if mob_health_percent == 0:
      break
    else:
      # Check every 1 second for mob health.
      time.sleep(1)

  # Just give it about 0.5 second for things to clear out a bit.
  time.sleep(random.uniform(0.6, 0.9))


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
  inpututil.press_and_release_key(inpututil.LOOT_MACRO)

  if block:
    time.sleep(random.uniform(3.0, 5.0))


def sit():
  inpututil.press_and_release_key(inpututil.SIT_MACRO)
  time.sleep(random.uniform(1.0, 1.5))


def stand():
  inpututil.press_and_release_key(inpututil.STAND_MACRO)
  time.sleep(random.uniform(1.0, 1.5))
