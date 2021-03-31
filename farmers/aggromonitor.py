# Monitor to determine if under attack.
# Should keep a running list of all attackers that can be queried against to determine appropriate actions.
import re
import threading
import time
from threading import Thread


class AggroMonitor(Thread):

  def __init__(self, screen_monitor):
    Thread.__init__(self)
    self.screen_monitor = screen_monitor
    self.complete_event = threading.Event()

    self.current_attackers = []

  def run(self):
    # Every 1 seconds get the incoming damage portions of the primary text box.
    # - Crop box: (21, 900) -> (343, 1031)
    # - RGB Color: (215, 121, 49)
    # Extract the names of the attackers: <attacker name> hit you for N damage.
    # For each attacker, use _add_new_attacker to add to the list.
    name_match_regex = re.compile(r'^(.*)hit you for.*$', re.IGNORECASE | re.MULTILINE)
    while True:
      if self.complete_event.is_set(): return

      attackers = self.screen_monitor.get_screen_object().get_attackers()
      names = name_match_regex.findall(attackers)

      for name in names:
        self._add_new_attacker(name.strip())

      time.sleep(1)

  def remove_attacker(self, attacker_name):
    # Remove the given attacker_name from the list.
    # Return True if current_attackers still has some entities inside the list.
    if attacker_name in self.current_attackers:
      self.current_attackers.remove(attacker_name)

    if len(self.current_attackers) > 0:
      return True
    else:
      return False

  def _add_new_attacker(self, attacker_name):
    # If attacker_name is not in the current_attackers then add to the list.
    if attacker_name not in self.current_attackers:
      self.current_attackers.append(attacker_name)

  def mark_as_completed(self):
    self.complete_event.set()

  def is_completed(self):
    return self.complete_event.is_set()
