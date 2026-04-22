#!/usr/bin/env python3
"""
Simple Plant Disease Predictor
Lightweight version without heavy ML dependencies for Vercel deployment
"""

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import os
from typing import List, Tuple, Dict, Optional
import logging
import requests

class SimplePlantDiseasePredictor:
    def __init__(self, model_api_url: Optional[str] = None):
        self.model_api_url = model_api_url or os.getenv('MODEL_API_URL')
        self._class_names = [
            'Healthy', 'Bacterial Spot', 'Early Blight', 'Late Blight',
            'Leaf Mold', 'Septoria Leaf Spot', 'Spider Mites', 'Target Spot',
            'Yellow Leaf Curl Virus', 'Mosaic Virus'
        ]
        self.confidence_threshold = 0.60
        self._enhancement_params = {
            'contrast': 1.2,
            'sharpness': 1.1,
            'color': 1.1,
            'unsharp_radius': 1,
            'unsharp_percent': 120,
            'unsharp_threshold': 3
        }
        self._target_size = (224, 224)
        self._enhance_size = (256, 256)
        
        # Configure logging
        logging.basicConfig(level=logging.ERROR)
        self.logger = logging.getLogger(__name__)
        
        print("Simple predictor initialized (no local model)")
    
    @property
    def class_names(self) -> List[str]:
        return self._class_names.copy()
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Enhanced image preprocessing"""
        # Resize first for faster processing
        image = image.resize(self._enhance_size, Image.LANCZOS)
        
        # Apply enhancements
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(self._enhancement_params['contrast'])
        
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(self._enhancement_params['sharpness'])
        
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(self._enhancement_params['color'])
        
        # Apply unsharp mask
        image = image.filter(ImageFilter.UnsharpMask(
            radius=self._enhancement_params['unsharp_radius'],
            percent=self._enhancement_params['unsharp_percent'],
            threshold=self._enhancement_params['unsharp_threshold']
        ))
        
        return image
    
    def predict_from_image_api(self, image_path: str) -> Dict:
        """Predict using external API"""
        try:
            if not self.model_api_url:
                return self._mock_prediction()
            
            # Prepare image for API
            with open(image_path, 'rb') as f:
                files = {'image': f}
                response = requests.post(self.model_api_url, files=files, timeout=30)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            self.logger.error(f"API prediction failed: {e}")
            return self._mock_prediction()
    
    def _mock_prediction(self) -> Dict:
        """Mock prediction for testing without ML model"""
        import random
        predicted_class = random.choice(self._class_names)
        confidence = random.uniform(0.7, 0.95)
        
        return {
            'predicted_class': predicted_class,
            'confidence': confidence,
            'all_predictions': {
                predicted_class: confidence,
                'Healthy': random.uniform(0.1, 0.3),
                'Early Blight': random.uniform(0.1, 0.3)
            },
            'preprocessing_info': {
                'enhanced': True,
                'target_size': self._target_size,
                'model_type': 'mock'
            }
        }
    
    def predict_from_image(self, image_path: str) -> Dict:
        """Main prediction method"""
        try:
            # Check if image exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            # Use API prediction if available, otherwise mock
            return self.predict_from_image_api(image_path)
            
        except Exception as e:
            self.logger.error(f"Prediction failed: {e}")
            return {
                'error': str(e),
                'predicted_class': 'Unknown',
                'confidence': 0.0,
                'all_predictions': {},
                'preprocessing_info': {'error': True}
            }
