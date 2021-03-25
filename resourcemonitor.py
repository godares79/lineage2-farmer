# Does all monitoring of health, buffs, consumables, etc.
import time
from threading import Thread

import soundutil


class ResourceMonitorThread(Thread):

  def __init__(self, screen_monitor, using_wolf):
    Thread.__init__(self)

    self.screen_monitor = screen_monitor
    self.using_wolf = using_wolf

    self.has_low_health = None
    self.has_low_mana = None
    self.has_high_health = None

  def run(self):
    while True:
      current_health_percent = self.screen_monitor.get_screen_object().get_health_percent()
      if current_health_percent < 25:
        self.has_low_health = True
      else:
        self.has_low_health = False

      if current_health_percent > 85:
        self.has_high_health = True
      else:
        self.has_high_health = False

      # Not bothering to track Mana currently.
      # if self.screen_monitor.get_screen_object().get_mana_percent() < 30:
      #   self.has_low_mana = True
      # else:
      #   self.has_low_mana = False

      # If using a pet (wolf) then monitor the pet health and alert if it gets low.
      if self.using_wolf:
        pet_health_percent = self.screen_monitor.get_screen_object().get_pet_health_percent()
        if pet_health_percent < 100:
          soundutil.play_alert()

      time.sleep(5)
