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
        self.root.geometry("520x370")
        self.root.resizable(False, False)
        
        self.window_id = None
        self.running = False
        self.bot_thread = None
        
        # TUNABLE: Chopping cooldown – increased to 600s + random jitter
        self.last_tree_click_time = 0
        self.chopping_cooldown_seconds = 420 # Can take a few mins
        
        # Template folders
        self.tree_templates = self.load_templates('templates/trees')
        # self.tree_templates = self.load_templates('templates/trees/default')
        
        print(f"✅ Loaded {len(self.tree_templates)} tree marker templates.")
        print("   (Blue/red outlined circles only – crop tightly!)")
        
        # GUI Elements
        tk.Label(self.root, text="Zezimax Bot", font=("Arial", 14, "bold")).pack(pady=15)
        tk.Label(self.root, text="Tree markers + Longer cooldown + Slower polling (every ~2.5s)", font=("Arial", 9)).pack(pady=5)
        
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
            print(f"⚠️  Folder '{folder}' not found – create it and drop cropped blue/red circle images!")
            return templates
        for filename in os.listdir(folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                path = os.path.join(folder, filename)
                template = cv2.imread(path, cv2.IMREAD_COLOR)
                if template is not None:
                    templates.append(template)
                    print(f"   Loaded template: {filename} ({template.shape[1]}x{template.shape[0]})")
        return templates
    
    def find_tree_markers(self, img_bgr):
        if not self.tree_templates:
            return []
        matches = []
        for template in self.tree_templates:
            result = cv2.matchTemplate(img_bgr, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= 0.78)
            for pt in zip(*locations[::-1]):
                center_x = pt[0] + template.shape[1] // 2
                center_y = pt[1] + template.shape[0] // 2
                offset_x = random.randint(-7, 7)
                offset_y = random.randint(-7, 7)
                matches.append((center_x + offset_x, center_y + offset_y))
        return matches[:3]
    
    def detect_idle_orange(self, img_bgr):
        idle_color_ratio = 0.67 # Set the orange needed for screen to be considered "idle"
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
        print(f"[{timestamp}] 🟠 Idle check → Orange ratio in center viewport: {orange_ratio:.2f} (needs > {idle_color_ratio:.2f})")
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
        self.running = True
        self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
        self.bot_thread.start()
        print("🚀 Visual woodcutting bot started – longer cooldown + slower polling!")
    
    def stop_bot(self):
        if self.running:
            self.running = False
            print("🛑 Bot stop requested.")
    
    def bot_loop(self):
        print("🔄 Visual woodcutting loop active (28s cooldown + ~2.5s polling)...")
        
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
            
            # === CHOPPING COOLDOWN (prevents clicking new trees while one is still being chopped) ===
            in_chopping_cooldown = (current_time - self.last_tree_click_time) < self.chopping_cooldown_seconds
            
            if in_chopping_cooldown:
                if self.detect_idle_orange(img_bgr):
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟠 ORANGE IDLE DETECTED – dismissing!")
                    center_x = geom['left'] + width // 2
                    center_y = geom['top'] + height // 2
                    self.click_at(center_x, center_y, button='right')
                    self.last_tree_click_time = 0
                    time.sleep(1.2)
                    continue
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Still chopping (cooldown active)...")
                    time.sleep(random.uniform(2.2, 2.8))   # ← Slower polling as requested (~2.5s)
                    continue
            
            # Not in cooldown → check for orange first, then look for trees
            if self.detect_idle_orange(img_bgr):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟠 ORANGE IDLE DETECTED – dismissing!")
                center_x = geom['left'] + width // 2
                center_y = geom['top'] + height // 2
                self.click_at(center_x, center_y, button='right')
                time.sleep(1.2)
                continue
            
            # Look for new trees
            tree_positions = self.find_tree_markers(img_bgr)
            if tree_positions:
                rel_x, rel_y = random.choice(tree_positions)
                abs_x = geom['left'] + rel_x
                abs_y = geom['top'] + rel_y
                self.click_at(abs_x, abs_y, button='left')
                self.last_tree_click_time = current_time
                # Add tiny random jitter to cooldown so it doesn't always fire at exactly N seconds
                jitter = random.uniform(0, 4)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🌳 Tree marker clicked – entering {self.chopping_cooldown_seconds + jitter:.1f}s chopping cooldown")
                time.sleep(1.2)
                continue
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ No tree markers or orange idle – retrying in 2s")
            time.sleep(2.0)
        
        print("🛑 Bot loop ended.")
    
    def on_closing(self):
        self.stop_bot()
        self.root.destroy()

if __name__ == "__main__":
    print("🚀 Launching Next-Gen OSRS Visual Bot (longer cooldown + slower polling)...")
    print("📁 templates/trees/ should contain your 12 cropped markers.")
    bot = OSRSBot()