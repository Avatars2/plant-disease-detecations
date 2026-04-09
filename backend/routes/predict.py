from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import sys
import tensorflow as tf
import numpy as np
from PIL import Image
from datetime import datetime
from db import db
import uuid
import hashlib
from cache_manager import (
    cache_result, cache_prediction_result, get_cached_prediction,
    cache_user_history, get_cached_user_history, cache_model_classes,
    get_cached_model_classes
)
from enhanced_predictor import enhanced_predictor
from model_ensemble import model_ensemble, confidence_filter
from functools import lru_cache
import multiprocessing as mp

predict_bp = Blueprint('predict', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# PlantVillage dataset classes
CLASS_NAMES = [
    'Healthy', 'Bacterial Spot', 'Early Blight', 'Late Blight',
    'Leaf Mold', 'Septoria Leaf Spot', 'Spider Mites', 'Target Spot',
    'Yellow Leaf Curl Virus', 'Mosaic Virus'
]

# Global model variable with lazy loading
model = None
model_loaded = False

@lru_cache(maxsize=1)
def get_model_info():
    """Cache model information"""
    return {
        'classes': CLASS_NAMES,
        'num_classes': len(CLASS_NAMES),
        'input_shape': (224, 224, 3)  # Updated to match trained model
    }

def load_model():
    """Load the plant disease detection model with optimized loading"""
    global model, model_loaded
    
    if model_loaded and model is not None:
        return True
        
    try:
        model_path = os.path.join(os.path.dirname(__file__), '..', 'model.h5')
        if os.path.exists(model_path):
            # Optimize model loading for inference
            model = tf.keras.models.load_model(model_path, compile=False)  # Don't compile for inference
            
            # Optimize model for inference
            try:
                # Enable XLA compilation for faster inference
                tf.config.optimizer.set_jit(True)
                print("✅ XLA compilation enabled for faster inference")
            except:
                print("⚠️ XLA compilation not available")
            
            model_loaded = True
            print("✅ Plant disease model loaded successfully")
            return True
        else:
            print("❌ Model file not found")
            return False
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

def preprocess_image(image_path):
    """Preprocess image for model prediction"""
    try:
        # Load and resize image
        img = Image.open(image_path)
        img = img.convert('RGB')
        img = img.resize((128, 128))  # Updated to match trained model
        
        # Convert to numpy array and normalize
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    except Exception as e:
        print(f"❌ Error preprocessing image: {e}")
        return None

def get_image_hash(image_path):
    """Generate hash for image to use as cache key"""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        return hashlib.md5(image_data).hexdigest()
    except Exception as e:
        print(f"❌ Error generating image hash: {e}")
        return None

@cache_result("simple_prediction", ttl=3600)
def predict_disease_simple(image_path):
    """Simple and reliable plant disease prediction"""
    global model
    
    if model is None:
        if not load_model():
            return {'error': 'Model not available'}
    
    try:
        # Preprocess the image
        processed_image = preprocess_image(image_path)
        if processed_image is None:
            return {'error': 'Failed to preprocess image'}
        
        # Make prediction
        predictions = model.predict(processed_image, verbose=0)
        
        if len(predictions) == 0 or len(predictions[0]) == 0:
            return {'error': 'Empty prediction result'}
        
        # Get top prediction
        predicted_class_index = np.argmax(predictions[0])
        confidence = float(np.max(predictions[0]))
        
        # Safety check for class index
        if predicted_class_index >= len(CLASS_NAMES):
            return {'error': f'Invalid class index: {predicted_class_index}'}
        
        predicted_class = CLASS_NAMES[predicted_class_index]
        
        return {
            'predicted_disease': predicted_class,
            'confidence': round(float(confidence) * 100, 2),  # Convert from 0-1 to percentage
            'class_index': int(predicted_class_index),
            'prediction_method': 'simple',
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'success' if confidence > 0.5 else 'low_confidence'
        }
        
    except Exception as e:
        print(f"❌ Error in simple prediction: {e}")
        return {'error': f'Prediction failed: {str(e)}'}

@cache_result("prediction", ttl=3600)
def predict_disease(image_path):
    """Predict plant disease using real ML model with caching (legacy)"""
    global model
    
    if model is None:
        if not load_model():
            return None
    
    try:
        # Generate image hash for caching
        image_hash = get_image_hash(image_path)
        if not image_hash:
            return None
        
        # Check cache first
        cached_result = get_cached_prediction(image_hash)
        if cached_result:
            print(f"🎯 Cache hit for image: {image_hash[:8]}...")
            return cached_result
        
        # Preprocess the image
        processed_image = preprocess_image(image_path)
        if processed_image is None:
            return None
        
        # Make prediction
        predictions = model.predict(processed_image)
        predicted_class_index = np.argmax(predictions[0])
        confidence = float(np.max(predictions[0]))
        predicted_class = CLASS_NAMES[predicted_class_index]
        
        result = {
            'disease': predicted_class,
            'confidence': confidence,
            'class_index': int(predicted_class_index),
            'image_hash': image_hash
        }
        
        # Cache the result
        cache_prediction_result(image_hash, result, 3600)
        
        return result
    except Exception as e:
        print(f"❌ Error making prediction: {e}")
        return None

@predict_bp.route('/upload', methods=['POST'])
def upload_and_predict():
    try:
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        file.save(file_path)
        
        # Use simple and reliable prediction first
        prediction_result = predict_disease_simple(file_path)
        
        if 'error' in prediction_result:
            # Try enhanced prediction as fallback
            print("⚠️ Simple prediction failed, trying enhanced method...")
            try:
                from enhanced_predictor import enhanced_predictor
                prediction_result = enhanced_predictor.predict_with_confidence_filtering(file_path)
                if 'error' in prediction_result:
                    os.remove(file_path)
                    return jsonify({'error': 'Failed to process image or make prediction'}), 500
            except Exception as e:
                print(f"❌ Enhanced prediction also failed: {e}")
                os.remove(file_path)
                return jsonify({'error': 'Failed to process image or make prediction'}), 500
        
        # Extract prediction details (handle both simple and enhanced formats)
        if 'predicted_disease' in prediction_result:
            # Simple prediction format
            predicted_class = prediction_result['predicted_disease']
            confidence = prediction_result['confidence']  # Already in percentage
            predicted_class_index = prediction_result.get('class_index', 0)
            prediction_status = prediction_result.get('status', 'unknown')
            all_predictions = [prediction_result]
        elif 'top_prediction' in prediction_result:
            # Enhanced prediction format
            top_pred = prediction_result['top_prediction']
            predicted_class = top_pred['class']
            confidence = top_pred['confidence']  # Already in percentage
            predicted_class_index = top_pred['class_index']
            prediction_status = prediction_result.get('status', 'unknown')
            all_predictions = prediction_result.get('predictions', [])
        else:
            # Fallback to legacy format
            predicted_class = prediction_result['disease']
            confidence = prediction_result['confidence']
            predicted_class_index = prediction_result['class_index']
            prediction_status = 'confident'
            all_predictions = [prediction_result]
        
        result = {
            'filename': unique_filename,
            'original_filename': filename,
            'predicted_disease': predicted_class,
            'confidence': confidence,
            'timestamp': datetime.utcnow()
        }
        
        history_collection = db.get_collection('history')
        history_collection.insert_one(result)
        
        os.remove(file_path)
        
        return jsonify({
            'success': True,
            'prediction': {
                'disease': predicted_class,
                'confidence': round(confidence, 2),  # Already in percentage
                'class_index': int(predicted_class_index),
                'status': prediction_status,
                'recommendation': prediction_result.get('recommendation', ''),
                'all_predictions': all_predictions,
                'method': prediction_result.get('prediction_method', 'standard'),
                'ensemble_used': prediction_result.get('ensemble_used', False)
            }
        }), 200
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@predict_bp.route('/history', methods=['GET'])
def get_prediction_history():
    try:
        # Get all prediction history from database
        history = db.get_collection('history').find(
            {},
            {'_id': 0}
        ).sort('timestamp', -1).limit(50)
        
        history_list = list(history)
        
        # Convert ObjectId to string for JSON serialization
        for record in history_list:
            if '_id' in record:
                record['_id'] = str(record['_id'])
            if 'timestamp' in record:
                record['timestamp'] = record['timestamp'].isoformat()
        
        return jsonify({
            'success': True,
            'history': history_list,
            'total': len(history_list)
        })
    except Exception as e:
        print(f"❌ Error fetching history: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch prediction history'
        }), 500

@predict_bp.route('/classes', methods=['GET'])
def get_disease_classes():
    try:
        return jsonify({
            'success': True,
            'classes': CLASS_NAMES
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500