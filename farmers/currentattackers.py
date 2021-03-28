# Monitor to determine if under attack.
# Should keep a running list of all attackers that can be queried against to determine appropriate actions.
from threading import Thread


class AggroMonitor(Thread):

  def __init__(self, screen_monitor):
    Thread.__init__(self)
    self.screen_monitor = screen_monitor

  def run(self):
    pass
