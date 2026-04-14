import tkinter as tk
from tkinter import messagebox
import subprocess
import time
import threading
import random
from mss import mss
from PIL import Image
import keyboard
import cv2
import numpy as np
import os
from datetime import datetime

class OSRSBot:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Zezimax: Next-Gen Visual Imaging Bot (OpenCV Edition)")
        self.root.geometry("640x540")
        self.root.resizable(False, False)
        
        self.window_id = None
        self.running = False
        self.bot_thread = None
        
        # TUNABLE: Chopping cooldown
        self.last_tree_click_time = 0
        self.chopping_cooldown_seconds = 420
        
        # Template folders + single buttons
        self.tree_templates = self.load_templates('templates/trees')
        self.empty_slot_templates = self.load_templates('templates/empty_slots')
        self.bank_templates = self.load_templates('templates/bank')
        self.bank_deposit_template = self.load_single_template('templates/misc/bank_deposit_inventory.png')
        self.bank_exit_template = self.load_single_template('templates/misc/exit.png')
        
        print(f"✅ Loaded {len(self.tree_templates)} tree marker templates.")
        print(f"✅ Loaded {len(self.empty_slot_templates)} empty slot templates.")
        print(f"✅ Loaded {len(self.bank_templates)} bank marker templates.")
        if self.bank_deposit_template is not None:
            print("✅ Bank deposit button template loaded successfully.")
        if self.bank_exit_template is not None:
            print("✅ Bank exit button template loaded successfully.")
        else:
            print("❌ Bank exit template MISSING – create templates/misc/exit.png")
        
        # GUI Elements
        tk.Label(self.root, text="Zezimax Bot", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(self.root, text="Tree markers + Longer cooldown + Slower polling (~2.5s)\n"
                                 "+ CLEAN screenshot inventory/bank checks + .png debug\n"
                                 "+ Deposit → random 1-2s → click Exit button → random 1-2s → resume trees\n"
                                 "+ FIXED: cooldown reset after full deposit+exit flow", 
                 font=("Arial", 9), justify="center").pack(pady=5)
        
        self.select_btn = tk.Button(self.root, text="Select RuneLite Window", command=self.select_window, width=35, height=2)
        self.select_btn.pack(pady=8)
        
        self.start_btn = tk.Button(self.root, text="Start Woodcutting Bot (F11)", command=self.start_bot, width=35, height=2)
        self.start_btn.pack(pady=8)
        
        self.stop_btn = tk.Button(self.root, text="Stop Bot (F12)", command=self.stop_bot, width=35, height=2)
        self.stop_btn.pack(pady=8)
        
        try:
            keyboard.add_hotkey('f11', self.start_bot)
            keyboard.add_hotkey('f12', self.stop_bot)
        except Exception as e:
            print(f"Warning: Could not register global hotkeys: {e}")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def load_templates(self, folder):
        templates = []
        if not os.path.exists(folder):
            print(f"⚠️  Folder '{folder}' not found – create it and drop cropped template images!")
            return templates
        for filename in sorted(os.listdir(folder)):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                path = os.path.join(folder, filename)
                template = cv2.imread(path, cv2.IMREAD_COLOR)
                if template is not None:
                    templates.append((template, filename))
                    print(f"   Loaded template: {filename} ({template.shape[1]}x{template.shape[0]})")
        return templates
    
    def load_single_template(self, path):
        if not os.path.exists(path):
            print(f"⚠️  Template '{path}' not found – create the file!")
            return None
        template = cv2.imread(path, cv2.IMREAD_COLOR)
        if template is not None:
            print(f"   Loaded single template: {os.path.basename(path)} ({template.shape[1]}x{template.shape[0]})")
            return template
        print(f"❌ Failed to load template: {path}")
        return None
    
    def find_tree_markers(self, img_bgr):
        if not self.tree_templates:
            return []
        matches = []
        for template, _ in self.tree_templates:
            result = cv2.matchTemplate(img_bgr, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= 0.65)   # UPDATED THRESHOLD
            for pt in zip(*locations[::-1]):
                center_x = pt[0] + template.shape[1] // 2
                center_y = pt[1] + template.shape[0] // 2
                offset_x = random.randint(-7, 7)
                offset_y = random.randint(-7, 7)
                matches.append((center_x + offset_x, center_y + offset_y))
        return matches[:3]
    
    def find_empty_slots(self, img_bgr):
        if not self.empty_slot_templates:
            return []
        h, w = img_bgr.shape[:2]
        inv_left = int(w * 0.58)
        inv_top = int(h * 0.32)
        inv_right = w
        inv_bottom = h
        inv_roi = img_bgr[inv_top:inv_bottom, inv_left:inv_right]
        
        matches = []
        for template, filename in self.empty_slot_templates:
            result = cv2.matchTemplate(inv_roi, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= 0.97)   # UPDATED THRESHOLD
            num_matches = len(locations[0])
            print(f"   🔍 Empty-slot '{filename}': {num_matches} potential matches (threshold 0.97)")
            
            for pt in zip(*locations[::-1]):
                center_x = pt[0] + template.shape[1] // 2 + inv_left
                center_y = pt[1] + template.shape[0] // 2 + inv_top
                matches.append((center_x, center_y))
        
        print(f"   📊 Total empty slot candidates found: {len(matches)}")
        return matches
    
    def is_inventory_full(self, img_bgr):
        empty_slots = self.find_empty_slots(img_bgr)
        num_empty = len(empty_slots)
        if num_empty > 0:
            print(f"📦 Inventory check: {num_empty} empty slot(s) detected → NOT full")
            return False
        print("📦 Inventory check: NO empty slots detected → INVENTORY FULL!")
        return True
    
    def find_bank_markers(self, img_bgr):
        if not self.bank_templates:
            return []
        matches = []
        for template, filename in self.bank_templates:
            result = cv2.matchTemplate(img_bgr, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= 0.34)   # UPDATED THRESHOLD
            num_matches = len(locations[0])
            print(f"   🔍 Bank '{filename}': {num_matches} potential matches")
            for pt in zip(*locations[::-1]):
                center_x = pt[0] + template.shape[1] // 2
                center_y = pt[1] + template.shape[0] // 2
                offset_x = random.randint(-8, 8)
                offset_y = random.randint(-8, 8)
                matches.append((center_x + offset_x, center_y + offset_y))
        print(f"   📊 Total bank markers found: {len(matches)}")
        return matches[:3]
    
    def find_deposit_button(self, img_bgr):
        if self.bank_deposit_template is None:
            return []
        result = cv2.matchTemplate(img_bgr, self.bank_deposit_template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.85)
        matches = []
        for pt in zip(*locations[::-1]):
            center_x = pt[0] + self.bank_deposit_template.shape[1] // 2
            center_y = pt[1] + self.bank_deposit_template.shape[0] // 2
            matches.append((center_x, center_y))
        print(f"   🔍 Deposit button: {len(matches)} potential matches (threshold 0.85)")
        return matches[:1]
    
    def find_exit_button(self, img_bgr):
        if self.bank_exit_template is None:
            return []
        result = cv2.matchTemplate(img_bgr, self.bank_exit_template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.85)
        matches = []
        for pt in zip(*locations[::-1]):
            center_x = pt[0] + self.bank_exit_template.shape[1] // 2
            center_y = pt[1] + self.bank_exit_template.shape[0] // 2
            matches.append((center_x, center_y))
        print(f"   🔍 Exit button: {len(matches)} potential matches (threshold 0.85)")
        return matches[:1]
    
    def detect_idle_orange(self, img_bgr):
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
    
    def click_at(self, abs_x, abs_y, button='left'):
        self.activate_window()
        subprocess.call(['xdotool', 'mousemove', str(abs_x), str(abs_y)])
        time.sleep(0.08)
        subprocess.call(['xdotool', 'click', '1' if button == 'left' else '3'])
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🖱️  {button.upper()} click at ({abs_x}, {abs_y})")
    
    def select_window(self):
        if self.running:
            messagebox.showwarning("Operation in Progress", "Stop the bot first.")
            return
        try:
            output = subprocess.check_output(['xdotool', 'selectwindow'], stderr=subprocess.STDOUT).decode('utf-8').strip()
            self.window_id = output
            messagebox.showinfo("Window Selected", f"RuneLite window selected!\nID: {self.window_id}")
            self.activate_window()
        except Exception as e:
            messagebox.showerror("Selection Error", f"Failed:\n{e}")
    
    def get_window_geometry(self):
        if not self.window_id:
            return None
        try:
            output = subprocess.check_output(['xdotool', 'getwindowgeometry', self.window_id]).decode('utf-8')
            lines = output.splitlines()
            pos_line = next((line for line in lines if 'Position:' in line), None)
            geo_line = next((line for line in lines if 'Geometry:' in line), None)
            if pos_line and geo_line:
                pos_str = pos_line.split(':', 1)[1].strip().split(',')[0:2]
                x = int(pos_str[0].strip())
                y = int(pos_str[1].split('(')[0].strip())
                geo_str = geo_line.split(':', 1)[1].strip().split('x')
                width = int(geo_str[0])
                height = int(geo_str[1])
                return {'left': x, 'top': y, 'width': width, 'height': height}
        except Exception:
            return None
        return None
    
    def activate_window(self):
        if self.window_id:
            try:
                subprocess.call(['xdotool', 'windowactivate', '--sync', self.window_id])
                time.sleep(0.05)
            except:
                pass
    
    def start_bot(self):
        if not self.window_id:
            messagebox.showwarning("No Window", "Select your RuneLite window first!")
            return
        if self.running:
            return
        self.last_tree_click_time = 0
        self.running = True
        self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.bot_thread.start()
        print("🚀 Visual woodcutting bot started (fresh cooldown reset)!")
    
    def stop_bot(self):
        if self.running:
            self.running = False
            self.last_tree_click_time = 0
            print("🛑 Bot stop requested.")
    
    def handle_idle_state(self, geom, width, height, current_time):
        """Orange detected → dismiss → NEW clean screenshot → inventory + bank on clean image"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟠 ORANGE IDLE DETECTED → Dismissing first...")
        
        center_x = geom['left'] + width // 2
        center_y = geom['top'] + height // 2
        self.click_at(center_x, center_y, button='right')
        time.sleep(1.8)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📸 Taking NEW clean screenshot for inventory/bank checks...")
        with mss() as sct:
            screenshot = sct.grab(geom)
            img_pil = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            clean_img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
        if self.is_inventory_full(clean_img_bgr):
            bank_positions = self.find_bank_markers(clean_img_bgr)
            if bank_positions:
                rel_x, rel_y = random.choice(bank_positions)
                abs_x = geom['left'] + rel_x
                abs_y = geom['top'] + rel_y
                self.click_at(abs_x, abs_y, button='left')
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🏦 Purple bank marker clicked – starting bank deposit polling cycle...")
                
                # Start deposit flow (it will handle the final cooldown reset)
                self.perform_bank_deposit(geom)
                return   # <-- NO cooldown set here anymore
            
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Inventory full but no bank marker found!")
        
        # Not full → reset cooldown
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌲 Tree chopping finished – resetting cooldown")
        self.last_tree_click_time = 0
    
    # === Deposit → 1-2s → Exit → 1-2s → final cooldown reset ===
    def perform_bank_deposit(self, geom):
        if self.bank_deposit_template is None:
            print("⚠️ No deposit button template – skipping and resuming")
            self.last_tree_click_time = 0
            return
        
        print("🔄 Bank deposit polling started (max 15 attempts, 2-4s interval)...")
        for attempt in range(1, 16):
            with mss() as sct:
                screenshot = sct.grab(geom)
                img_pil = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
            
            deposit_positions = self.find_deposit_button(img_bgr)
            if deposit_positions:
                rel_x, rel_y = deposit_positions[0]
                abs_x = geom['left'] + rel_x
                abs_y = geom['top'] + rel_y
                self.click_at(abs_x, abs_y, button='left')
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🏦 Deposit Inventory button clicked!")
                
                pause1 = random.uniform(1.0, 2.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Pausing {pause1:.1f}s before clicking Exit button...")
                time.sleep(pause1)
                
                self.click_exit_button(geom)
                
                pause2 = random.uniform(1.0, 2.0)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Pausing {pause2:.1f}s before resuming woodcutting...")
                time.sleep(pause2)
                
                self.last_tree_click_time = 0
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌲 Bank deposit + exit complete – cooldown reset, resuming tree search")
                return
            
            print(f"   Attempt {attempt}/15 – deposit button not found yet...")
            time.sleep(random.uniform(2.0, 4.0))
        
        print("⚠️ Max 15 deposit attempts reached – resuming chopping anyway")
        self.last_tree_click_time = 0
    
    def click_exit_button(self, geom):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 📸 Taking screenshot for Exit button...")
        with mss() as sct:
            screenshot = sct.grab(geom)
            img_pil = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
        exit_positions = self.find_exit_button(img_bgr)
        if exit_positions:
            rel_x, rel_y = exit_positions[0]
            abs_x = geom['left'] + rel_x
            abs_y = geom['top'] + rel_y
            self.click_at(abs_x, abs_y, button='left')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🏦 Exit button clicked!")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Exit button not found – continuing anyway")
    
    def bot_loop(self):
        print("🔄 Visual woodcutting loop active (Deposit → Exit → tree search flow)...")
        
        while self.running:
            self.activate_window()
            geom = self.get_window_geometry()
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
                    self.handle_idle_state(geom, width, height, current_time)
                    continue
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Still chopping (cooldown active)...")
                    time.sleep(random.uniform(2.2, 2.8))
                    continue
            
            if self.detect_idle_orange(img_bgr):
                self.handle_idle_state(geom, width, height, current_time)
                continue
            
            tree_positions = self.find_tree_markers(img_bgr)
            if tree_positions:
                rel_x, rel_y = random.choice(tree_positions)
                abs_x = geom['left'] + rel_x
                abs_y = geom['top'] + rel_y
                self.click_at(abs_x, abs_y, button='left')
                self.last_tree_click_time = current_time
                jitter = random.uniform(0, 4)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌳 Tree marker clicked – entering {self.chopping_cooldown_seconds + jitter:.1f}s cooldown")
                time.sleep(1.2)
                continue
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ No tree markers or orange idle – retrying in 2s")
            time.sleep(2.0)
        
        print("🛑 Bot loop ended.")
    
    def on_closing(self):
        self.stop_bot()
        self.root.destroy()

if __name__ == "__main__":
    print("🚀 Launching Next-Gen OSRS Visual Bot (Deposit → Exit → tree search flow)...")
    print("📁 Required folders/files:")
    print("   • templates/trees/")
    print("   • templates/empty_slots/")
    print("   • templates/bank/")
    print("   • templates/misc/bank_deposit_inventory.png")
    print("   • templates/misc/exit.png")
    bot = OSRSBot()