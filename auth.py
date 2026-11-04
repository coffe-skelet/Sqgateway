"""
OAuth Authentication Module for Squeeze Gateway
Supports Google and GitHub OAuth flows
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeTimedSerializer
from starlette.requests import Request

# Session management
SESSION_SECRET = os.environ.get("SESSION_SECRET", secrets.token_urlsafe(32))
serializer = URLSafeTimedSerializer(SESSION_SECRET)

# OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")

# Base URL for OAuth redirects
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8082")

# Initialize OAuth
oauth = OAuth()

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
        }
    )

if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
    oauth.register(
        name='github',
        client_id=GITHUB_CLIENT_ID,
        client_secret=GITHUB_CLIENT_SECRET,
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_params=None,
        authorize_url='https://github.com/login/oauth/authorize',
        authorize_params=None,
        api_base_url='https://api.github.com/',
        client_kwargs={'scope': 'user:email'},
    )


# Session storage (in production use Redis or database)
sessions = {}


def create_session(user_data: dict) -> str:
    """Create a new session token"""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        'user': user_data,
        'created_at': datetime.utcnow(),
        'expires_at': datetime.utcnow() + timedelta(days=7),
    }
    return session_id


def get_session(session_token: str) -> Optional[dict]:
    """Get session data by token"""
    session = sessions.get(session_token)
    if not session:
        return None

    # Check expiration
    if datetime.utcnow() > session['expires_at']:
        del sessions[session_token]
        return None

    return session['user']


def delete_session(session_token: str):
    """Delete a session"""
    if session_token in sessions:
        del sessions[session_token]


async def get_current_user(request: Request) -> Optional[dict]:
    """Get current authenticated user from request"""
    # Try to get session token from cookie
    session_token = request.cookies.get('sqg_session')
    if not session_token:
        return None

    return get_session(session_token)


def require_auth(request: Request):
    """Dependency that requires authentication"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    return user


# OAuth Routes
def setup_auth_routes(app):
    """Setup authentication routes"""

    @app.get("/auth/google")
    async def google_login(request: Request):
        """Initiate Google OAuth flow"""
        if not GOOGLE_CLIENT_ID:
            raise HTTPException(400, "Google OAuth not configured")

        redirect_uri = f"{BASE_URL}/auth/google/callback"
        return await oauth.google.authorize_redirect(request, redirect_uri)


    @app.get("/auth/google/callback")
    async def google_callback(request: Request):
        """Handle Google OAuth callback"""
        try:
            token = await oauth.google.authorize_access_token(request)
            user_info = token.get('userinfo')

            if not user_info:
                raise HTTPException(400, "Failed to get user info from Google")

            # Create user session
            user_data = {
                'id': user_info['sub'],
                'email': user_info['email'],
                'name': user_info.get('name', ''),
                'picture': user_info.get('picture', ''),
                'provider': 'google',
            }

            session_token = create_session(user_data)

            # Redirect to profile with session cookie
            response = RedirectResponse(url='/profile.html')
            response.set_cookie(
                key='sqg_session',
                value=session_token,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='lax',
                max_age=7 * 24 * 60 * 60,  # 7 days
            )

            return response

        except Exception as e:
            print(f"Google OAuth error: {e}")
            return RedirectResponse(url='/login.html?error=google_auth_failed')


    @app.get("/auth/github")
    async def github_login(request: Request):
        """Initiate GitHub OAuth flow"""
        if not GITHUB_CLIENT_ID:
            raise HTTPException(400, "GitHub OAuth not configured")

        redirect_uri = f"{BASE_URL}/auth/github/callback"
        return await oauth.github.authorize_redirect(request, redirect_uri)


    @app.get("/auth/github/callback")
    async def github_callback(request: Request):
        """Handle GitHub OAuth callback"""
        try:
            token = await oauth.github.authorize_access_token(request)

            # Get user info from GitHub
            resp = await oauth.github.get('user', token=token)
            user_info = resp.json()

            # Get user email (might be in a separate endpoint)
            email_resp = await oauth.github.get('user/emails', token=token)
            emails = email_resp.json()
            primary_email = next((e['email'] for e in emails if e['primary']), None)

            # Create user session
            user_data = {
                'id': str(user_info['id']),
                'email': primary_email or user_info.get('email', ''),
                'name': user_info.get('name') or user_info.get('login', ''),
                'picture': user_info.get('avatar_url', ''),
                'provider': 'github',
                'username': user_info.get('login', ''),
            }

            session_token = create_session(user_data)

            # Redirect to profile with session cookie
            response = RedirectResponse(url='/profile.html')
            response.set_cookie(
                key='sqg_session',
                value=session_token,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite='lax',
                max_age=7 * 24 * 60 * 60,  # 7 days
            )

            return response

        except Exception as e:
            print(f"GitHub OAuth error: {e}")
            return RedirectResponse(url='/login.html?error=github_auth_failed')


    @app.get("/auth/logout")
    async def logout(request: Request):
        """Logout user"""
        session_token = request.cookies.get('sqg_session')
        if session_token:
            delete_session(session_token)

        response = RedirectResponse(url='/login.html')
        response.delete_cookie('sqg_session')
        return response


    @app.get("/auth/me")
    async def get_me(request: Request):
        """Get current user info"""
        user = await get_current_user(request)
        if not user:
            raise HTTPException(401, "Not authenticated")

        return {
            'authenticated': True,
            'user': user,
        }


    @app.get("/auth/status")
    async def auth_status(request: Request):
        """Check authentication status"""
        user = await get_current_user(request)
        return {
            'authenticated': bool(user),
            'user': user if user else None,
            'google_enabled': bool(GOOGLE_CLIENT_ID),
            'github_enabled': bool(GITHUB_CLIENT_ID),
        }
