import random
import time
import numpy as np
from mss import mss
from PIL import Image
import cv2
from datetime import datetime


class BankingActions:
    """Dedicated banking logic (deposit polling + exit button)."""
    
    def __init__(self, input_controller, vision, shared_actions):
        self.input = input_controller
        self.vision = vision
        self.shared = shared_actions   # SharedSkillActions instance
    
    def perform_bank_deposit(self, geom):
        if self.vision.templates.bank_deposit_template is None:
            print("⚠️ No deposit button template – skipping and resuming")
            return False
        
        print("🔄 Bank deposit polling started (max 15 attempts, 2-4s interval)...")
        for attempt in range(1, 16):
            with mss() as sct:
                screenshot = sct.grab(geom)
                img_pil = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            
            deposit_positions = self.vision.find_deposit_button(img_bgr)
            if deposit_positions:
                rel_x, rel_y = deposit_positions[0]
                abs_x = geom['left'] + rel_x
                abs_y = geom['top'] + rel_y
                self.input.click_at(abs_x, abs_y, button='left')
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🏦 Deposit Inventory button clicked!")
                
                pause1 = random.uniform(1.0, 2.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Pausing {pause1:.1f}s before clicking Exit button...")
                time.sleep(pause1)
                
                # Call shared exit button
                self.shared.click_exit_button(geom, self.vision)
                
                pause2 = random.uniform(1.0, 2.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Pausing {pause2:.1f}s before resuming woodcutting...")
                time.sleep(pause2)
                
                return True
            
            print(f"   Attempt {attempt}/15 – deposit button not found yet...")
            time.sleep(random.uniform(2.0, 4.0))
        
        print("⚠️ Max 15 deposit attempts reached – resuming chopping anyway")
        return False