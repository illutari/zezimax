import random
import time
import math
import cv2
import numpy as np
from datetime import datetime
from mss import mss
from PIL import Image


class SharedSkillActions:
    """Shared utility methods used by ALL skills."""
    
    def __init__(self, input_controller):
        self.input = input_controller
    
    def detect_idle_orange(self, img_bgr):
        """General idle orange screen detection."""
        idle_color_ratio = 0.67
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        lower_orange = np.array([0, 60, 100])
        upper_orange = np.array([40, 255, 255])
        mask = cv2.inRange(hsv, lower_orange, upper_orange)
        
        h, w = mask.shape
        center_w = int(w * 0.68)
        center_h = int(h * 0.68)
        x_start = (w - center_w) // 2
        y_start = (h - center_h) // 2
        
        center_mask = mask[y_start:y_start+center_h, x_start:x_start+center_w]
        orange_ratio = cv2.countNonZero(center_mask) / center_mask.size
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🟠 Idle check → Orange ratio: {orange_ratio:.2f} (needs > {idle_color_ratio:.2f})")
        return orange_ratio > idle_color_ratio
    
    def random_right_click_dismiss(self, geom, width, height):
        """Random right-click inside circle (diameter = 1/8 screen width)."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟠 ORANGE IDLE DETECTED → Random dismiss click...")
        
        center_x = geom['left'] + width // 2
        center_y = geom['top'] + height // 2
        
        radius = width / 16.0
        angle = random.uniform(0, 2 * math.pi)
        r = radius * math.sqrt(random.random())
        
        dx = int(r * math.cos(angle))
        dy = int(r * math.sin(angle))
        
        random_x = center_x + dx
        random_y = center_y + dy
        
        self.input.click_at(random_x, random_y, button='right')
        time.sleep(1.8)
    
    def click_exit_button(self, geom, vision):
        """Shared exit button click – called by banking actions."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📸 Taking screenshot for Exit button...")
        with mss() as sct:
            screenshot = sct.grab(geom)
            img_pil = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
        exit_positions = vision.find_exit_button(img_bgr)
        if exit_positions:
            rel_x, rel_y = exit_positions[0]
            abs_x = geom['left'] + rel_x
            abs_y = geom['top'] + rel_y
            self.input.click_at(abs_x, abs_y, button='left')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🏦 Exit button clicked!")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Exit button not found – continuing anyway")