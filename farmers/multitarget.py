import random
import threading
import time
from threading import Thread

import inpututil
import soundutil
from farmers import actions, aggromonitor


class SimpleMultiTargetFarm(Thread):
  # Simple multi-target farming that just uses the /target <target> command.
  # This does not require editing l2.ini to increase render distance as no mouse movement is used.

  def __init__(self, args, screen_capture_thread, resource_monitor_thread):
    Thread.__init__(self)
    self.stop_event = threading.Event()
    self.args = args
    self.screen_capture_thread = screen_capture_thread
    self.resource_monitor_thread = resource_monitor_thread

  def run(self):
    random.seed()
    currently_sitting = False
    aggro_monitor = None

    while True:
      if self.stop_event.is_set(): return

      valid_target_selected = False
      should_seed_and_spoil = True
      while not valid_target_selected:
        if self.stop_event.is_set(): return

        # If a target has already been selected then assume it is valid.
        current_target_name = self.screen_capture_thread.get_screen_object().get_current_target_name()
        if current_target_name:
          valid_target_selected = True
          if self.args.target in current_target_name:
            should_seed_and_spoil = True
          else:
            should_seed_and_spoil = False
          continue

        # Implement the target selection logic. It needs to handle some edge cases:
        # 1. Case where the target is selected, but cannot be seen (notification is system log).
        # 2. Case where the target is selected, but already dead.
        # 3. Case where the target is selected, but already under attack from another player.
        # 4. Case where no target is selected.
        inpututil.press_and_release_key(inpututil.TARGET_MACRO)
        time.sleep(random.uniform(0.8, 1.0))

        if not self.screen_capture_thread.get_screen_object().has_selected_target(self.args.target):
          print(f'Could not select {self.args.target}!')
          valid_target_selected = False
          soundutil.notify()
          actions.sit()
          currently_sitting = True
          inpututil.press_and_release_key(inpututil.CLEAR_TARGET)
          time.sleep(6)
          continue

        if (self.screen_capture_thread.get_screen_object().has_selected_target(self.args.target) and
                self.screen_capture_thread.get_screen_object().get_target_health() < 100):
          print(f'Target {self.args.target} health is less than 100%!')
          valid_target_selected = False
          soundutil.notify()
          actions.sit()
          currently_sitting = True
          inpututil.press_and_release_key(inpututil.CLEAR_TARGET)
          time.sleep(6)
          continue

        if self.screen_capture_thread.get_screen_object().is_target_unseen():
          print(f'Target {self.args.target} cannot be seen!')
          valid_target_selected = False
          soundutil.notify()
          actions.sit()
          currently_sitting = True
          inpututil.press_and_release_key(inpututil.CLEAR_TARGET)
          time.sleep(6)
          continue

        valid_target_selected = True

      # At this point a valid target is selected and we can go through the motions. Keep track of all mobs
      # attacking us. Only start the aggro monitor if it is not already started.
      if not aggro_monitor or aggro_monitor.is_completed():
        aggro_monitor = aggromonitor.AggroMonitor(self.screen_capture_thread)
        aggro_monitor.start()

      if self.stop_event.is_set(): return
      target_under_attack_event = threading.Event()
      actions.perform_starting_actions(
        self.screen_capture_thread, self.stop_event,
        should_stand=currently_sitting,
        should_seed=self.args.manor and should_seed_and_spoil,
        should_spoil=self.args.spoil and should_seed_and_spoil,
        monitor_if_attacked=True,
        target_under_attack_event=target_under_attack_event)

      currently_sitting = False
      if target_under_attack_event.is_set():
        # Deselect the current target, stop running, and continue the loop to select another target.
        inpututil.press_and_release_key(inpututil.CLEAR_TARGET)
        inpututil.press_and_release_key(inpututil.MOVE_BACK)
        continue

      if self.stop_event.is_set(): return
      current_target_name = self.screen_capture_thread.get_screen_object().get_current_target_name()
      actions.attack_mob(self.screen_capture_thread, self.stop_event, soulshot_setting=self.args.soulshot)

      # Remove the now dead target from the list of current attackers in the aggro_monitor.
      aggro_monitor.remove_attacker(current_target_name)

      if self.stop_event.is_set(): return
      actions.perform_closing_actions(
        self.screen_capture_thread, self.stop_event,
        should_harvest=self.args.manor and should_seed_and_spoil,
        should_sweep=self.args.spoil and should_seed_and_spoil,
        should_loot=True,
        should_sit=False)

      # Select a target in melee range if it exists.
      # If we are being attacked by a ranged target, the sleep after the next target command will give time for the
      # game to manually select the target.
      inpututil.press_and_release_key(inpututil.CLEAR_TARGET)
      inpututil.press_and_release_key(inpututil.NEXT_TARGET)
      time.sleep(random.uniform(0.5, 0.8))
      current_target_name = self.screen_capture_thread.get_screen_object().get_current_target_name()
      if current_target_name:
        # Go through the loop again to handle the other aggroing mobs.
        continue

      # Perform a final loot only after all attackers are dead.
      actions.loot(block=True)
      aggro_monitor.mark_as_completed()

      if self.resource_monitor_thread.has_low_health or self.resource_monitor_thread.has_low_mana:
        # Sit down and rest until both mana and health are considered high. Monitor for attackers during this time.
        actions.sit()
        currently_sitting = True
        aggro_monitor = aggromonitor.AggroMonitor(self.screen_capture_thread)
        aggro_monitor.start()
        while not self.resource_monitor_thread.has_high_health and not self.resource_monitor_thread.has_high_mana:
          if len(aggro_monitor.current_attackers) > 0:
            # Break out of the inner loop here and go to into a normal attacker management mode. The attacker should be
            # automatically selected by this point.
            break
          time.sleep(3)

  def should_stop(self):
    self.stop_event.set()


# Multi-target farming. Pans the mouse around the screen to locate other mobs with the same name.
# Should use an edited l2.ini file to get mob name display distance higher.
# Because moving, possibility of being aggro'd by other mobs. Need to confirm I am not being attacked before
# moving on to start of algorithm again. Two things to check: (1) Is there an aggroing mob in targetnext, or (2) if
# being damaged after sweep is performed.
class ComplexMultiTargetFarm(Thread):
  def __init__(self):
    pass

  def run(self):
    pass

  def _pan_screen(self):
    # Hold down the right mouse button and move the mouse slightly to pan.
    # Use https://stackoverflow.com/questions/1181464/controlling-mouse-with-python
    pass
