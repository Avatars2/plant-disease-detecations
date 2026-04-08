# 🌿 AI-Based Plant Disease Detection System

A full-stack web application that allows users to detect plant diseases using a trained deep learning model with user authentication and real-time image processing.

## 🎯 Features

- **User Authentication**: Secure signup/login system with JWT tokens
- **Image Upload**: Upload plant leaf images for disease detection
- **Camera Capture**: Capture images directly from camera
- **AI Prediction**: CNN-based disease detection with confidence scores
- **Prediction History**: View past detection results
- **Modern UI**: Responsive design with gradient styling

## 🏗️ System Architecture

```
React Frontend → Flask Backend → MongoDB → TensorFlow Model
```

## 🛠️ Technologies Used

### Frontend
- React.js 19.2.4
- React Router DOM 7.13.1
- Axios 1.13.6

### Backend
- Flask 2.3.3
- Flask-JWT-Extended 4.5.2
- Flask-CORS 4.0.0
- TensorFlow 2.13.0
- MongoDB (pymongo 4.5.0)

### Database
- MongoDB for user data and prediction history

## 📋 Prerequisites

- Node.js (v16 or higher)
- Python 3.8+
- MongoDB installed and running
- Git

## 🚀 Setup Instructions

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd IM
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### 3. Create Placeholder Model (for testing)
```bash
cd backend
python utils/model_utils.py
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

### 5. Start MongoDB
Make sure MongoDB is running on your system:
```bash
# On macOS with Homebrew
brew services start mongodb-community

# On Windows
net start MongoDB

# On Linux
sudo systemctl start mongod
```

## 🏃‍♂️ Running the Application

### 1. Start Backend Server
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python app.py
```

The backend will run on `http://localhost:5000`

### 2. Start Frontend Development Server
```bash
cd frontend
npm start
```

The frontend will run on `http://localhost:3000`

## 📱 Usage

1. **Sign Up**: Create a new account with username, email, phone, and password
2. **Login**: Use your credentials to access the dashboard
3. **Upload Image**: Choose a plant leaf image or capture from camera
4. **Get Prediction**: Click "Predict Disease" to analyze the image
5. **View History**: Check your past predictions in the History section

## 🔧 Configuration

### Backend Environment Variables (.env)
```
MONGODB_URI=mongodb://localhost:27017/plant_disease_db
JWT_SECRET_KEY=your_jwt_secret_key_here_change_in_production
FLASK_ENV=development
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
```

## 📊 Disease Classes

The system can detect the following plant conditions:
- Healthy
- Bacterial Spot
- Early Blight
- Late Blight
- Leaf Mold
- Septoria Leaf Spot
- Spider Mites
- Target Spot
- Yellow Leaf Curl Virus
- Mosaic Virus

## 🔐 API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/profile` - Get user profile

### Prediction
- `POST /api/predict/upload` - Upload and predict image
- `GET /api/predict/history` - Get user prediction history
- `GET /api/predict/classes` - Get available disease classes

### Health Check
- `GET /api/health` - API health status

## 🎨 UI Features

- **Responsive Design**: Works on desktop and mobile devices
- **Modern Gradients**: Beautiful gradient backgrounds and buttons
- **Interactive Elements**: Hover effects and smooth transitions
- **Error Handling**: User-friendly error messages
- **Loading States**: Visual feedback during operations

## 🔍 Testing the Application

1. Create a test account
2. Upload a plant leaf image
3. Test camera capture functionality
4. Verify prediction results
5. Check prediction history
6. Test logout and login flow

## 🚀 Future Enhancements

- [ ] Mobile application
- [ ] Multi-language support
- [ ] Weather-based prediction
- [ ] Admin panel
- [ ] Real-time video detection
- [ ] More disease classes
- [ ] Treatment recommendations

## 🐛 Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running
   - Check the connection string in .env

2. **CORS Error**
   - Backend CORS is configured for localhost:3000
   - Make sure frontend is running on port 3000

3. **Model Loading Error**
   - Run the placeholder model creation script
   - Ensure model.h5 exists in backend directory

4. **Camera Access Denied**
   - Use HTTPS or localhost for camera access
   - Check browser permissions

## 📞 Support

For any issues or questions, please check the troubleshooting section or create an issue in the repository.

## 📄 License

This project is licensed under the MIT License.

---

**Happy Plant Disease Detection! 🌱**
# plant-disease-detecations
