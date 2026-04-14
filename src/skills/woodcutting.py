import random
import time
import numpy as np
from mss import mss
from PIL import Image
import cv2
from datetime import datetime

from .general import SharedSkillActions
from .banking import BankingActions


class WoodcuttingBot(SharedSkillActions):
    """Woodcutting-specific bot."""
    
    def __init__(self, vision, input_controller, templates):
        super().__init__(input_controller)
        self.vision = vision
        self.templates = templates
        self.banking = BankingActions(input_controller, vision, self)   # pass self (SharedSkillActions)
        
        self.running = False
        self.last_tree_click_time = 0
        self.chopping_cooldown_seconds = 420
    
    def run(self):
        self.running = True
        print("🔄 Woodcutting bot loop started (Deposit → Exit → tree search flow)...")
        
        while self.running:
            self.input.activate_window()
            geom = self.input.get_window_geometry()
            if not geom:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  Could not get window geometry. Retrying...")
                time.sleep(2)
                continue
            
            with mss() as sct:
                screenshot = sct.grab(geom)
                img_pil = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            
            width, height = img_bgr.shape[1], img_bgr.shape[0]
            current_time = time.time()
            
            in_chopping_cooldown = (current_time - self.last_tree_click_time) < self.chopping_cooldown_seconds
            
            if in_chopping_cooldown:
                if self.detect_idle_orange(img_bgr):
                    self._handle_idle_state(geom, width, height, current_time)
                    continue
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Still chopping (cooldown active)...")
                    time.sleep(random.uniform(2.2, 2.8))
                    continue
            
            if self.detect_idle_orange(img_bgr):
                self._handle_idle_state(geom, width, height, current_time)
                continue
            
            tree_positions = self.vision.find_tree_markers(img_bgr)
            if tree_positions:
                rel_x, rel_y = random.choice(tree_positions)
                abs_x = geom['left'] + rel_x
                abs_y = geom['top'] + rel_y
                self.input.click_at(abs_x, abs_y, button='left')
                self.last_tree_click_time = current_time
                jitter = random.uniform(0, 4)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌳 Tree marker clicked – entering {self.chopping_cooldown_seconds + jitter:.1f}s cooldown")
                time.sleep(1.2)
                continue
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ No tree markers or orange idle – retrying in 2s")
            time.sleep(2.0)
        
        print("🛑 Woodcutting bot loop ended.")
    
    def stop(self):
        self.running = False
    
    def _handle_idle_state(self, geom, width, height, current_time):
        self.random_right_click_dismiss(geom, width, height)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📸 Taking NEW clean screenshot for inventory/bank checks...")
        with mss() as sct:
            screenshot = sct.grab(geom)
            img_pil = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            clean_img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
        if self.vision.is_inventory_full(clean_img_bgr):
            bank_positions = self.vision.find_bank_markers(clean_img_bgr)
            if bank_positions:
                rel_x, rel_y = random.choice(bank_positions)
                abs_x = geom['left'] + rel_x
                abs_y = geom['top'] + rel_y
                self.input.click_at(abs_x, abs_y, button='left')
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🏦 Purple bank marker clicked – starting bank deposit polling cycle...")
                
                self.banking.perform_bank_deposit(geom)
                
                self.last_tree_click_time = 0
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌲 Bank deposit + exit complete – cooldown reset, resuming tree search")
                return
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌲 Tree chopping finished – resetting cooldown")
        self.last_tree_click_time = 0