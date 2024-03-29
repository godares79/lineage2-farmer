# Common functions that are used across multiple farming algorithms.
import random
import threading
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
                             should_spoil=False,
                             monitor_if_attacked=False,
                             target_under_attack_event=None):
  if stop_event.is_set(): return
  if should_stand:
    stand()

  if stop_event.is_set(): return
  if should_seed:
    seed(screen_monitor_thread, stop_event, monitor_if_attacked=monitor_if_attacked,
         target_under_attack_event=target_under_attack_event)

  if target_under_attack_event.is_set(): return
  if stop_event.is_set(): return
  if should_spoil:
    # Only monitor for other players attacking if we are not seeding. If seeding then do not monitor as it could lead
    # to false positives.
    spoil(screen_monitor_thread, stop_event, monitor_if_attacked=monitor_if_attacked and not should_seed,
          target_under_attack_event=target_under_attack_event)

  if not should_seed and not should_spoil:
    # If we aren't either seeding or spoiling, then explicitly press the attack key to ensure we start attacking.
    inpututil.press_and_release_key(inpututil.ATTACK)


def seed(screen_monitor_thread, stop_event, monitor_if_attacked, target_under_attack_event):
  manoraction.plant_seed(screen_monitor_thread, stop_event,
                         monitor_if_attacked=monitor_if_attacked, attack_event=target_under_attack_event)


def spoil(screen_monitor_thread, stop_event, monitor_if_attacked, target_under_attack_event):
  spoilaction.spoil(screen_monitor_thread, stop_event,
                    monitor_if_attacked=monitor_if_attacked, attack_event=target_under_attack_event)


def attack_mob(screen_monitor_thread, stop_event, soulshot_setting):
  mob_health_percent = 100
  used_soulshot = False

  while mob_health_percent > 0:
    if stop_event.is_set(): return
    mob_health_percent = screen_monitor_thread.get_screen_object().get_target_health()
    if not mob_health_percent or mob_health_percent == 0:
      # Break out of the loop if for some reason the mob health percent is None.
      break

    if soulshot_setting == SoulshotSetting.ONCE:
      if mob_health_percent < 70 and not used_soulshot:
        used_soulshot = True
        inpututil.press_and_release_key(inpututil.SOULSHOT)

    # Check every 1 second for mob health.
    time.sleep(1)


def perform_closing_actions(screen_monitor_thread,
                            stop_event,
                            should_harvest=False,
                            should_sweep=False,
                            should_loot=False,
                            should_sit=False):
  time.sleep(random.uniform(0.2, 0.4))  # TODO: Reborn only.
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
  time.sleep(random.uniform(1.0, 1.5))
  inpututil.press_and_release_key(inpututil.LOOT_MACRO, lower_bound_time=0.4, upper_bound_time=0.7)


def _loot_spam(iterations):
  for i in range(1, iterations):
    inpututil.press_and_release_key(inpututil.LOOT_MACRO)
    time.sleep(random.uniform(0.25, 0.3))


def sit():
  inpututil.press_and_release_key(inpututil.SIT_MACRO)
  time.sleep(random.uniform(1.0, 1.5))


def stand():
  inpututil.press_and_release_key(inpututil.STAND_MACRO)
  time.sleep(random.uniform(1.0, 1.5))
