// API Base URL
const API_BASE_URL = 'http://localhost:5000/api';

// DOM Elements
const loginForm = document.getElementById('loginForm');
const registerForm = document.getElementById('registerForm');
const loginError = document.getElementById('login-error');
const registerError = document.getElementById('register-error');

// Error handling
function showError(form, message) {
    const errorElement = form === 'login' ? loginError : registerError;
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.add('show');
    }
}

function hideError(form) {
    const errorElement = form === 'login' ? loginError : registerError;
    if (errorElement) {
        errorElement.classList.remove('show');
    }
}

// Login functionality
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError('login');
        
        const formData = new FormData(loginForm);
        const loginData = {
            email: formData.get('email'),
            password: formData.get('password')
        };
        
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(loginData)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Store token and user data
                localStorage.setItem('token', result.access_token);
                localStorage.setItem('user', JSON.stringify(result.user));
                
                // Redirect to dashboard
                window.location.href = 'dashboard.html';
            } else {
                showError('login', result.error || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            showError('login', 'Network error. Please try again.');
        }
    });
}

// Register functionality
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError('register');
        
        const formData = new FormData(registerForm);
        const registerData = {
            username: formData.get('username'),
            email: formData.get('email'),
            phone: formData.get('phone'),
            password: formData.get('password')
        };
        
        try {
            const response = await fetch(`${API_BASE_URL}/auth/signup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(registerData)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Store token and user data
                localStorage.setItem('token', result.access_token);
                localStorage.setItem('user', JSON.stringify(result.user));
                
                // Redirect to dashboard
                window.location.href = 'dashboard.html';
            } else {
                showError('register', result.error || 'Registration failed');
            }
        } catch (error) {
            console.error('Registration error:', error);
            showError('register', 'Network error. Please try again.');
        }
    });
}

// Check if user is already logged in and redirect if needed
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    const currentPath = window.location.pathname;
    
    // If user is logged in and trying to access auth pages, redirect to dashboard
    if (token && (currentPath.includes('login.html') || currentPath.includes('register.html') || currentPath.endsWith('/'))) {
        // Verify token is valid by checking profile
        fetch(`${API_BASE_URL}/auth/profile`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (response.ok) {
                // Token is valid, redirect to dashboard
                window.location.href = 'dashboard.html';
            } else {
                // Token is invalid, remove it
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
        })
        .catch(error => {
            console.error('Token validation error:', error);
            localStorage.removeItem('token');
            localStorage.removeItem('user');
        });
    }
});

// Form validation helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^[0-9]{10}$/;
    return re.test(phone);
}

// Real-time validation
document.getElementById('register-email').addEventListener('blur', function() {
    if (this.value && !validateEmail(this.value)) {
        this.setCustomValidity('Please enter a valid email address');
    } else {
        this.setCustomValidity('');
    }
});

document.getElementById('register-phone').addEventListener('blur', function() {
    if (this.value && !validatePhone(this.value)) {
        this.setCustomValidity('Please enter a valid 10-digit phone number');
    } else {
        this.setCustomValidity('');
    }
});
