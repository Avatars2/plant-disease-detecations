from app import app
import json

# Vercel serverless handler
def handler(request):
    """Vercel serverless function handler"""
    try:
        # Convert Vercel request to WSGI format
        environ = {
            'REQUEST_METHOD': request.method,
            'PATH_INFO': request.path,
            'SERVER_NAME': 'vercel.app',
            'SERVER_PORT': '443',
            'wsgi.url_scheme': 'https',
            'wsgi.input': request.body if hasattr(request, 'body') else b'',
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
        
        # Parse response body and return proper format
        try:
            body_json = json.loads(response_body.decode('utf-8'))
            # Ensure CORS headers are included
            headers = dict(response_data['headers'])
            headers.update({
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            })
            
            return {
                'statusCode': int(response_data['status'].split()[0]),
                'headers': headers,
                'body': json.dumps(body_json)
            }
        except json.JSONDecodeError:
            headers = dict(response_data['headers'])
            headers.update({
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            })
            return {
                'statusCode': int(response_data['status'].split()[0]),
                'headers': headers,
                'body': response_body.decode('utf-8')
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Server error: {str(e)}'})
        }
