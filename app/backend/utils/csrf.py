import secrets
from flask import Response, abort, request, session


def setup_csrf(app):
    @app.before_request
    def check_csrf_token():
        if app.config.get('TESTING') or not app.config.get('CSRF_PROTECTION'):
            return None
        
        if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            cookie_token = request.cookies.get('csrf_token')
            session_token = session.get('csrf_token')
            if not cookie_token or not session_token or not secrets.compare_digest(cookie_token, session_token):
                abort(403, 'CSRF token is missing or is invalid.')
                
    @app.after_request
    def set_csrf_token(response: Response):
        if app.config.get('TESTING') or not app.config.get('CSRF_PROTECTION'):
            return response
        
        token = session.get('csrf_token')
        if not token:
            token = secrets.token_hex(32)
        response.set_cookie('csrf_token', token, samesite="Strict")
        session['csrf_token'] = token

        return response
