import threading
from threading import Thread

from farmers import actions


class SimpleMultiTargetFarm(Thread):
  # Simple multi-target farming that just uses the /target <target> command.
  # This does not require editing l2.ini to increase render distance.

  def __init__(self, args, screen_capture_thread):
    Thread.__init__(self)
    self.stop_event = threading.Event()
    self.args = args
    self.screen_capture_thread = screen_capture_thread

  def run(self):
    # TODO: Implement the target selection logic. It needs to handle some edge cases:
    # 1. Case where the target is selected, but cannot be seen (notification is system log).
    # 2. Case where the target is selected, but already dead.
    # 3. Case where the target is selected, but already under attack from another player.
    # 4. Case where no target is selected.

    if self.stop_event.is_set(): return
    actions.perform_starting_actions(
      self.screen_capture_thread, self.stop_event,
      should_stand=False, should_seed=self.args.manor, should_spoil=self.args.spoil)

    if self.stop_event.is_set(): return
    actions.attack_mob(self.screen_capture_thread, self.stop_event, soulshot_setting=self.args.soulshot)

    if self.stop_event.is_set(): return
    # TODO: Handle case where we are being attacked by another mob.
    # TODO: Only loot if not currently under attack by another mob. If under attack, harvest and sweep only.
    actions.perform_closing_actions(
      self.screen_capture_thread, self.stop_event,
      should_harvest=self.args.manor, should_sweep=self.args.spoil, should_loot=True, should_sit=False)

    # TODO: Should sit down and rest if health or mana gets too low. Monitor to determine if attacked at this time.

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
