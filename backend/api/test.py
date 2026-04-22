#!/usr/bin/env python3
"""
Simple test endpoint to verify backend is working
"""

def handler(request):
    """Test handler for debugging"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': '{"message": "Backend API is working!", "status": "healthy", "method": "' + request.method + '"}'
    }
