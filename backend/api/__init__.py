from app import app

# Vercel serverless handler
def handler(request):
    """Vercel serverless function handler"""
    return app(request)
