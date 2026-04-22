from app import app
import json

# Vercel serverless function handler
def handler(request):
    # Create WSGI environ from Vercel request
    environ = {
        'REQUEST_METHOD': request.method,
        'PATH_INFO': request.path,
        'SERVER_NAME': 'vercel.app',
        'SERVER_PORT': '443',
        'wsgi.url_scheme': 'https',
        'wsgi.input': request.body,
        'wsgi.errors': None,
        'wsgi.version': (1, 0),
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': True,
    }
    
    # Add headers
    for key, value in request.headers.items():
        environ[f'HTTP_{key.upper().replace("-", "_")}'] = value
    
    # Collect response
    response_data = {}
    
    def start_response(status, headers):
        response_data['status'] = status
        response_data['headers'] = headers
    
    # Get response from Flask app
    response = app(environ, start_response)
    response_body = b''.join(response)
    
    return {
        'statusCode': int(response_data['status'].split()[0]),
        'headers': dict(response_data['headers']),
        'body': response_body.decode('utf-8')
    }
