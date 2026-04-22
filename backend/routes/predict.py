from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import sys
import numpy as np
from PIL import Image
from datetime import datetime
from db import db
import uuid
import hashlib
from simple_predictor import SimplePlantDiseasePredictor
from functools import lru_cache

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

# Simple predictor instance
simple_predictor = SimplePlantDiseasePredictor()

@lru_cache(maxsize=1)
def get_model_info():
    """Cache model information"""
    return {
        'classes': CLASS_NAMES,
        'num_classes': len(CLASS_NAMES),
        'input_shape': (224, 224, 3),
        'model_type': 'simple/external_api'
    }

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

def predict_disease_simple(image_path):
    """Simple plant disease prediction using lightweight predictor"""
    try:
        return simple_predictor.predict_from_image(image_path)
    except Exception as e:
        print(f"â Error in simple prediction: {e}")
        return {'error': f'Prediction failed: {str(e)}'}

def predict_disease(image_path):
    """Legacy prediction method - now uses simple predictor"""
    return predict_disease_simple(image_path)

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
        
        # Use simple prediction
        prediction_result = predict_disease_simple(file_path)
        
        if 'error' in prediction_result:
            os.remove(file_path)
            return jsonify({'error': 'Failed to process image or make prediction'}), 500
        
        # Extract prediction details
        predicted_class = prediction_result.get('predicted_class', 'Unknown')
        confidence = prediction_result.get('confidence', 0.0)
        predicted_class_index = CLASS_NAMES.index(predicted_class) if predicted_class in CLASS_NAMES else 0
        prediction_status = 'success' if confidence > 0.6 else 'low_confidence'
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
                'confidence': round(confidence * 100, 2),  # Convert to percentage
                'class_index': int(predicted_class_index),
                'status': prediction_status,
                'recommendation': '',
                'all_predictions': all_predictions,
                'method': 'simple',
                'ensemble_used': False
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