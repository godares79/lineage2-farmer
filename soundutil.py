import os
import winsound
from playsound import playsound


def notify():
  playsound(os.path.join('sounds', 'notify.wav'), block=False)


def warn():
  playsound(os.path.join('sounds', 'warn.wav'), block=False)


def alert():
  playsound(os.path.join('sounds', 'alert.wav'), block=False)


def play_alert():
  winsound.PlaySound('Notification.Looping.Alarm', winsound.SND_ALIAS | winsound.SND_ASYNC)
