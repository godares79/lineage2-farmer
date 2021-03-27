import time
from threading import Thread

import soundutil


class AntiBotProtection(Thread):
  # For initial implementation, just beep if the bot protection comes up and alert the farming thread to spin down.
  # Maybe just send the numlock event to do the spin down, that way it doesn't restart until I want.

  def __init__(self, screen_monitor_thread, target):
    Thread.__init__(self)
    self.screen_monitor_thread = screen_monitor_thread
    self.target = target

  def run(self):
    # Need to check constantly to see if the bot protection windows have popped up.
    # Signal an alarm if that has happened.
    while True:
      if self.screen_monitor_thread.get_screen_object().is_antibot_protection_present():
        print('Antibot Protection present!')
        soundutil.alert()
        time.sleep(5)

      if self.screen_monitor_thread.get_screen_object().has_been_whispered():
        print('Whisper received!')
        soundutil.alert()
        time.sleep(5)

      if self.screen_monitor_thread.get_screen_object().has_local_chat():
        print('Local chat received!')
        soundutil.alert()
        time.sleep(5)

      if self.screen_monitor_thread.get_screen_object().has_shout_chat():
        print('Shout chat received!')
        soundutil.alert()
        time.sleep(5)

      if self.screen_monitor_thread.get_screen_object().antibot_text_on_screen():
        print('Antibot text recognized on screen!')
        soundutil.alert()
        time.sleep(5)

      if self.screen_monitor_thread.get_screen_object().unknown_dialog_present():
        print('Unrecognized dialog displayed on screen!')
        soundutil.alert()
        time.sleep(5)

      time.sleep(5)
