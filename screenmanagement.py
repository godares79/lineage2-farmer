# Monitors all player resources..
# Does not perform any actions, only monitors and parses information as needed.

# Parsing pixel data:
# https://stackoverflow.com/questions/23147244/most-efficient-quickest-way-to-parse-pixel-data-with-python
# Using MSS and Pillow to do cropping is fast enough. I don't need to concern myself.

# Save interface.xdat. I think that has the interface item locations and settings in it. Have some other
# backups of the config files in system/ too.

# Use Tesseract 5 to do the OCR. It is much better than Tesseract 4. The downside is that I need to use
# pytesseract. tesserocr does not support Tesseract 5 on Windows.
import os
import threading
import time
from enum import Enum
from queue import Queue
from threading import Thread

import cv2
import mss
import numpy as np
import pytesseract
import win32gui
from PIL import Image, ImageDraw

from settings.windowsetting import WindowSetting


# Queue for passing screenshot entries from the capture thread to the writer thread.
# Entries will be a tuple of (time.time(), ScreenObject).
screenshot_queue = Queue(20)


class ScreenCaptureThread(Thread):

  class Rectangle:
    def __init__(self, rectangle_list):
      self.x = rectangle_list[0]
      self.y = rectangle_list[1]
      self.width = rectangle_list[2] - self.x
      self.height = rectangle_list[3] - self.y

    def to_map(self):
      return {'top': self.y, 'left': self.x, 'width': self.width, 'height': self.height}


  def __init__(self, window_setting, testing_mode=None, testing_file=None):
    Thread.__init__(self)
    self.screen_object = None
    self.stop_event = threading.Event()
    self.window_setting = window_setting

    self.testing_mode = testing_mode
    self.testing_file = testing_file

  def stop(self):
    self.stop_event.set()

  def get_screen_object(self):
    return self.screen_object

  def _get_window_rectangle(self):
    # Use EnumWindows to find the appropriate window I want. If I only do it at script startup then
    # performance is no big deal.
    window_id = []
    win32gui.EnumWindows(lambda x, y: y.append(x) if 'Lineage II' == win32gui.GetWindowText(x).strip() else None,
                         window_id)

    if not window_id:
      print('\033[91mDid not find Lineage II window. Ensure the game is launched.\033[0m')
      return None
    if len(window_id) > 1:
      print('\033[91mFound multiple Lineage II windows. Not sure which one to use!\033[0m')
      return None

    try:
      win32gui.SetForegroundWindow(window_id[0])
    except:
      print('\033[91mFailed to bring Lineage II window to the foreground. Make sure the console was started in '
            'admin mode prior to the Lineage II launcher.\033[0m')
      return None

    time.sleep(1)

    # It seems that on Windows10 there are hidden padding values that are returned by GetWindowsRect.
    # Seems that there is a 7px padding around the visible left, right, and bottom borders of the window.
    # TODO: Adjust other pixel values used throughout this accordingly as my old pixel values were off.
    window_rect = self.Rectangle(win32gui.GetWindowRect(window_id[0]))

    if self.window_setting == WindowSetting.WINDOWED:
      window_rect.x += 8
      window_rect.width -= 16
      window_rect.y += 31
      window_rect.height -= 39

    return window_rect

  def run(self):
    # Start running the screenshot output thread.
    history_output_thread = HistoryOutputThread()
    history_output_thread.daemon = True
    history_output_thread.start()

    # Counter for determining when a screenshot should be added to the output queue.
    # Should loop every 10 iterations as a screenshot is taken every 0.2s.
    screen_output_counter = 0

    if self.testing_mode:
      # Load the testing file as though it was as an active screenshot.
      image = Image.open(self.testing_file)
      self.screen_object = ScreenObject(image)
      image.show()
      while True:
        screen_output_counter += 1

        # Just busywait forever.
        time.sleep(0.2)

        # Add stuff to the screenshot queue.
        if screen_output_counter == 10:
          if not screenshot_queue.full():
            screenshot_queue.put((time.time(), self.screen_object))
          screen_output_counter = 0

    window_rectangle = None
    if self.window_setting == WindowSetting.WINDOWED:
      window_rectangle = self._get_window_rectangle()
    elif self.window_setting == WindowSetting.FULLSCREEN:
      window_rectangle = ScreenCaptureThread.Rectangle((0, 0, 1920, 1080))

    if not window_rectangle:
      print('\033[91mCould not get window dimensions. Unable to take screenshot.\033[0m')
      return

    with mss.mss() as sct:
      while not self.stop_event.is_set():
        sct_img = sct.grab(window_rectangle.to_map())
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        self.screen_object = ScreenObject(img)

        # My timing needs aren't enough to do any kind of thread scheduling. Just do a sleep for 0.2s.
        time.sleep(0.2)

        # Add every 10th screenshot to the output queue.
        screen_output_counter += 1
        if screen_output_counter == 10:
          if not screenshot_queue.full():
            screenshot_queue.put((time.time(), self.screen_object))
          screen_output_counter = 0


class ScreenObject:
  # Represents a screen capture of a game screen.

  class Tribool(Enum):
    TRUE = 'TRUE'
    FALSE = 'FALSE'
    UNKNOWN = 'UNKNOWN'


  def __init__(self, pillow_image):
    self.pillow_image = pillow_image
    self._system_message_text = None
    self._processed_target_text = None
    self._target_health_percent = None

  def get_health_percent(self):
    # Create opencv image for the health bar area.
    # Interestingly, if I only try to crop a single row of pixels I get an exception.
    # Just crop two rows of pixels instead.
    health_img = cv2.cvtColor(np.asarray(self.pillow_image.crop((868, 1037, 1220, 1038))), cv2.COLOR_RGB2BGR)

    # Total length. Use the total length because the flashing of the health bar when health is low makes
    # capturing the health portion difficult.
    total_length = len(health_img[0])

    # Length of low health portion.
    mask = cv2.inRange(health_img, (41, 28, 99), (41, 28, 99))
    low_health_len = len(health_img[mask != 0])

    if low_health_len + total_length == 0:
      # Something went wrong. Just return None.
      return None

    return int((total_length / (total_length + low_health_len)) * 100)

  def get_pet_health_percent(self):
    # Same colors as getting the target health. But just different co-ordinates.
    # (868, 969) -> (1219, 975)

    # Create opencv image for the health bar area.
    health_bar_cv_img = cv2.cvtColor(np.asarray(self.pillow_image.crop((868, 969, 1219, 975))), cv2.COLOR_RGB2BGR)
    mask = cv2.inRange(health_bar_cv_img, (40, 30, 90), (90, 70, 120))
    low_health_len = len(health_bar_cv_img[mask != 0])
    total_length = len(health_bar_cv_img[0])

    if low_health_len + total_length == 0:
      return None

    return int((total_length / (total_length + low_health_len)) * 100)

  def get_mana_percent(self):
    # Create opencv image for the health bar area.
    # Interestingly, if I only try to crop a single row of pixels I get an exception.
    # Just crop two rows of pixels instead.
    mana_img = cv2.cvtColor(np.asarray(self.pillow_image.crop((868, 1051, 1120, 1052))), cv2.COLOR_RGB2BGR)

    # Total length. Like in health calculation, used due low mana alert changing the bar color.
    total_length = len(mana_img[0])

    # Length of low mana portion.
    mask = cv2.inRange(mana_img, (99, 65, 24), (99, 65, 24))
    low_mana_len = len(mana_img[mask != 0])

    if low_mana_len + total_length == 0:
      # Something went wrong. Just return None.
      return None

    return int((total_length / (total_length + low_mana_len)) * 100)

  def get_pet_mana_percent(self):
    pass

  def get_pet_hunger_percent(self):
    pass

  def get_cp(self):
    pass

  def has_started_sowing(self):
    # True if seeding has begun. False if not or unknown.
    system_message_text = self._get_system_message_text()
    if 'you use sowing' in system_message_text:
      return True
    else:
      return False

  def was_harvest_successful(self):
    # Tribool.TRUE if harvest succeeded. Tribool.FALSE if it failed. Tribool.UNKNOWN if unknown.
    system_message_text = self._get_system_message_text()
    if 'you harvested' in system_message_text:
      return ScreenObject.Tribool.TRUE
    if 'the harvest has failed' in system_message_text:
      return ScreenObject.Tribool.FALSE
    return ScreenObject.Tribool.UNKNOWN

  def get_spoil_status(self):
    # True if spoil successful, False otherwise.
    # First 3 rows pixel bounds: (21, 837) -> (341, 884)
    # Use a pixel color match because it is more accurate than OCR.
    system_crop_img = self.pillow_image.crop((21, 837, 341, 884))
    cvarr = cv2.cvtColor(np.asarray(system_crop_img), cv2.COLOR_RGB2BGR)
    mask = cv2.inRange(cvarr, (115, 220, 62), (120, 230, 67))
    if len(cvarr[mask != 0]) > 0:
      return True
    return False

  def is_spoil_applied(self):
    # True if spoil has been applied, False otherwise.
    # First 3 rows pixel bounds: (21, 837) -> (341, 884)
    # Use OCR to match text as sweeper and spoil system message are same color.
    system_crop_img = self.pillow_image.crop((21, 837, 341, 884))
    if 'use spoil' in self._process_text(system_crop_img):
      return True
    return False

  def has_been_whispered(self):
    # Chat window co-ords: (21, 909) -> (343, 1031)
    # Monitor for colors of text in the textbox. Whispers RGB: (255, 0, 255)
    chat_window_img = self.pillow_image.crop((21, 909, 343, 1031))
    cvarr = cv2.cvtColor(np.asarray(chat_window_img), cv2.COLOR_RGB2BGR)
    mask = cv2.inRange(cvarr, (250, 0, 250), (255, 10, 255))
    if len(cvarr[mask != 0]) > 0:
      return True
    return False

  def has_local_chat(self):
    # Chat window co-ords: (21, 909) -> (343, 1031)
    # Monitor for colors of text in the textbox. Local Text RGB: (220, 217, 220)
    chat_window_img = self.pillow_image.crop((21, 909, 343, 1031))
    cvarr = cv2.cvtColor(np.asarray(chat_window_img), cv2.COLOR_RGB2BGR)
    mask = cv2.inRange(cvarr, (210, 210, 210), (225, 220, 225))
    if len(cvarr[mask != 0]) > 0:
      return True
    return False

  def has_shout_chat(self):
    # Chat window co-ords: (21, 909) -> (343, 1031)
    # Monitor for colors of text in the textbox. Local Text RGB: (220, 217, 220)
    chat_window_img = self.pillow_image.crop((21, 909, 343, 1031))
    cvarr = cv2.cvtColor(np.asarray(chat_window_img), cv2.COLOR_RGB2BGR)
    mask = cv2.inRange(cvarr, (0, 100, 240), (0, 112, 255))
    if len(cvarr[mask != 0]) > 0:
      return True
    return False

  def has_selected_target(self, target):
    # Look at the target window and do OCR to determine the selected target matches the given target.
    # I can use opencv for this instead. Able to avoid looping over pixels that way.
    current_target_box = self.pillow_image.crop((1248, 1011, 1582, 1028))

    for i in range(current_target_box.size[0]):
      for j in range(current_target_box.size[1]):
        pixel = current_target_box.getpixel((i, j))
        if pixel[0] + pixel[1] + pixel[2] > 500:
          current_target_box.putpixel((i, j), (255, 255, 255))
        else:
          current_target_box.putpixel((i, j), (0, 0, 0))
    current_target_box = current_target_box.resize((current_target_box.size[0] * 2, current_target_box.size[1] * 2))

    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
    return target.lower() in pytesseract.image_to_string(current_target_box).strip().lower()

  def has_target_spawned(self, target):
    if self._processed_target_text:
      return self._processed_target_text

    # I can speed up the cropping and masking by just doing it all in opencv/numpy. The cropping should not be done
    # in Pillow.
    polygon = ((0, 0), (0, 756), (352, 756), (352, 835), (1650, 835), (1650, 0))
    mask_img = Image.new('L', self.pillow_image.size, 0)
    draw = ImageDraw.Draw(mask_img)
    draw.polygon(polygon, fill=255, outline=None)
    black_img = Image.new('L', self.pillow_image.size, 0)
    result = Image.composite(self.pillow_image, black_img, mask_img)

    # Turn anything that isn't white into black. Makes OCR easier.
    cv_img = cv2.cvtColor(np.asarray(result), cv2.COLOR_RGB2BGR)
    white_low = np.array([240, 240, 240])
    white_high = np.array([255, 255, 255])
    mask = cv2.inRange(cv_img, white_low, white_high)
    cv_img[mask == 0] = (0, 0, 0)

    # Using OCR...
    processed_image = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
    self._processed_target_text = pytesseract.image_to_string(processed_image).strip().lower()

    if target.lower() in self._processed_target_text:
      return True
    else:
      return False

    # TODO: Using OpenCV template matching... I should use this in the future.
    searcher_text = cv2.imread(os.path.join('images', 'monster_eye_searcher.bmp'))
    template_result = cv2.matchTemplate(cv_img, searcher_text, cv2.TM_CCOEFF_NORMED)
    match_location = np.where(template_result > 0.7)
    if len(match_location[0]) >= 1 or len(match_location[1]) >= 1:
      for pt in zip(*match_location[::-1]):
        cv2.rectangle(cv_img, (pt[0] - 73, pt[1]), (pt[0] + 48, pt[1] + 15), (0, 0, 255), 1)
        print(f'Intended Click Location: {pt[0] - 15}, {pt[1] + 20}')
      return True
    else:
      return False

  def antibot_text_on_screen(self):
    # Returns true if there is an unknown name (not my name, or the target's name on the display).
    # This can also realistically detect the bot captcha.
    # I can speed up the cropping and masking by just doing it all in opencv/numpy. The cropping should not be done
    # in Pillow.
    polygon = ((10, 10), (10, 756), (352, 756), (352, 835), (1650, 835), (1650, 10))
    mask_img = Image.new('L', self.pillow_image.size, 0)
    draw = ImageDraw.Draw(mask_img)
    draw.polygon(polygon, fill=255, outline=None)
    black_img = Image.new('L', self.pillow_image.size, 0)
    result = Image.composite(self.pillow_image, black_img, mask_img)

    # Turn anything that isn't white into black. Makes OCR easier.
    cv_img = cv2.cvtColor(np.asarray(result), cv2.COLOR_RGB2BGR)
    white_low = np.array([180, 200, 200])
    white_high = np.array([255, 255, 255])
    mask = cv2.inRange(cv_img, white_low, white_high)
    cv_img[mask == 0] = (0, 0, 0)

    processed_image = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
    self._processed_target_text = pytesseract.image_to_string(processed_image).strip().lower()

    # Return True if the typical antibot text appears anywhere in the onscreen text
    if (('antibot' in self._processed_target_text)
        or ('anti' in self._processed_target_text)
        or ('ok' in self._processed_target_text)
        or ('cancel' in self._processed_target_text)
        or ('bot' in self._processed_target_text)
        or ('click' in self._processed_target_text)
        or ('press' in self._processed_target_text)
        or ('dualbox' in self._processed_target_text)
        or ('dualbex' in self._processed_target_text)):
      return True
    return False

  def is_antibot_protection_present(self):
    # There are two possible antibot dialogs that can appear. Check if they are present.
    antibot_location_one = self.pillow_image.crop((806, 475, 1114, 604))
    antibot_location_two = self.pillow_image.crop((0, 280, 309, 680))

    # For location one, search for the AntiBotIcon.
    antibot_icon = cv2.imread(os.path.join('images', 'AntiBotIcon.bmp'))
    template_result = cv2.matchTemplate(
        cv2.cvtColor(np.asarray(antibot_location_one), cv2.COLOR_RGB2BGR),
        antibot_icon,
        cv2.TM_CCOEFF_NORMED)
    match_location = np.where(template_result > 0.7)
    # np.where returns a tuple of two arrays (one for x direction, one for y direction).
    # The array length of both will be >= 1 if there is a match.
    if len(match_location[0]) >= 1 or len(match_location[1]) >= 1:
      return True

    # For location two, search for the anti dualbox text title.
    # I'm going to try doing a template match again. But can use OCR if needed too.
    antidualbox_text = cv2.imread(os.path.join('images', 'AntiDualboxText.bmp'))
    template_result = cv2.matchTemplate(
        cv2.cvtColor(np.asarray(antibot_location_two), cv2.COLOR_RGB2BGR),
        antidualbox_text,
        cv2.TM_CCOEFF_NORMED)
    match_location = np.where(template_result > 0.7)
    if len(match_location[0]) >= 1 or len(match_location[1]) >= 1:
      return True

  def unknown_dialog_present(self):
    # Returns True if there is any kind of unknown dialog present on the screen.
    # 1. Match the golden window titlebar in the top left OR the X symbol in the top right
    watch_area_img = self.pillow_image.crop((0, 0, 1650, 760))

    title_bar_top_left = cv2.imread(os.path.join('images', 'TitleBarTopLeft.bmp'))
    title_bar_top_right = cv2.imread(os.path.join('images', 'TitleBarTopRight.bmp'))
    top_left_template_result = cv2.matchTemplate(
      cv2.cvtColor(np.asarray(watch_area_img), cv2.COLOR_RGB2BGR),
      title_bar_top_left,
      cv2.TM_CCOEFF_NORMED)
    top_left_match_location = np.where(top_left_template_result > 0.7)
    if len(top_left_match_location[0]) >= 1 or len(top_left_match_location[1]) >= 1:
      return True
    top_right_template_result = cv2.matchTemplate(
      cv2.cvtColor(np.asarray(watch_area_img), cv2.COLOR_RGB2BGR),
      title_bar_top_right,
      cv2.TM_CCOEFF_NORMED)
    top_right_match_location = np.where(top_right_template_result > 0.7)
    if len(top_right_match_location[0]) >= 1 or len(top_right_match_location[1]) >= 1:
      return True

    # 2. Match the dialog window border. This is always the same it seems: A 1 pixel wide bar of black then grey.
    # The black and grey colors are not consistent, so use a range for matching.
    # Apply a mask for black and grey pixels to the whole image then run HoughLinesP over the masked image.
    cvarr = cv2.cvtColor(np.asarray(watch_area_img), cv2.COLOR_RGB2BGR)

    black_mask = cv2.inRange(cvarr, (0, 0, 0), (10, 10, 10))
    grey_mask = cv2.inRange(cvarr, (70, 70, 70), (100, 100, 100))
    combined_mask = cv2.bitwise_xor(black_mask, grey_mask)
    cvarr[combined_mask == 0] = (0, 255, 0)

    # Try a HoughLinesP call on the resultant mask image.
    edges = cv2.Canny(cvarr, 50, 150, apertureSize=3)
    minLineLength = 100
    maxLineGap = 0
    lines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=100, minLineLength=minLineLength, maxLineGap=maxLineGap)
    if lines is None:
      return False
    else:
      # for i in range(lines.shape[0]):
      #   x1 = lines[i][0][0]
      #   y1 = lines[i][0][1]
      #   x2 = lines[i][0][2]
      #   y2 = lines[i][0][3]
      #   cv2.line(cvarr, (x1, y1), (x2, y2), (0, 0, 255), 2)
      # Image.fromarray(cv2.cvtColor(cvarr, cv2.COLOR_BGR2RGB)).show()
      return True

  def get_target_health(self):
    # Don't bother to recalculate.
    if self._target_health_percent:
      return self._target_health_percent

    # Create opencv image for the health bar area.
    health_bar_cv_img = cv2.cvtColor(np.asarray(self.pillow_image.crop((1246, 1030, 1597, 1035))), cv2.COLOR_RGB2BGR)
    health_bar_cv_img_copy = health_bar_cv_img.copy()

    # Length of high health portion.
    mask = cv2.inRange(health_bar_cv_img, (20, 0, 200), (140, 100, 255))
    high_health_len = len(health_bar_cv_img[mask != 0])

    # Length of low health portion.
    mask = cv2.inRange(health_bar_cv_img_copy, (40, 30, 90), (90, 70, 120))
    low_health_len = len(health_bar_cv_img_copy[mask != 0])

    if low_health_len + high_health_len == 0:
      # Something went wrong. Just return None.
      return None

    self._target_health_percent = int((high_health_len / (high_health_len+low_health_len)) * 100)
    return self._target_health_percent

  def get_icon_hotkeys(self):
    # Use NumPy and OpenCV to do template matching to find subimages. I can use that to find bounding boxes, icons,
    # etc. Answer 2: https://stackoverflow.com/questions/7670112/finding-a-subimage-inside-a-numpy-image
    # The bounding boxes can be used to determine which co-ordinates to use for OCR. The subimages are useful for
    # checking tooltips, icon hotkeys, etc. I dunno...
    pass

  def get_attackers(self):
    # Get the attacker lines from the primary text box.
    # - Crop box: (21, 900) -> (343, 1031)
    # - RGB Color: (215, 121, 49)
    primary_textbox_cropped_img = self.pillow_image.crop((21, 900, 343, 1031))
    cv_img = cv2.cvtColor(np.asarray(primary_textbox_cropped_img), cv2.COLOR_RGB2BGR)
    mask = cv2.inRange(cv_img, (49, 121, 215), (49, 121, 215))
    cv_img[mask == 0] = (0, 0, 0)
    cv_img[mask != 0] = (255, 255, 255)

    primary_textbox_processed = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    system_crop_img = primary_textbox_processed.resize(
      (primary_textbox_processed.size[0] * 3, primary_textbox_processed.size[1] * 3))
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
    return pytesseract.image_to_string(system_crop_img).strip().lower()

  def _get_system_message_text(self):
    if self._system_message_text:
      # Only parse the first time.
      return self._system_message_text

    system_crop_img = self.pillow_image.crop((21, 768, 345, 884))
    self._system_message_text = self._process_text(system_crop_img)
    return self._system_message_text

  def _process_text(self, image):
    for i in range(image.size[0]):
      for j in range(image.size[1]):
        pixel = image.getpixel((i, j))
        if pixel[0] + pixel[1] + pixel[2] > 300:
          image.putpixel((i, j), (255, 255, 255))
        else:
          image.putpixel((i, j), (0, 0, 0))

    system_crop_img = image.resize((image.size[0] * 3, image.size[1] * 3))

    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
    return pytesseract.image_to_string(system_crop_img).strip().lower()


class HistoryOutputThread(Thread):
  # This is to track when something goes wrong. Use a Queue for communication between capture thread and this.
  # Writing and then deleting is very slow. Maybe I should only take a screenshot every 2 seconds?

  # The maximum number of screenshots that should be output in total before old screens are removed.
  MAX_SCREENS = 30

  def __init__(self):
    Thread.__init__(self)

    self.write_counter = 0
    self.most_recent_timestamps_queue = Queue(HistoryOutputThread.MAX_SCREENS)

  def run(self):
    # Remove all output files currently in the recentvideo directory.
    for old_screenshot in os.listdir('recentvideo'):
      print(f'Removing old screenshot: {old_screenshot}')
      os.remove(f'{os.path.join("recentvideo", old_screenshot)}')

    while True:
      if not screenshot_queue.empty():
        self.write_counter += 1

        timestamp, screen_object = screenshot_queue.get()
        self.most_recent_timestamps_queue.put(timestamp)
        screen_object.pillow_image.save(f'{os.path.join("recentvideo", f"{timestamp}.png")}')

        if self.write_counter >= HistoryOutputThread.MAX_SCREENS:
          os.remove(f'{os.path.join("recentvideo", f"{self.most_recent_timestamps_queue.get()}.png")}')

      # Only check every 0.5s to avoid using tons of CPU.
      time.sleep(0.5)
