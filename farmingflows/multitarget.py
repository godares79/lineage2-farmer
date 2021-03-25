from threading import Thread


# Multi-target farming. Pans the mouse around the screen to locate other mobs with the same name.
# Should use an edited l2.ini file to get mob name display distance higher.
# Because moving, possibility of being aggro'd by other mobs. Need to confirm I am not being attacked before
# moving on to start of algorithm again. Two things to check: (1) Is there an aggroing mob in targetnext, or (2) if
# being damaged after sweep is performed.
class HybridSingleTargetFarm(Thread):
  def __init__(self):
    pass

  def run(self):
    pass

  def _pan_screen(self):
    # Hold down the right mouse button and move the mouse slightly to pan.
    # Use https://stackoverflow.com/questions/1181464/controlling-mouse-with-python
    pass
