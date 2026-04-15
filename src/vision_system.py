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
        # Inventory ROI (bottom-right panel)
        inv_left = int(w * 0.58)
        inv_top = int(h * 0.32)
        inv_right = w
        inv_bottom = h
        inv_roi = img_bgr[inv_top:inv_bottom, inv_left:inv_right]
        
        matches = []
        for template, filename in self.templates.empty_slot_templates:
            result = cv2.matchTemplate(inv_roi, template, cv2.TM_CCOEFF_NORMED)
            
            # NEW: Get the BEST match ratio for this template (exactly like orange idle)
            best_ratio = float(result.max()) if result.size > 0 else 0.0
            
            # Count how many locations are above threshold
            locations = np.where(result >= 0.97)
            num_matches = len(locations[0])
            
            # Improved debug output with ratio (same style as idle check)
            print(f"   🔍 Empty-slot '{filename}': best ratio {best_ratio:.4f} "
                  f"(threshold 0.97) → {num_matches} matches")
            
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
        best_overall_ratio = 0.0
        best_location = None
        
        for template, filename in self.templates.bank_templates:
            result = cv2.matchTemplate(img_bgr, template, cv2.TM_CCOEFF_NORMED)
            
            # Best match ratio for this template (same style as empty slots + idle)
            best_ratio_this_template = float(result.max()) if result.size > 0 else 0.0
            
            locations = np.where(result >= 0.55)
            num_matches = len(locations[0])
            
            print(f"   🔍 Bank '{filename}': best ratio {best_ratio_this_template:.4f} "
                  f"(threshold 0.55) → {num_matches} matches")
            
            # Track the single strongest match across all templates
            if best_ratio_this_template > best_overall_ratio:
                best_overall_ratio = best_ratio_this_template
                y, x = np.unravel_index(result.argmax(), result.shape)
                best_location = (x + template.shape[1] // 2, y + template.shape[0] // 2)
        
        # If we found at least one good match, use the best one(s)
        if best_location:
            # Add the single best match with random offset
            offset_x = random.randint(-8, 8)
            offset_y = random.randint(-8, 8)
            matches.append((best_location[0] + offset_x, best_location[1] + offset_y))
            
            print(f"   📊 Best bank marker overall ratio: {best_overall_ratio:.4f}")
        
        print(f"   📊 Total bank markers found: {len(matches)}")
        return matches[:3]   # Still limit to 3 for safety
    
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
    
    # NEW: Special move detection (top 1/8 corner near minimap)
    def find_special_move(self, img_bgr):
        """Detect special move icon ONLY in the top 1/8 corner (minimap border area)."""
        if self.templates.special_move_template is None:
            return []
        
        h, w = img_bgr.shape[:2]
        # ROI = top ~1/8 of screen (slightly taller for safety) + right side (minimap area)
        roi_h = int(h * 0.125)          # exactly 1/8 height
        roi_w_start = int(w * 0.68)     # start from ~68% width (far right corner)
        
        roi = img_bgr[0:roi_h, roi_w_start:w]
        
        result = cv2.matchTemplate(roi, self.templates.special_move_template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.95)
        
        matches = []
        for pt in zip(*locations[::-1]):
            # Convert ROI coords back to full-screen coords
            center_x = pt[0] + self.templates.special_move_template.shape[1] // 2 + roi_w_start
            center_y = pt[1] + self.templates.special_move_template.shape[0] // 2
            matches.append((center_x, center_y))
        
        if matches:
            print(f"   ⚔️ Special move icon found at threshold 0.95! ({len(matches)} match)")
        else:
            print(f"   ⚔️ No special move icon in top 1/8 corner (threshold 0.95)")
        
        return matches[:1]