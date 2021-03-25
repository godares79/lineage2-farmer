# Main entry point

# Need several decorators:
# - Manor management (planting seeds and harvesting)
#   - Seems the prices are reasonable. It is worth doing. Crafted leather sells for much more than the seed cost.
#   - Russian manor calculator here: http://dodreams.blogspot.com/2008/04/lineage-2-manor-calculator.html
# - Spoil management
# - Health/Mana/CP/Experience/Buff monitor
# - Alerting when receiving whisper or local conversation
# - Bot detection manager

# Each function should add a necessary pause after that action
# (or do some kind of verification) so that other functions
# do not need to worry about waiting.

# Key Pressing and keypress receiving globally:
# Try to use ScanCodes to send keypresses:
# https://stackoverflow.com/questions/14489013/simulate-python-keypresses-for-controlling-a-game
# Can try the https://pypi.org/project/PyDirectInput/ module for sending keypresses.
# More here: https://danieldusek.com/feeding-key-presses-to-reluctant-games-in-python.html

# Can receive keypresses globally if I run the script as administrator. It's the only option.

# Mouse movement:
# Use pyautogui. If I find it too slow there is a delay setting that I can lower in order to make it faster.
# I need to make sure the mouse movements are a bit erratic.

# Linux L2 Support
# https://l2reborn.com/community/wontfix-not-a-bug/l2-reborn-on-linux-launcher-doesnt-work-while-l2-exe-runs-smoothly/

# I should create a general monitor that captures the whole screen every 0.N seconds and then
# actions can be performed on that screenshot to determine current state. The screenshot should be
# added to a queue, then there is another thread that watches that queue and performs analysis on the
# resulting screenshot.

# Console overlay for fullscreen game: https://guidedhacking.com/threads/fullscreen-opengl-overlay-with-python-ogl-glfw.16296/
# I could also overlay a windowed game. I kind of like having that more than having a separate console window.
# I'll need to remove the overlay for the split second while the screenshot happens every 0.5s. Then it can be
# re-added.

import argparse
import os
import sys
import time

import keyboard

import antibotprotection
from farmingalgorithm import FarmingAlgorithm
from farmingflows import singletarget, hybridsingletarget
import resourcemonitor
import screenmanagement
from lineageapplication import LineageApplication
from soulshotsetting import SoulshotSetting
from windowsetting import WindowSetting


parser = argparse.ArgumentParser(description='Simple farming program.')
parser.add_argument('--manor', required=False, type=bool, default=False,
                    help='True if farmer should plant and harvest seeds.')
parser.add_argument('--spoil', required=False, type=bool, default=False,
                    help='True if spoiling and sweeping should be done.')
parser.add_argument('--target', required=True, help='String name of the target of the intended farming target. '
                                                    'Can be a partial name.')
parser.add_argument('--soulshot', required=False, type=SoulshotSetting, choices=list(SoulshotSetting),
                    default=SoulshotSetting.NEVER, help='Soulshot setting.')
parser.add_argument('--sit', required=False, default=False, type=bool, help='Should sit between attacks?')
parser.add_argument('--using_wolf', required=False, type=bool, help='Set to True if using a wolf or other pet.')
parser.add_argument('--farming_algo', required=False, type=FarmingAlgorithm, choices=list(FarmingAlgorithm),
                    default=FarmingAlgorithm.SINGLE_TARGET, help='Farming algorithm choice.')
parser.add_argument('--quest', required=False, type=bool, help='Set to True if questing.')

parser.add_argument('--window_setting', required=True, type=WindowSetting, choices=list(WindowSetting),
                    help='Windows display setting. Must be 1080P.')
parser.add_argument('--l2_app', required=True, type=LineageApplication, choices=list(LineageApplication),
                    help='The Lineage2 application that is being opened.')

parser.add_argument('--testing', required=False, type=bool, help='If should use testing mode only.')
parser.add_argument('--testing_file', required=False, help='Path to test file from venv root.')

parser.add_argument('--sell_crops', required=False, type=bool, help='If should sell crops. Ignores all other args.')


def create_and_start_capture_thread(window_setting, testing_mode=None, testing_file=None):
  screen_monitor = screenmanagement.ScreenCaptureThread(window_setting, testing_mode, testing_file)
  screen_monitor.daemon = True
  screen_monitor.start()
  return screen_monitor


def create_and_start_farming_thread(args, capture_thread, resource_monitor):
  if args.farming_algo == FarmingAlgorithm.SINGLE_TARGET:
    farming_thread = singletarget.SingleTargetFarm(args, capture_thread, resource_monitor)
  elif args.farming_algo == FarmingAlgorithm.HYBRID_SINGLE_TARGET:
    farming_thread = hybridsingletarget.HybridSingleTargetFarm(args, capture_thread, resource_monitor)
  else:
    raise ValueError(f'Value of args.farming_algo is unimplemented: {args.farming_algo}')

  farming_thread.daemon = True
  farming_thread.start()
  return farming_thread


def create_and_start_bot_protection_thread(screen_monitor, target):
  anti_bot_protection = antibotprotection.AntiBotProtection(screen_monitor, target)
  anti_bot_protection.daemon = True
  anti_bot_protection.start()
  return anti_bot_protection


def create_and_start_resource_monitor_thread(screen_monitor, using_wolf):
  # A thread that will monitor health, mana, etc. and alert if anything goes outside of comfort areas.
  resource_monitor = resourcemonitor.ResourceMonitorThread(screen_monitor, using_wolf)
  resource_monitor.daemon = True
  resource_monitor.start()
  return resource_monitor


def main():
  args = parser.parse_args()

  print(f'\033[92mTarget: {args.target}\033[0m')
  print(f'\033[92mManoring: {args.manor}\033[0m')
  print(f'\033[92mSpoiling: {args.spoil}\033[0m')
  print(f'\033[92mSoulshot: {args.soulshot}\033[0m')
  print(f'\033[92mUsing Wolf: {args.using_wolf}\033[0m')
  print(f'\033[92mSit between attacks: {args.sit}\033[0m')
  print(f'\033[92mWindow Type: {args.window_setting}\033[0m')
  print(f'\033[92mFarming Algorithm: {args.farming_algo}\033[0m\n')

  if args.testing:
    print(f'In testing mode. File: {args.testing_file}')
    screen_monitor = create_and_start_capture_thread(args.window_setting, args.testing, args.testing_file)

    time.sleep(3)

    print(f'Has target spawned: {screen_monitor.get_screen_object().has_target_spawned(args.target)}')

    print('Spacebar to exit.')
    keyboard.wait('spacebar')
    sys.exit(0)

  if args.sell_crops:
    # Selling crops will be much more specialized. Just a single thread that quickly clicks buttons needed to sell
    # crops.
    print('Crop selling not yet implemented!')
    sys.exit(0)

  bot_protection_thread = None
  resource_monitor_thread = None
  screen_monitor = None
  while True:
    print('`/~ to start (or stop).')
    keyboard.wait('`')

    if not screen_monitor:
      # Add a short wait for data to get populated in the thread before continuing.
      screen_monitor = create_and_start_capture_thread(args.window_setting)
      time.sleep(1)

    # Start the resource monitor thread.
    if not resource_monitor_thread:
      resource_monitor_thread = create_and_start_resource_monitor_thread(screen_monitor, args.using_wolf)

    # Start farming flow in a new thread.
    farming_thread = create_and_start_farming_thread(args, screen_monitor, resource_monitor_thread)

    if not bot_protection_thread:
      bot_protection_thread = create_and_start_bot_protection_thread(screen_monitor, args.target)

    keyboard.wait('`')
    print('`/~ pressed. Stopping all threads.')
    farming_thread.stop()
    time.sleep(1)  # Sleep for 1 second after stopping so that we can spam the stop button.


if __name__ == '__main__':
  os.system('color')  # Turn enable colors in the terminal in Windows need this call.
  main()
