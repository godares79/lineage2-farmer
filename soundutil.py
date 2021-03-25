import winsound


def play_alert():
  winsound.PlaySound('Notification.Looping.Alarm', winsound.SND_ALIAS | winsound.SND_ASYNC)
