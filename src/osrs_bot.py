import tkinter as tk
from tkinter import messagebox, ttk
import threading

from template_manager import TemplateManager
from vision_system import VisionSystem
from input_controller import InputController
from skills.woodcutting import WoodcuttingBot


class OSRSBot:
    """Pure GUI launcher – selects skill and starts the correct bot."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Zezimax: Next-Gen Visual Imaging Bot")
        self.root.geometry("640x580")  # Slightly taller for resolution options
        self.root.resizable(False, False)
        
        self.running = False
        self.bot_thread = None
        self.current_skill_bot = None
        
        # Shared components (created when window is selected)
        self.templates = None
        self.vision = None
        self.input = InputController()
        
        # GUI
        tk.Label(self.root, text="Zezimax Bot", font=("Arial", 16, "bold")).pack(pady=15)
        
        # Skill dropdown
        tk.Label(self.root, text="Select Skill:", font=("Arial", 10)).pack(pady=(10, 0))
        self.skill_var = tk.StringVar(value="Woodcutting")
        self.skill_dropdown = ttk.Combobox(
            self.root, textvariable=self.skill_var, state="readonly",
            values=["Fishing", "Mining", "Woodcutting"], width=25
        )
        self.skill_dropdown.pack(pady=5)
        
        # Resolution selection
        tk.Label(self.root, text="Resolution:", font=("Arial", 10)).pack(pady=(15, 0))
        
        res_frame = tk.Frame(self.root)
        res_frame.pack(pady=5)
        
        self.resolution_var = tk.StringVar(value="1080")
        tk.Radiobutton(res_frame, text="1080p", variable=self.resolution_var, 
                      value="1080", font=("Arial", 10)).pack(side=tk.LEFT, padx=20)
        tk.Radiobutton(res_frame, text="1440p", variable=self.resolution_var, 
                      value="1440", font=("Arial", 10)).pack(side=tk.LEFT, padx=20)
        
        self.select_btn = tk.Button(self.root, text="Select RuneLite Window", 
                                   command=self.select_window_and_load_templates, 
                                   width=35, height=2)
        self.select_btn.pack(pady=20)
        
        self.start_btn = tk.Button(self.root, text="Start Bot (F11)", command=self.start_bot, width=35, height=2)
        self.start_btn.pack(pady=8)
        
        self.stop_btn = tk.Button(self.root, text="Stop Bot (F12)", command=self.stop_bot, width=35, height=2)
        self.stop_btn.pack(pady=8)
        
        try:
            import keyboard
            keyboard.add_hotkey('f11', self.start_bot)
            keyboard.add_hotkey('f12', self.stop_bot)
        except Exception as e:
            print(f"Warning: Could not register global hotkeys: {e}")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def select_window_and_load_templates(self):
        """Select RuneLite window AND immediately load templates for the chosen resolution."""
        success = self.input.select_window()
        
        if success and self.input.window_id:
            selected_res = self.resolution_var.get()
            
            print(f"✅ RuneLite window selected successfully (ID: {self.input.window_id})")
            print(f"📸 Loading {selected_res}p templates and vision system...")
            
            self.templates = TemplateManager(resolution=selected_res)
            self.vision = VisionSystem(self.templates)
            
            # Combined success message (exactly what you asked for)
            messagebox.showinfo(
                "Success",
                f"✅ RuneLite window selected successfully!\n"
                f"Window ID: {self.input.window_id}\n\n"
                f"📸 Templates for {selected_res}p resolution have been loaded and are ready to use."
            )
        else:
            messagebox.showerror("Selection Failed", "Failed to select RuneLite window.")
    
    def start_bot(self):
        if not self.input.window_id:
            messagebox.showwarning("No Window", "Please click 'Select RuneLite Window' first!")
            return
        if not self.templates or not self.vision:
            messagebox.showwarning("Templates Not Loaded", 
                                  "Please select your RuneLite window again to load templates.")
            return
        if self.running:
            return
        
        selected_skill = self.skill_var.get()
        selected_res = self.resolution_var.get()
        
        print(f"🚀 Starting {selected_skill} bot at {selected_res}p resolution...")
        
        if selected_skill == "Woodcutting":
            self.current_skill_bot = WoodcuttingBot(self.vision, self.input, self.templates)
        else:
            messagebox.showinfo("Coming Soon", f"{selected_skill} support is not implemented yet.")
            return
        
        self.running = True
        self.bot_thread = threading.Thread(target=self.current_skill_bot.run, daemon=True)
        self.bot_thread.start()
    
    def stop_bot(self):
        if self.running and self.current_skill_bot:
            self.current_skill_bot.stop()
            self.running = False
            print("🛑 Bot stop requested.")
    
    def on_closing(self):
        self.stop_bot()
        self.root.destroy()


if __name__ == "__main__":
    print("🚀 Launching Zezimax Bot – Skill Selector GUI")
    OSRSBot()