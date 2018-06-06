import time
import win32gui
import win32api
import ctypes
import pyautogui
from PIL import ImageOps, Image, ImageGrab
import numpy as np
from numpy import *
import time
import cv2
import random
from threading import Thread

WINDOW_SUBSTRING = "HALF-LIFE 2"

# Brazenhem algo
def draw_line(x1=0, y1=0, x2=0, y2=0):

    coordinates = []

    dx = x2 - x1
    dy = y2 - y1

    sign_x = 1 if dx > 0 else -1 if dx < 0 else 0
    sign_y = 1 if dy > 0 else -1 if dy < 0 else 0

    if dx < 0:
        dx = -dx
    if dy < 0:
        dy = -dy

    if dx > dy:
        pdx, pdy = sign_x, 0
        es, el = dy, dx
    else:
        pdx, pdy = 0, sign_y
        es, el = dx, dy

    x, y = x1, y1

    error, t = el / 2, 0

    coordinates.append([x, y])

    while t < el:
        error -= es
        if error < 0:
            error += el
            x += sign_x
            y += sign_y
        else:
            x += pdx
            y += pdy
        t += 1
        coordinates.append([x, y])

    return coordinates

def get_window_info():
    # set window info
    window_info = {}
    win32gui.EnumWindows(set_window_coordinates, window_info)
    return window_info


# EnumWindows handler
# sets L2 window coordinates
def set_window_coordinates(hwnd, window_info):
    if win32gui.IsWindowVisible(hwnd):
        if WINDOW_SUBSTRING in win32gui.GetWindowText(hwnd):
            rect = win32gui.GetWindowRect(hwnd)
            x = rect[0]
            y = rect[1]
            w = rect[2] - x
            h = rect[3] - y
            window_info['x'] = x
            window_info['y'] = y
            window_info['width'] = w
            window_info['height'] = h
            window_info['name'] = win32gui.GetWindowText(hwnd)
            win32gui.SetForegroundWindow(hwnd)


def get_screen(x1, y1, x2, y2):
    box = (x1 + 8, y1 + 30, x2 - 8, y2)
    screen = ImageGrab.grab(box)
    img = array(screen.getdata(), dtype=uint8).reshape((screen.size[1], screen.size[0], 3))
    return img


def get_target_centers(img):

    # Hide buff line
    # img[0:70, 0:500] = (0, 0, 0)

    # Hide your name in first camera position (default)
    img[210:230, 350:440] = (0, 0, 0)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # cv2.imwrite('1_gray_img.png', gray)

    # Find only white text
    ret, threshold1 = cv2.threshold(gray, 252, 255, cv2.THRESH_BINARY)
    # cv2.imwrite('2_threshold1_img.png', threshold1)

    # Morphological transformation
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 5))
    closed = cv2.morphologyEx(threshold1, cv2.MORPH_CLOSE, kernel)
    # cv2.imwrite('3_morphologyEx_img.png', closed)
    closed = cv2.erode(closed, kernel, iterations=1)
    # cv2.imwrite('4_erode_img.png', closed)
    closed = cv2.dilate(closed, kernel, iterations=1)
    # cv2.imwrite('5_dilate_img.png', closed)

    (_, centers, hierarchy) = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return centers

window_info = get_window_info()
print(window_info)
img = get_screen(
            window_info['x'],
           window_info['y'],
            window_info['x'] + window_info['width'],
            window_info['y'] + window_info['height']
        )
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
blurred = cv2.GaussianBlur(gray, (5, 5), 0)
edged = cv2.Canny(blurred, 50, 200, 255)
cv2.imwrite('test.jpg', edged)

SendInput = ctypes.windll.user32.SendInput

# C struct redefinitions
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time",ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                 ("mi", MouseInput),
                 ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

# Actuals Functions

def PressKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput( 0, hexKeyCode, 0x0008, 0, ctypes.pointer(extra) )
    x = Input( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def ReleaseKey(hexKeyCode):
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    ii_.ki = KeyBdInput( 0, hexKeyCode, 0x0008 | 0x0002, 0, ctypes.pointer(extra) )
    x = Input( ctypes.c_ulong(1), ii_ )
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def mse(imageA, imageB):
	err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
	err /= float(imageA.shape[0] * imageA.shape[1])
	return err

# directx scan codes http://www.gamespp.com/directx/directInputKeyboardScanCodes.html

def Forward(delay):
    PressKey(0x11)
    time.sleep(delay)
    ReleaseKey(0x11)
    time.sleep(delay)

def Left(delay):
    PressKey(0x05)
    time.sleep(delay)
    ReleaseKey(0x05)
    time.sleep(delay)

def Right(delay):
    PressKey(0x07)
    time.sleep(delay)
    ReleaseKey(0x07)
    time.sleep(delay)

def Run():
    while True:
        Forward(0.1)

TURN_BORDER = 700

img = get_screen(
            window_info['x'],
           window_info['y'],
            window_info['x'] + window_info['width'],
            window_info['y'] + window_info['height']
        )
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#blurred = cv2.GaussianBlur(gray, (5, 5), 0)
ImageA = cv2.Canny(gray, 175, 200)
ImageB = ImageA.copy()
res = 1000
delay = 0.1
PressKey(0x11)
time.sleep(0.3)

thread = Thread(target = Run)
thread.start()

while (True):
    #if res < 1000 and res > TURN_BORDER:
    #    delay = 0.3*(1000 - res)/(1000 - TURN_BORDER)
    #elif res <= TURN_BORDER:
    #    delay = 0
    #else:
    #    delay = 0.3
    #Forward(delay)

    img = get_screen(
            window_info['x'],
           window_info['y'],
            window_info['x'] + window_info['width'],
            window_info['y'] + window_info['height']
        )
    ImageA = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    #ImageA = cv2.Canny(blurred, 100, 200)
    res = mse(ImageA,ImageB)
    ImageB = ImageA.copy()
    print(res)
    if res < 700:
        chance = random.randint(0,1)
        if chance == 0:
            angle = random.randint(1,10)
            Left(angle/10)
        elif chance == 1:
            angle = random.randint(1,10)
            Right(angle/10)

    #cv2.imwrite('test' + str(i) + '.jpg', edged)