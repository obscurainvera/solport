from flask import Response

def add_cors_headers(response, status_code=200):
    """
    Add CORS headers to the response
    
    Args:
        response: Flask response object
        status_code: HTTP status code (default: 200)
        
    Returns:
        Response with CORS headers
    """
    if isinstance(response, Response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.status_code = status_code
        return response
    else:
        resp = Response(response)
        resp.headers.add('Access-Control-Allow-Origin', '*')
        resp.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        resp.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        resp.status_code = status_code
        return resp 