import cv2
import numpy as np
import random

class VisionSystem:
    """All computer-vision detection logic (template matching)."""
    
    def __init__(self, templates):
        self.templates = templates
    
    def find_tree_markers(self, img_bgr):
        if not self.templates.tree_templates:
            return []
        matches = []
        for template, _ in self.templates.tree_templates:
            result = cv2.matchTemplate(img_bgr, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= 0.65)
            for pt in zip(*locations[::-1]):
                center_x = pt[0] + template.shape[1] // 2
                center_y = pt[1] + template.shape[0] // 2
                offset_x = random.randint(-7, 7)
                offset_y = random.randint(-7, 7)
                matches.append((center_x + offset_x, center_y + offset_y))
        return matches[:3]
    
    def find_empty_slots(self, img_bgr):
        if not self.templates.empty_slot_templates:
            return []
        h, w = img_bgr.shape[:2]
        inv_left = int(w * 0.58)
        inv_top = int(h * 0.32)
        inv_right = w
        inv_bottom = h
        inv_roi = img_bgr[inv_top:inv_bottom, inv_left:inv_right]
        
        matches = []
        for template, filename in self.templates.empty_slot_templates:
            result = cv2.matchTemplate(inv_roi, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= 0.97)
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
        if not self.templates.bank_templates:
            return []
        matches = []
        for template, filename in self.templates.bank_templates:
            result = cv2.matchTemplate(img_bgr, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= 0.55)
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
        if self.templates.bank_deposit_template is None:
            return []
        result = cv2.matchTemplate(img_bgr, self.templates.bank_deposit_template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.85)
        matches = []
        for pt in zip(*locations[::-1]):
            center_x = pt[0] + self.templates.bank_deposit_template.shape[1] // 2
            center_y = pt[1] + self.templates.bank_deposit_template.shape[0] // 2
            matches.append((center_x, center_y))
        print(f"   🔍 Deposit button: {len(matches)} potential matches (threshold 0.85)")
        return matches[:1]
    
    def find_exit_button(self, img_bgr):
        if self.templates.bank_exit_template is None:
            return []
        result = cv2.matchTemplate(img_bgr, self.templates.bank_exit_template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.85)
        matches = []
        for pt in zip(*locations[::-1]):
            center_x = pt[0] + self.templates.bank_exit_template.shape[1] // 2
            center_y = pt[1] + self.templates.bank_exit_template.shape[0] // 2
            matches.append((center_x, center_y))
        print(f"   🔍 Exit button: {len(matches)} potential matches (threshold 0.85)")
        return matches[:1]