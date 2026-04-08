#!/usr/bin/env python3
"""
Model Ensemble for Plant Disease Detection
Combines multiple models for improved accuracy
"""

import tensorflow as tf
import numpy as np
from typing import List, Dict, Optional
import os
import json

class ModelEnsemble:
    def __init__(self, model_paths: List[str] = None, weights: List[float] = None):
        self.models = []
        self.weights = weights or [1.0]  # Equal weights by default
        self.class_names = [
            'Healthy Leaf', 'Powdery Mildew', 'Leaf Rust', 'Bacterial Blight', 
            'Anthracnose', 'Downy Mildew', 'Leaf Spot', 'Fusarium Wilt', 
            'Root Rot', 'Viral Mosaic', 'Bacterial Canker', 'Gray Mold',
            'Early Blight', 'Late Blight', 'Septoria Leaf Spot', 'White Rot'
        ]
        
        if model_paths:
            self.load_models(model_paths)
    
    def load_models(self, model_paths: List[str]) -> bool:
        """Load multiple models for ensemble"""
        self.models = []
        
        for model_path in model_paths:
            try:
                if os.path.exists(model_path):
                    model = tf.keras.models.load_model(model_path)
                    self.models.append(model)
                    print(f"✅ Loaded model: {model_path}")
                else:
                    print(f"⚠️ Model not found: {model_path}")
            except Exception as e:
                print(f"❌ Error loading model {model_path}: {e}")
        
        if len(self.models) == 0:
            print("❌ No models loaded successfully")
            return False
        
        # Normalize weights
        total_weight = sum(self.weights[:len(self.models)])
        self.weights = [w / total_weight for w in self.weights[:len(self.models)]]
        
        print(f"✅ Ensemble loaded with {len(self.models)} models")
        return True
    
    def predict_ensemble(self, processed_image: np.ndarray) -> Dict:
        """Make ensemble prediction from all models"""
        if len(self.models) == 0:
            return {'error': 'No models loaded'}
        
        try:
            all_predictions = []
            
            # Get predictions from all models
            for model in self.models:
                pred = model.predict(processed_image, verbose=0)
                all_predictions.append(pred[0])
            
            # Weighted average of predictions
            ensemble_pred = np.zeros_like(all_predictions[0])
            for pred, weight in zip(all_predictions, self.weights):
                ensemble_pred += pred * weight
            
            # Get top predictions
            top_indices = np.argsort(ensemble_pred)[-3:][::-1]
            top_predictions = []
            
            for idx in top_indices:
                confidence = float(ensemble_pred[idx])
                class_name = self.class_names[idx]
                
                # Ensure confidence is within valid range (0-1) before converting to percentage
                if confidence > 1.0:
                    confidence = confidence / 100.0
                
                top_predictions.append({
                    'class': class_name,
                    'confidence': round(confidence * 100, 2),
                    'class_index': int(idx)
                })
            
            # Calculate prediction agreement (variance)
            predictions_array = np.array(all_predictions)
            variance = np.var(predictions_array, axis=0)
            avg_variance = np.mean(variance)
            
            return {
                'predictions': top_predictions,
                'top_prediction': top_predictions[0],
                'ensemble_size': len(self.models),
                'model_weights': self.weights,
                'prediction_variance': float(avg_variance),
                'agreement_score': 1.0 - min(avg_variance, 1.0)  # Higher is better
            }
            
        except Exception as e:
            print(f"❌ Error in ensemble prediction: {e}")
            return {'error': 'Ensemble prediction failed'}
    
    def voting_ensemble(self, processed_image: np.ndarray) -> Dict:
        """Voting-based ensemble prediction"""
        if len(self.models) == 0:
            return {'error': 'No models loaded'}
        
        try:
            # Get predictions from all models
            model_votes = []
            for model in self.models:
                pred = model.predict(processed_image, verbose=0)
                top_class = np.argmax(pred[0])
                model_votes.append(top_class)
            
            # Count votes for each class
            vote_counts = {}
            for vote in model_votes:
                vote_counts[vote] = vote_counts.get(vote, 0) + 1
            
            # Find class with most votes
            winning_class = max(vote_counts, key=vote_counts.get)
            vote_percentage = (vote_counts[winning_class] / len(model_votes)) * 100
            
            # Get average confidence for winning class
            confidences = []
            for model in self.models:
                pred = model.predict(processed_image, verbose=0)
                confidences.append(float(pred[0][winning_class]))
            
            avg_confidence = np.mean(confidences)
            
            # Ensure confidence is within valid range (0-1) before converting to percentage
            if avg_confidence > 1.0:
                avg_confidence = avg_confidence / 100.0
            
            return {
                'winning_class': self.class_names[winning_class],
                'class_index': int(winning_class),
                'confidence': round(avg_confidence * 100, 2),
                'vote_percentage': round(vote_percentage, 2),
                'total_votes': len(model_votes),
                'vote_breakdown': {self.class_names[k]: v for k, v in vote_counts.items()},
                'method': 'voting'
            }
            
        except Exception as e:
            print(f"❌ Error in voting ensemble: {e}")
            return {'error': 'Voting ensemble failed'}

class ConfidenceFilter:
    def __init__(self, min_confidence: float = 0.60, uncertainty_threshold: float = 0.40):
        self.min_confidence = min_confidence
        self.uncertainty_threshold = uncertainty_threshold
    
    def filter_prediction(self, prediction_result: Dict) -> Dict:
        """Apply confidence filtering to prediction results"""
        if 'error' in prediction_result:
            return prediction_result
        
        confidence = prediction_result.get('confidence', 0)
        
        # Ensure confidence is in decimal form (0-1) for comparison
        if confidence > 1.0:
            confidence = confidence / 100.0
        
        if confidence >= self.min_confidence:
            status = 'confident'
            message = "High confidence prediction"
        elif confidence >= self.uncertainty_threshold:
            status = 'moderate'
            message = "Moderate confidence - consider expert consultation"
        else:
            status = 'uncertain'
            message = "Low confidence - please provide a clearer image"
        
        prediction_result['confidence_status'] = status
        prediction_result['confidence_message'] = message
        
        return prediction_result

# Create ensemble with single model for now (can be extended later)
def create_ensemble() -> ModelEnsemble:
    """Create model ensemble - currently uses single model"""
    model_path = "model.h5"
    if os.path.exists(model_path):
        return ModelEnsemble([model_path], [1.0])
    else:
        return ModelEnsemble()

# Global instances
model_ensemble = create_ensemble()
confidence_filter = ConfidenceFilter()
