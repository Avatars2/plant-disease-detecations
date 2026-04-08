// API Base URL
const API_BASE_URL = 'http://localhost:5000/api';

// DOM Elements
const usernameElement = document.getElementById('username');
const logoutBtn = document.getElementById('logout-btn');
const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const previewContainer = document.getElementById('previewContainer');
const previewImage = document.getElementById('previewImage');
const detectBtn = document.getElementById('detectBtn');
const clearBtn = document.getElementById('clearBtn');
const resultsSection = document.getElementById('resultsSection');
const loadingOverlay = document.getElementById('loadingOverlay');
const historyContainer = document.getElementById('historyContainer');

// User data
let currentUser = null;
let detectionHistory = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
    loadUserData();
    loadDetectionHistory();
    setupEventListeners();
});

// Check authentication
async function checkAuth() {
    const token = localStorage.getItem('token');
    
    if (!token) {
        window.location.href = 'index.html';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/profile`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Invalid token');
        }
        
        const result = await response.json();
        currentUser = result.user;
    } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = 'index.html';
    }
}

// Load user data
function loadUserData() {
    const userData = localStorage.getItem('user');
    if (userData) {
        const user = JSON.parse(userData);
        if (usernameElement) {
            usernameElement.textContent = user.username;
        }
    }
}

// Setup event listeners
function setupEventListeners() {
    // Logout
    logoutBtn.addEventListener('click', logout);
    
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = e.target.dataset.section;
            switchSection(section);
            
            // Update active state
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            e.target.classList.add('active');
        });
    });
    
    // File upload
    uploadArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleDrop);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    
    // Buttons
    detectBtn.addEventListener('click', detectDisease);
    clearBtn.addEventListener('click', clearImage);
}

// Logout functionality
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

// File handling
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        processFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    uploadArea.style.borderColor = '#5a6fd8';
    uploadArea.style.background = '#f0f4ff';
}

function handleDragLeave(event) {
    event.preventDefault();
    uploadArea.style.borderColor = '#667eea';
    uploadArea.style.background = '#f8f9ff';
}

function handleDrop(event) {
    event.preventDefault();
    uploadArea.style.borderColor = '#667eea';
    uploadArea.style.background = '#f8f9ff';
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        processFile(files[0]);
    }
}

function processFile(file) {
    // Validate file type
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
    }
    
    // Validate file size (16MB max)
    if (file.size > 16 * 1024 * 1024) {
        alert('File size must be less than 16MB');
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        previewImage.src = e.target.result;
        uploadArea.style.display = 'none';
        previewContainer.style.display = 'block';
    };
    reader.readAsDataURL(file);
    
    // Store file for detection
    window.currentFile = file;
}

function clearImage() {
    previewImage.src = '';
    uploadArea.style.display = 'block';
    previewContainer.style.display = 'none';
    resultsSection.style.display = 'none';
    fileInput.value = '';
    window.currentFile = null;
}

// Disease detection
async function detectDisease() {
    if (!window.currentFile) {
        alert('Please select an image first');
        return;
    }
    
    showLoading(true);
    
    const formData = new FormData();
    formData.append('file', window.currentFile);
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/predict/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            if (result.success && result.prediction) {
                displayResults(result.prediction);
                addToHistory(result.prediction);
            } else {
                alert(result.error || 'Detection failed');
            }
        } else {
            alert(result.error || 'Detection failed');
        }
    } catch (error) {
        console.error('Detection error:', error);
        alert('Network error. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Display detection results
function displayResults(result) {
    const diseaseName = document.getElementById('diseaseName');
    const confidenceScore = document.getElementById('confidenceScore');
    const diseaseDescription = document.getElementById('diseaseDescription');
    const recommendationsList = document.getElementById('recommendationsList');
    
    diseaseName.textContent = result.disease || 'Unknown';
    
    // Handle confidence (backend returns percentage already)
    const confidenceValue = result.confidence > 1 ? result.confidence : result.confidence * 100;
    confidenceScore.textContent = `${Math.round(confidenceValue)}%`;
    
    // Set confidence color based on score
    if (confidenceValue >= 80) {
        confidenceScore.style.background = '#28a745'; // Green
    } else if (confidenceValue >= 60) {
        confidenceScore.style.background = '#ffc107'; // Yellow
    } else {
        confidenceScore.style.background = '#dc3545'; // Red
    }
    
    // Simple descriptions for common diseases
    const descriptions = {
        'Healthy': 'The plant appears to be healthy with no visible signs of disease.',
        'Bacterial Spot': 'Bacterial spot is caused by bacteria that create small, water-soaked spots on leaves.',
        'Early Blight': 'Early blight is a fungal disease that causes target-like spots on leaves.',
        'Late Blight': 'Late blight is a serious fungal disease that can destroy entire crops.',
        'Leaf Mold': 'Leaf mold is a fungal disease that causes yellow spots and mold growth.',
        'Septoria Leaf Spot': 'Septoria leaf spot causes small, circular spots with dark borders.',
        'Spider Mites': 'Spider mites are tiny pests that cause yellow stippling on leaves.',
        'Target Spot': 'Target spot causes concentric rings on leaves, resembling targets.',
        'Yellow Leaf Curl Virus': 'A viral disease that causes leaves to curl and turn yellow.',
        'Mosaic Virus': 'Mosaic virus causes mottled patterns on leaves and stunted growth.'
    };
    
    diseaseDescription.textContent = descriptions[result.disease] || 'No description available.';
    
    // Display recommendations
    recommendationsList.innerHTML = '';
    const recommendations = getRecommendations(result.disease);
    recommendations.forEach(rec => {
        const li = document.createElement('li');
        li.textContent = rec;
        recommendationsList.appendChild(li);
    });
    
    resultsSection.style.display = 'block';
    setTimeout(() => {
        resultsSection.classList.add('show');
    }, 100);
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Get recommendations based on disease
function getRecommendations(disease) {
    const recommendations = {
        'Healthy': [
            'Continue regular monitoring',
            'Maintain proper watering and fertilization',
            'Ensure good air circulation'
        ],
        'Bacterial Spot': [
            'Remove infected leaves immediately',
            'Apply copper-based fungicides',
            'Avoid overhead watering',
            'Ensure proper plant spacing'
        ],
        'Early Blight': [
            'Remove affected plant parts',
            'Apply fungicides containing chlorothalonil',
            'Improve air circulation',
            'Use disease-resistant varieties'
        ],
        'Late Blight': [
            'Destroy infected plants immediately',
            'Apply metalaxyl-based fungicides',
            'Ensure proper drainage',
            'Monitor weather conditions'
        ],
        'Leaf Mold': [
            'Reduce humidity around plants',
            'Improve air circulation',
            'Remove affected leaves',
            'Apply appropriate fungicides'
        ],
        'Septoria Leaf Spot': [
            'Remove infected leaves',
            'Apply fungicides with copper',
            'Avoid overhead irrigation',
            'Ensure proper spacing'
        ],
        'Spider Mites': [
            'Wash leaves with soapy water',
            'Apply miticides if infestation is severe',
            'Increase humidity around plants',
            'Remove heavily infested leaves'
        ],
        'Target Spot': [
            'Remove infected plant parts',
            'Apply appropriate fungicides',
            'Improve air circulation',
            'Avoid wetting leaves during watering'
        ],
        'Yellow Leaf Curl Virus': [
            'Remove infected plants',
            'Control whitefly populations',
            'Use virus-free seeds',
            'Implement crop rotation'
        ],
        'Mosaic Virus': [
            'Remove infected plants',
            'Control aphid populations',
            'Use resistant varieties',
            'Sanitize tools between plants'
        ]
    };
    
    return recommendations[disease] || ['Consult with agricultural expert for specific treatment'];
}

// Add to detection history
function addToHistory(result) {
    const historyItem = {
        id: Date.now(),
        image: previewImage.src,
        disease: result.disease || 'Unknown',
        confidence: result.confidence > 1 ? result.confidence : result.confidence * 100,
        timestamp: new Date().toISOString()
    };
    
    detectionHistory.unshift(historyItem);
    
    // Keep only last 10 items
    if (detectionHistory.length > 10) {
        detectionHistory = detectionHistory.slice(0, 10);
    }
    
    // Save to localStorage
    localStorage.setItem('detectionHistory', JSON.stringify(detectionHistory));
    
    // Update display
    updateHistoryDisplay();
}

// Switch between sections
function switchSection(section) {
    // Hide all sections
    document.querySelectorAll('.upload-section, .results-section, .history-section, .welcome-card').forEach(sec => {
        sec.style.display = 'none';
    });
    
    // Show selected section
    switch(section) {
        case 'dashboard':
            document.querySelector('.welcome-card').style.display = 'block';
            document.querySelector('.upload-section').style.display = 'block';
            document.querySelector('.history-section').style.display = 'block';
            if (resultsSection.style.display === 'block') {
                resultsSection.style.display = 'block';
            }
            break;
        case 'history':
            document.querySelector('.history-section').style.display = 'block';
            break;
        case 'settings':
            // Show settings (you can create a settings section)
            alert('Settings section coming soon!');
            switchSection('dashboard');
            break;
    }
}

// Load detection history from API
async function loadDetectionHistory() {
    const token = localStorage.getItem('token');
    if (!token) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/predict/history`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                detectionHistory = result.history;
                updateHistoryDisplay();
            }
        }
    } catch (error) {
        console.error('Failed to load history:', error);
        // Fallback to localStorage
        const saved = localStorage.getItem('detectionHistory');
        if (saved) {
            detectionHistory = JSON.parse(saved);
            updateHistoryDisplay();
        }
    }
}

// Update history display
function updateHistoryDisplay() {
    if (detectionHistory.length === 0) {
        historyContainer.innerHTML = `
            <div class="no-history-card">
                <div class="no-history-icon">📊</div>
                <h3>No detection history available</h3>
                <p>Upload your first plant image to get started with disease detection</p>
            </div>
        `;
        return;
    }
    
    historyContainer.innerHTML = '';
    
    detectionHistory.forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        const date = new Date(item.timestamp);
        const formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        
        // Determine confidence level
        const confidence = item.confidence || 0;
        let confidenceClass = 'confidence-low';
        if (confidence >= 80) confidenceClass = 'confidence-high';
        else if (confidence >= 60) confidenceClass = 'confidence-medium';
        
        historyItem.innerHTML = `
            <div class="history-item-header">
                <h4>${item.predicted_disease || item.disease || 'Unknown'}</h4>
                <span class="confidence-badge ${confidenceClass}">${Math.round(confidence)}%</span>
            </div>
            <div class="history-item-body">
                <p class="history-filename">📁 ${item.original_filename || 'Unknown file'}</p>
                <p class="history-date">🕒 ${formattedDate}</p>
            </div>
        `;
        
        historyContainer.appendChild(historyItem);
    });
}

// Loading overlay
function showLoading(show) {
    loadingOverlay.style.display = show ? 'flex' : 'none';
}
