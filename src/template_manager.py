import os
import cv2

class TemplateManager:
    """Handles loading and storing all template images."""
    
    def __init__(self):
        self.tree_templates = self._load_templates('templates/trees')
        self.empty_slot_templates = self._load_templates('templates/empty_slots')
        self.bank_templates = self._load_templates('templates/bank')
        self.bank_deposit_template = self._load_single_template('templates/misc/bank_deposit_inventory.png')
        self.bank_exit_template = self._load_single_template('templates/misc/exit.png')
        
        print(f"✅ Loaded {len(self.tree_templates)} tree marker templates.")
        print(f"✅ Loaded {len(self.empty_slot_templates)} empty slot templates.")
        print(f"✅ Loaded {len(self.bank_templates)} bank marker templates.")
        if self.bank_deposit_template is not None:
            print("✅ Bank deposit button template loaded successfully.")
        if self.bank_exit_template is not None:
            print("✅ Bank exit button template loaded successfully.")
        else:
            print("❌ Bank exit template MISSING – create templates/misc/exit.png")
    
    def _load_templates(self, folder):
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
    
    def _load_single_template(self, path):
        if not os.path.exists(path):
            print(f"⚠️  Template '{path}' not found – create the file!")
            return None
        template = cv2.imread(path, cv2.IMREAD_COLOR)
        if template is not None:
            print(f"   Loaded single template: {os.path.basename(path)} ({template.shape[1]}x{template.shape[0]})")
            return template
        print(f"❌ Failed to load template: {path}")
        return None