import subprocess
import time
from datetime import datetime

class InputController:
    """Handles all mouse/keyboard interaction and window management."""
    
    def __init__(self):
        self.window_id = None
    
    def click_at(self, abs_x, abs_y, button='left'):
        self.activate_window()
        subprocess.call(['xdotool', 'mousemove', str(abs_x), str(abs_y)])
        time.sleep(0.08)
        subprocess.call(['xdotool', 'click', '1' if button == 'left' else '3'])
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🖱️  {button.upper()} click at ({abs_x}, {abs_y})")
    
    def select_window(self):
        """Selects the RuneLite window (now silent – success message handled in GUI)."""
        try:
            output = subprocess.check_output(['xdotool', 'selectwindow'], stderr=subprocess.STDOUT).decode('utf-8').strip()
            self.window_id = output
            self.activate_window()
            return True
        except Exception as e:
            print(f"❌ Window selection failed: {e}")
            return False
    
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