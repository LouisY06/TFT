import cv2
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class ChampionDetector:
    """Detects TFT champions using template matching and OCR."""
    
    def __init__(self):
        self.champion_templates = {}
        self.trait_templates = {}
        self.cost_colors = {
            1: [(169, 169, 169), (192, 192, 192)],  # Gray for 1-cost
            2: [(0, 128, 0), (50, 205, 50)],        # Green for 2-cost  
            3: [(0, 0, 255), (65, 105, 225)],       # Blue for 3-cost
            4: [(128, 0, 128), (186, 85, 211)],     # Purple for 4-cost
            5: [(255, 215, 0), (255, 255, 0)],      # Gold for 5-cost
        }
        self.load_templates()
    
    def load_templates(self):
        """Load champion and trait template images."""
        template_dir = Path("champ_templates")
        
        if template_dir.exists():
            for template_file in template_dir.glob("*.png"):
                template = cv2.imread(str(template_file), cv2.IMREAD_COLOR)
                if template is not None:
                    champion_name = template_file.stem
                    self.champion_templates[champion_name] = template
                    logger.debug(f"Loaded template for {champion_name}")
            
            logger.info(f"Loaded {len(self.champion_templates)} champion templates")
        else:
            logger.warning(f"Template directory {template_dir} not found")
    
    def detect_champion_by_template(self, image: np.ndarray, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Detect champions using template matching.
        
        Args:
            image: Input image to search
            threshold: Matching confidence threshold
            
        Returns:
            List of detected champions with positions and confidence
        """
        detections = []
        
        if not self.champion_templates:
            logger.warning("No champion templates loaded")
            return detections
        
        # Convert to grayscale for template matching
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        for champion_name, template in self.champion_templates.items():
            try:
                # Convert template to grayscale
                gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                
                # Perform template matching
                result = cv2.matchTemplate(gray_image, gray_template, cv2.TM_CCOEFF_NORMED)
                locations = np.where(result >= threshold)
                
                # Get template dimensions
                h, w = gray_template.shape
                
                # Process matches
                for pt in zip(*locations[::-1]):  # Switch x and y
                    confidence = result[pt[1], pt[0]]
                    
                    detection = {
                        'name': champion_name,
                        'position': pt,
                        'size': (w, h),
                        'confidence': float(confidence),
                        'bounding_box': (pt[0], pt[1], pt[0] + w, pt[1] + h)
                    }
                    detections.append(detection)
                    
            except Exception as e:
                logger.error(f"Error matching template for {champion_name}: {e}")
        
        # Sort by confidence and remove overlapping detections
        detections = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        detections = self._remove_overlapping_detections(detections)
        
        logger.info(f"Detected {len(detections)} champions via template matching")
        return detections
    
    def _remove_overlapping_detections(self, detections: List[Dict[str, Any]], overlap_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Remove overlapping detections to avoid duplicates."""
        if not detections:
            return detections
        
        filtered = []
        
        for detection in detections:
            is_overlap = False
            x1, y1, x2, y2 = detection['bounding_box']
            
            for existing in filtered:
                ex1, ey1, ex2, ey2 = existing['bounding_box']
                
                # Calculate intersection over union (IoU)
                intersection_area = max(0, min(x2, ex2) - max(x1, ex1)) * max(0, min(y2, ey2) - max(y1, ey1))
                union_area = (x2 - x1) * (y2 - y1) + (ex2 - ex1) * (ey2 - ey1) - intersection_area
                
                if union_area > 0:
                    iou = intersection_area / union_area
                    if iou > overlap_threshold:
                        is_overlap = True
                        break
            
            if not is_overlap:
                filtered.append(detection)
        
        return filtered
    
    def detect_champion_cost_by_color(self, champion_image: np.ndarray) -> Optional[int]:
        """Detect champion cost by analyzing border/background color.
        
        Args:
            champion_image: Cropped image of a single champion
            
        Returns:
            Detected cost (1-5) or None if uncertain
        """
        if champion_image is None or champion_image.size == 0:
            return None
        
        try:
            # Sample colors from the border area
            h, w = champion_image.shape[:2]
            
            # Sample from top, bottom, left, right borders
            border_pixels = []
            border_thickness = max(1, min(h, w) // 10)
            
            # Top and bottom borders
            border_pixels.extend(champion_image[:border_thickness, :].reshape(-1, 3))
            border_pixels.extend(champion_image[-border_thickness:, :].reshape(-1, 3))
            
            # Left and right borders
            border_pixels.extend(champion_image[:, :border_thickness].reshape(-1, 3))
            border_pixels.extend(champion_image[:, -border_thickness:].reshape(-1, 3))
            
            border_pixels = np.array(border_pixels)
            
            # Find the most common color
            avg_color = np.mean(border_pixels, axis=0)
            
            # Compare with known cost colors
            best_match_cost = None
            best_match_distance = float('inf')
            
            for cost, color_range in self.cost_colors.items():
                for color in color_range:
                    distance = np.linalg.norm(avg_color - np.array(color))
                    if distance < best_match_distance:
                        best_match_distance = distance
                        best_match_cost = cost
            
            # Only return if the match is reasonably confident
            if best_match_distance < 100:  # Threshold for color similarity
                return best_match_cost
            
        except Exception as e:
            logger.error(f"Error detecting champion cost by color: {e}")
        
        return None
    
    def detect_text_in_region(self, image: np.ndarray, region_type: str = "general") -> str:
        """Detect text in an image region using OCR.
        
        Args:
            image: Input image
            region_type: Type of region (gold, level, etc.) for OCR optimization
            
        Returns:
            Detected text string
        """
        try:
            import pytesseract
            from PIL import Image
            
            # Preprocess image for better OCR
            processed = self._preprocess_for_ocr(image, region_type)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(cv2.cvtColor(processed, cv2.COLOR_BGR2RGB))
            
            # Configure OCR based on region type
            if region_type in ['gold', 'level', 'health']:
                # Numbers only
                config = '--psm 7 -c tessedit_char_whitelist=0123456789'
            elif region_type == 'round':
                # Numbers and dash for rounds like "2-1"
                config = '--psm 7 -c tessedit_char_whitelist=0123456789-'
            else:
                # General text
                config = '--psm 6'
            
            text = pytesseract.image_to_string(pil_image, config=config)
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error detecting text in {region_type} region: {e}")
            return ""
    
    def _preprocess_for_ocr(self, image: np.ndarray, region_type: str) -> np.ndarray:
        """Preprocess image for better OCR results."""
        if image is None:
            return image
        
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Apply different preprocessing based on region type
            if region_type in ['gold', 'level', 'health']:
                # For numeric regions: threshold to get white text on black background
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # Invert if needed (OCR works better with black text on white)
                if np.mean(binary) < 127:
                    binary = cv2.bitwise_not(binary)
                
                # Scale up for better recognition
                scale_factor = 3
                scaled = cv2.resize(binary, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
                
                return cv2.cvtColor(scaled, cv2.COLOR_GRAY2BGR)
            
            else:
                # For general text: denoise and enhance contrast
                denoised = cv2.medianBlur(gray, 3)
                
                # Enhance contrast
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                enhanced = clahe.apply(denoised)
                
                return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
                
        except Exception as e:
            logger.error(f"Error preprocessing image for OCR: {e}")
            return image
    
    def analyze_shop_slots(self, shop_image: np.ndarray) -> List[Dict[str, Any]]:
        """Analyze individual shop slots for champions and costs.
        
        Args:
            shop_image: Image of the shop area
            
        Returns:
            List of shop slot analyses
        """
        if shop_image is None:
            return []
        
        slots = []
        
        try:
            # TFT shop typically has 5 slots
            slot_count = 5
            shop_width = shop_image.shape[1]
            slot_width = shop_width // slot_count
            
            for i in range(slot_count):
                # Extract individual slot
                x_start = i * slot_width
                x_end = (i + 1) * slot_width
                slot_image = shop_image[:, x_start:x_end]
                
                if slot_image.size == 0:
                    continue
                
                # Analyze this slot
                slot_analysis = {
                    'slot_index': i,
                    'champion_name': 'unknown',
                    'cost': None,
                    'confidence': 0.0
                }
                
                # Try template matching on this slot
                detections = self.detect_champion_by_template(slot_image, threshold=0.7)
                
                if detections:
                    best_detection = detections[0]  # Highest confidence
                    slot_analysis['champion_name'] = best_detection['name']
                    slot_analysis['confidence'] = best_detection['confidence']
                
                # Try to detect cost by color
                cost = self.detect_champion_cost_by_color(slot_image)
                if cost:
                    slot_analysis['cost'] = cost
                
                slots.append(slot_analysis)
                
        except Exception as e:
            logger.error(f"Error analyzing shop slots: {e}")
        
        return slots
    
    def get_champion_info(self, champion_name: str) -> Dict[str, Any]:
        """Get stored information about a champion.
        
        Args:
            champion_name: Name of the champion
            
        Returns:
            Champion information dictionary
        """
        try:
            # Load champion data
            champs_path = Path("data/champions.json")
            if champs_path.exists():
                with open(champs_path, 'r') as f:
                    champions_data = json.load(f)
                
                # Find matching champion (case-insensitive)
                for champ in champions_data:
                    if champ.get('name', '').lower() == champion_name.lower():
                        return champ
            
        except Exception as e:
            logger.error(f"Error getting champion info for {champion_name}: {e}")
        
        return {'name': champion_name, 'cost': 'unknown', 'traits': []}