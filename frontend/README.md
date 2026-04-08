# Plant Disease Detection Frontend

A simple, responsive frontend for the Plant Disease Detection application built with HTML, CSS, and JavaScript.

## Features

- **Authentication**: Login and registration system
- **Dashboard**: Main interface for disease detection
- **Image Upload**: Drag-and-drop or click to upload plant images
- **Disease Detection**: AI-powered disease identification
- **Results Display**: Shows disease information with confidence scores
- **Detection History**: Keeps track of previous detections

## File Structure

```
frontend/
├── index.html          # Login and registration page
├── dashboard.html      # Main dashboard page
├── styles.css          # Global styles
├── script.js           # Authentication logic
├── dashboard.js        # Dashboard functionality
└── README.md           # This file
```

## Setup

1. Make sure the backend server is running on `http://localhost:5000`
2. Open `index.html` in a web browser to start the application

## API Integration

The frontend connects to the following backend endpoints:

- `POST /api/auth/login` - User login
- `POST /api/auth/signup` - User registration
- `GET /api/auth/profile` - Get user profile
- `POST /api/predict/detect` - Detect plant disease

## Features Details

### Authentication
- Email and password login
- User registration with username, email, phone, and password
- JWT token-based authentication
- Auto-redirect to dashboard if already logged in

### Dashboard
- User profile display
- Image upload with drag-and-drop support
- Real-time disease detection
- Results visualization with confidence scores
- Detection history tracking

### Responsive Design
- Mobile-friendly interface
- Adaptive layout for different screen sizes
- Touch-friendly controls

## Browser Compatibility

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Security Notes

- JWT tokens are stored in localStorage
- API calls include proper authentication headers
- File upload validation for type and size
- Input validation and sanitization

## Development

To modify the frontend:

1. Edit HTML files for structure changes
2. Modify `styles.css` for styling updates
3. Update JavaScript files for functionality changes
4. Test with the backend running

## Troubleshooting

- **CORS Issues**: Ensure backend allows requests from your domain
- **Authentication Errors**: Check if backend is running and accessible
- **Upload Issues**: Verify file size and type restrictions
- **Display Issues**: Check browser console for JavaScript errors
