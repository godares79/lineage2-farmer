# Does all monitoring of health, buffs, consumables, etc.
import time
from threading import Thread

import soundutil


class ResourceMonitorThread(Thread):

  def __init__(self, screen_monitor, using_pet):
    Thread.__init__(self)

    self.screen_monitor = screen_monitor
    self.using_pet = using_pet

    self.has_low_health = None
    self.has_low_mana = None
    self.has_high_health = None
    self.has_high_mana = None

  def run(self):
    while True:
      current_health_percent = self.screen_monitor.get_screen_object().get_health_percent()
      if current_health_percent < 20:
        self.has_low_health = True
      else:
        self.has_low_health = False

      if current_health_percent > 80:
        self.has_high_health = True
      else:
        self.has_high_health = False

      current_mana_percent = self.screen_monitor.get_screen_object().get_mana_percent()
      if current_mana_percent < 10:
        self.has_low_mana = True
      else:
        self.has_low_mana = False

      if current_mana_percent > 80:
        self.has_high_mana = True
      else:
        self.has_high_mana = False

      # If using a pet then monitor the pet health and alert if it starts getting attacked.
      if self.using_pet:
        pet_health_percent = self.screen_monitor.get_screen_object().get_pet_health_percent()
        if pet_health_percent < 100:
          soundutil.alert()

      time.sleep(3)
