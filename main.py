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
from settings.farmingalgorithm import FarmingAlgorithm
from farmers import hybridsingletarget, multitarget, aggromonitor, mouseactions, hotkeyactions
import resourcemonitor
import screenmanagement
from settings.intendedtargets import IntendedTarget
from settings.lineageapplication import LineageApplication
from settings.soulshotsetting import SoulshotSetting
from settings.windowsetting import WindowSetting


parser = argparse.ArgumentParser(description='Simple farming program.')
parser.add_argument('-manor', dest='manor', default=False, action='store_true',
                    help='Should plant and harvest seeds.')
parser.add_argument('-spoil', dest='spoil', default=False, action='store_true',
                    help='Should spoil and sweep mobs.')
parser.add_argument('-target', dest='target', required=True,
                    help='String name of the target of the intended farming target. Can be a partial name.')
parser.add_argument('-soulshot', dest='soulshot', required=False,
                    type=SoulshotSetting, choices=list(SoulshotSetting), default=SoulshotSetting.NEVER,
                    help='Soulshot setting.')
parser.add_argument('-sit', dest='sit', default=False, action='store_true',
                    help='Should sit between attacks.')
parser.add_argument('-pet', dest='pet', required=False, action='store_true',
                    help='Specify if using a pet.')
parser.add_argument('-farm_type', dest='farm_type', required=True,
                    type=FarmingAlgorithm, choices=list(FarmingAlgorithm),
                    help='Farming algorithm choice.')
parser.add_argument('-quest', dest='quest', default=False, action='store_true',
                    help='Specify if running quest(s).')
parser.add_argument('-use_health_potions', dest='use_health_potions', default=False, action='store_true',
                    help='Specify if health potions should be used when health gets low.')
parser.add_argument('-target_enum', dest='target_enum', required=False,
                    type=IntendedTarget, choices=list(IntendedTarget), default=None,
                    help='Intended target (should replace -target args).')

parser.add_argument('-window_setting', dest='window_setting', required=True,
                    type=WindowSetting, choices=list(WindowSetting),
                    help='Windows display setting. Resolution must be 1080P.')
parser.add_argument('-l2_app', dest='l2_app', required=True,
                    type=LineageApplication, choices=list(LineageApplication),
                    help='The Lineage2 application that is being opened.')

parser.add_argument('-testing', dest='testing', required=False, action='store_true',
                    help='Specify if in testing mode.')
parser.add_argument('-testing_file', required=False,
                    help='Path to test file from venv root.')


def create_and_start_capture_thread(window_setting, testing_mode=None, testing_file=None):
  screen_monitor = screenmanagement.ScreenCaptureThread(window_setting, testing_mode, testing_file)
  screen_monitor.daemon = True
  screen_monitor.start()
  return screen_monitor


def create_and_start_farming_thread(args, capture_thread, resource_monitor):
  if args.farm_type == FarmingAlgorithm.HYBRID_SINGLE_TARGET:
    farming_thread = hybridsingletarget.HybridSingleTargetFarm(args, capture_thread)
  elif args.farm_type == FarmingAlgorithm.BASIC_MULTI_TARGET:
    farming_thread = multitarget.SimpleMultiTargetFarm(args, capture_thread, resource_monitor)
  else:
    raise ValueError(f'Value of args.farm_type is unimplemented: {args.farm_type}')

  farming_thread.daemon = True
  farming_thread.start()
  return farming_thread


def create_and_start_bot_protection_thread(screen_monitor, target):
  anti_bot_protection = antibotprotection.AntiBotProtection(screen_monitor, target)
  anti_bot_protection.daemon = True
  anti_bot_protection.start()
  return anti_bot_protection


def create_and_start_resource_monitor_thread(screen_monitor, using_pet):
  # A thread that will monitor health, mana, etc. and alert if anything goes outside of comfort areas.
  resource_monitor = resourcemonitor.ResourceMonitorThread(screen_monitor, using_pet)
  resource_monitor.daemon = True
  resource_monitor.start()
  return resource_monitor


def main():
  args = parser.parse_args()

  print(f'\033[92mTarget: {args.target}\033[0m')
  print(f'\033[92mManoring: {args.manor}\033[0m')
  print(f'\033[92mSpoiling: {args.spoil}\033[0m')
  print(f'\033[92mSoulshot: {args.soulshot}\033[0m')
  print(f'\033[92mUsing Pet: {args.pet}\033[0m')
  print(f'\033[92mSit between attacks: {args.sit}\033[0m')
  print(f'\033[92mWindow Type: {args.window_setting}\033[0m')
  print(f'\033[92mFarming Algorithm: {args.farm_type}\033[0m\n')

  if args.testing:
    print(f'In testing mode. File: {args.testing_file}')
    screen_monitor = create_and_start_capture_thread(args.window_setting, args.testing, args.testing_file)
    time.sleep(3)

    mouseactions.select_target_with_mouse(screen_monitor, args.target_enum)
    time.sleep(1)
    mouseactions.select_target_with_mouse(screen_monitor, args.target_enum)
    time.sleep(1)
    mouseactions.select_target_with_mouse(screen_monitor, args.target_enum)
    time.sleep(1)
    mouseactions.select_target_with_mouse(screen_monitor, args.target_enum)
    time.sleep(1)
    mouseactions.select_target_with_mouse(screen_monitor, args.target_enum)
    time.sleep(1)
    mouseactions.select_target_with_mouse(screen_monitor, args.target_enum)
    time.sleep(1)

    print('Spacebar to exit.')
    keyboard.wait('spacebar')
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
      resource_monitor_thread = create_and_start_resource_monitor_thread(screen_monitor, args.pet)

    # Start farming flow in a new thread.
    farming_thread = create_and_start_farming_thread(args, screen_monitor, resource_monitor_thread)

    if not bot_protection_thread:
      bot_protection_thread = create_and_start_bot_protection_thread(screen_monitor, args.target)

    keyboard.wait('`')
    print('`/~ pressed. Stopping all threads.')
    farming_thread.should_stop()
    time.sleep(1)  # Sleep for 1 second after stopping so that we can spam the stop button.


if __name__ == '__main__':
  os.system('color')  # Turn enable colors in the terminal in Windows need this call.
  main()
