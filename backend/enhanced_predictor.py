#!/usr/bin/env python3
"""
Enhanced Plant Disease Predictor
Advanced preprocessing and ensemble methods for better accuracy
"""

import tensorflow as tf
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import os
from typing import List, Tuple, Dict, Optional
import hashlib
from functools import lru_cache
import logging
from concurrent.futures import ThreadPoolExecutor
import time
import multiprocessing as mp

class EnhancedPlantDiseasePredictor:
    def __init__(self, model_path: str = "model.h5"):
        self.model_path = model_path
        self.model = None
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
        # Performance optimization: pre-allocate arrays
        self._target_size = (224, 224)  # Match trained model size
        self._enhance_size = (256, 256)
        self._kernel_size = (5, 5)
        self.num_workers = min(mp.cpu_count(), 4)  # Optimize for CPU cores
        
        # Configure logging
        logging.basicConfig(level=logging.ERROR)
        self.logger = logging.getLogger(__name__)
        
        # Pre-allocate numpy arrays for batch processing
        self._batch_buffer = np.zeros((1, 224, 224, 3), dtype=np.float32)
        
        self.load_model()
    
    @property
    def class_names(self) -> List[str]:
        return self._class_names.copy()
    
    def load_model(self) -> bool:
        """Load trained model"""
        if self.model is not None:
            return True
            
        try:
            if not os.path.exists(self.model_path):
                print("❌ Model file not found")
                return False
                
            self.model = tf.keras.models.load_model(self.model_path)
            print("✅ Enhanced model loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    @lru_cache(maxsize=128)
    def _get_enhancement_values(self) -> Dict[str, float]:
        """Cache enhancement parameters"""
        return self._enhancement_params.copy()
    
    def _enhance_image_optimized(self, image: Image.Image) -> Image.Image:
        """Optimized image enhancement with caching"""
        # Resize first for faster processing
        image = image.resize(self._enhance_size, Image.LANCZOS)
        
        # Apply enhancements with optimized parameters
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(self._enhancement_params['contrast'])
        
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(self._enhancement_params['sharpness'])
        
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(self._enhancement_params['color'])
        
        # Apply unsharp mask for better edge detection
        image = image.filter(ImageFilter.UnsharpMask(
            radius=self._enhancement_params['unsharp_radius'],
            percent=self._enhancement_params['unsharp_percent'],
            threshold=self._enhancement_params['unsharp_threshold']
        ))
        
        return image
    
    def enhance_image(self, image: Image.Image) -> Image.Image:
        """Apply image enhancement techniques"""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Use optimized enhancement method
            enhanced_image = self._enhance_image_optimized(image)
            
            return enhanced_image
        except Exception as e:
            print(f"❌ Error enhancing image: {e}")
            return image
    
    @lru_cache(maxsize=64)
    def _get_morphology_kernel(self) -> np.ndarray:
        """Cache morphology kernel"""
        return np.ones(self._kernel_size, np.uint8)
    
    def remove_background(self, image: Image.Image) -> Image.Image:
        """Remove background using simple segmentation"""
        try:
            # Convert to numpy array
            img_array = np.array(image)
            
            # Convert to HSV for better color segmentation
            hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
            
            # Define range for green color (healthy leaves)
            lower_green = np.array([35, 40, 40])
            upper_green = np.array([85, 255, 255])
            
            # Create mask for green areas
            mask = cv2.inRange(hsv, lower_green, upper_green)
            
            # Apply morphological operations with cached kernel
            kernel = self._get_morphology_kernel()
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Apply mask to original image
            result = cv2.bitwise_and(img_array, img_array, mask=mask)
            
            # Convert back to PIL Image
            return Image.fromarray(result)
        except Exception as e:
            print(f"❌ Error removing background: {e}")
            return image
    
    def preprocess_image_advanced(self, image_input) -> Optional[np.ndarray]:
        """Advanced image preprocessing pipeline"""
        try:
            # Handle both file paths and numpy arrays
            if isinstance(image_input, str):
                original_image = Image.open(image_input)
            elif isinstance(image_input, np.ndarray):
                original_image = Image.fromarray(image_input.astype('uint8'))
            else:
                return None
            
            # Apply enhancements
            enhanced_image = self.enhance_image(original_image)
            
            # Use enhanced image directly (background removal disabled for performance)
            segmented_image = enhanced_image
            
            # Resize to model input size
            processed_image = segmented_image.resize(self._target_size, Image.Resampling.LANCZOS)
            
            # Convert to numpy array and normalize
            img_array = np.array(processed_image, dtype=np.float32) / 255.0
            
            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)
            
            return img_array
        except Exception as e:
            print(f"❌ Error in advanced preprocessing: {e}")
            return None
    
    def test_time_augmentation(self, image_input, num_augmentations: int = 5) -> List[np.ndarray]:
        """Apply test-time augmentation for better predictions"""
        if num_augmentations <= 0:
            return []
            
        augmentations = []
        
        try:
            # Load and enhance base image
            if isinstance(image_input, str):
                base_image = self.enhance_image(Image.open(image_input))
            elif isinstance(image_input, np.ndarray):
                base_image = self.enhance_image(Image.fromarray(image_input.astype('uint8')))
            else:
                return []
            
            # Define augmentation operations
            augmentation_ops = [
                lambda img: img,  # Original
                lambda img: img.transpose(Image.FLIP_LEFT_RIGHT),  # Horizontal flip
                lambda img: img.transpose(Image.FLIP_TOP_BOTTOM),  # Vertical flip
                lambda img: img.rotate(90, expand=True),  # Rotate 90
                lambda img: img.rotate(270, expand=True)  # Rotate 270
            ]
            
            # Apply augmentations
            for i, aug_op in enumerate(augmentation_ops[:num_augmentations]):
                aug_img = aug_op(base_image)
                augmentations.append(aug_img.resize(self._target_size, Image.Resampling.LANCZOS))
            
            # Convert to numpy arrays and normalize
            processed_augmentations = []
            for aug_img in augmentations:
                img_array = np.array(aug_img, dtype=np.float32) / 255.0
                img_array = np.expand_dims(img_array, axis=0)
                processed_augmentations.append(img_array)
            
            return processed_augmentations
        except Exception as e:
            print(f"❌ Error in test-time augmentation: {e}")
            return []
    
    def ensemble_predict(self, image_input) -> Dict:
        """Make ensemble prediction using multiple methods"""
        if self.model is None:
            return {'error': 'Model not loaded'}
        
        start_time = time.time()
        
        try:
            # Method 1: Standard preprocessing
            standard_processed = self.preprocess_image_advanced(image_input)
            if standard_processed is None:
                return {'error': 'Failed to preprocess image'}
            
            standard_pred = self.model.predict(standard_processed, verbose=0)
            
            # Method 2: Test-time augmentation (parallel processing)
            tta_predictions = []
            augmented_images = self.test_time_augmentation(image_input, num_augmentations=3)
            
            # Parallel prediction for better performance
            if augmented_images:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = [executor.submit(self.model.predict, aug_img, verbose=0) for aug_img in augmented_images]
                    for future in futures:
                        pred = future.result()
                        tta_predictions.append(pred[0])
            
            # Average TTA predictions
            if tta_predictions:
                tta_avg = np.mean(tta_predictions, axis=0)
                # Combine standard and TTA predictions
                ensemble_pred = (standard_pred[0] * 0.6) + (tta_avg * 0.4)
            else:
                ensemble_pred = standard_pred[0]
            
            # Get top predictions (optimized sorting)
            if len(ensemble_pred) == 0:
                return {'error': 'Empty prediction array'}
                
            top_indices = np.argpartition(ensemble_pred, -3)[-3:][::-1]
            top_predictions = []
            
            for idx in top_indices:
                if idx < len(self._class_names):  # Safety check
                    confidence = float(ensemble_pred[idx])
                    class_name = self._class_names[idx]
                    
                    # Ensure confidence is within valid range (0-1) before converting to percentage
                    if confidence > 1.0:
                        confidence = confidence / 100.0
                    
                    top_predictions.append({
                        'class': class_name,
                        'confidence': round(confidence * 100, 2),
                        'class_index': int(idx)
                    })
            
            # Ensure we have at least one prediction
            if not top_predictions:
                return {'error': 'No valid predictions generated'}
                
            # Check confidence threshold
            top_confidence = top_predictions[0]['confidence']
            if top_confidence < (self.confidence_threshold * 100):
                prediction_status = 'uncertain'
                message = f"Low confidence prediction ({top_confidence}%). Please provide a clearer image."
            else:
                prediction_status = 'confident'
                message = "Prediction completed successfully"
            
            processing_time = round((time.time() - start_time) * 1000, 2)  # in milliseconds
            
            return {
                'status': prediction_status,
                'message': message,
                'predictions': top_predictions,
                'top_prediction': top_predictions[0],
                'ensemble_used': len(tta_predictions) > 0,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Error in ensemble prediction: {e}")
            return {'error': 'Prediction failed'}
    
    @lru_cache(maxsize=256)
    def _get_confidence_recommendation(self, confidence: float) -> str:
        """Cache confidence recommendations"""
        if confidence >= 80:
            return "High confidence prediction. Results are reliable."
        elif confidence >= 60:
            return "Moderate confidence. Consider consulting an expert for confirmation."
        else:
            return "Low confidence. Please provide a clearer, well-lit image of the plant leaf."
    
    def predict_with_confidence_filtering(self, image_path: str) -> Dict:
        """Main prediction method with confidence filtering"""
        result = self.ensemble_predict(image_path)
        
        if 'error' in result:
            return result
        
        # Add confidence-based recommendations (cached)
        top_prediction = result['top_prediction']
        confidence = top_prediction['confidence']
        
        result['recommendation'] = self._get_confidence_recommendation(confidence)
        return result
    
    @lru_cache(maxsize=512)
    def get_image_hash(self, image_path: str) -> Optional[str]:
        """Generate hash for image caching"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            return hashlib.md5(image_data).hexdigest()
        except Exception as e:
            self.logger.error(f"Error generating image hash: {e}")
            return None

# Global predictor instance
enhanced_predictor = EnhancedPlantDiseasePredictor()
