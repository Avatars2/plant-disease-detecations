#!/usr/bin/env python3
"""
Model loader for external model hosting
Downloads model from external storage on demand
"""

import os
import requests
import tempfile
from typing import Optional
import logging

class ExternalModelLoader:
    def __init__(self, model_url: Optional[str] = None):
        self.model_url = model_url or os.getenv('MODEL_URL')
        self.model_path = None
        self.logger = logging.getLogger(__name__)
    
    def download_model(self) -> str:
        """Download model from external storage"""
        if not self.model_url:
            raise ValueError("Model URL not provided")
        
        # Create temporary file for model
        temp_dir = tempfile.mkdtemp()
        model_path = os.path.join(temp_dir, "model.h5")
        
        try:
            self.logger.info(f"Downloading model from {self.model_url}")
            response = requests.get(self.model_url, stream=True)
            response.raise_for_status()
            
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.model_path = model_path
            self.logger.info(f"Model downloaded to {model_path}")
            return model_path
            
        except Exception as e:
            self.logger.error(f"Failed to download model: {e}")
            raise
    
    def get_model_path(self) -> str:
        """Get model path, download if necessary"""
        if not self.model_path or not os.path.exists(self.model_path):
            return self.download_model()
        return self.model_path
