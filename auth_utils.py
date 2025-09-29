import os
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
import streamlit as st
import urllib.parse
from jwt import ExpiredSignatureError, InvalidTokenError

# Import database utilities
from db_utils import (
    get_user_usage_from_db, 
    ensure_user_exists, 
    init_user_session
)

# Constants for subscription
FREE_USAGE_LIMIT = 6
PREMIUM_USAGE_LIMIT = 20
SUBSCRIPTION_DURATION_DAYS = 1

def init_session_state():
    """Initialize session state with authentication and usage tracking variables"""
    if "_auth_session_initialized" not in st.session_state:
        # Authentication related
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        
        if "user_token" not in st.session_state:
            st.session_state.user_token = None
            
        if "user_name" not in st.session_state:
            st.session_state.user_name = None
            
        if "user_email" not in st.session_state:
            st.session_state.user_email = None
            
        if "paid_user" not in st.session_state:
            st.session_state.paid_user = False
            
        if "premium_user" not in st.session_state:
            st.session_state.premium_user = False
            
        if "usage_count" not in st.session_state:
            st.session_state.usage_count = 0
            
        if "premium_usage_count" not in st.session_state:
            st.session_state.premium_usage_count = 0
            
        if "subscription_expires_at" not in st.session_state:
            st.session_state.subscription_expires_at = None
            
        if "payment_processed" not in st.session_state:
            st.session_state.payment_processed = False
            
        st.session_state._auth_session_initialized = True

def handle_token_authentication(token: str, secret_key: str):
    """Handle token authentication similar to test.py"""
    try:
        # Decode token
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        # Extract user information
        email = decoded.get("email", "")
        user_name = decoded.get("name") or email.split("@")[0]
        
        # Ensure user exists in database
        if not ensure_user_exists(email, user_name):
            st.error("Failed to create/verify user account")
            st.stop()
        
        # Get usage count from database
        db_usage_count = get_user_usage_from_db(email)
        
        # Store in session state
        st.session_state.user_token = token
        st.session_state.user_name = user_name
        st.session_state.user_email = email
        st.session_state.authenticated = True
        st.session_state.usage_count = db_usage_count
        
        # Initialize user session from database
        init_user_session(email)
        
        # Clear the URL parameters
        st.query_params.clear()
        st.rerun()
        
    except ExpiredSignatureError:
        st.error("Session expired. Please log in again.")
        st.stop()
    except InvalidTokenError as e:
        st.error(f"Invalid token. Please log in again. ({e})")
        st.stop()

def generate_token(email: str, name: str, secret_key: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generate a JWT token for authentication"""
    if not expires_delta:
        expires_delta = timedelta(days=1)
    
    expiration = datetime.utcnow() + expires_delta
    payload = {
        "email": email,
        "name": name,
        "exp": expiration
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

def validate_token(token: str, secret_key: str) -> Optional[Dict]:
    """Validate JWT token and return decoded payload"""
    try:
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        st.error("Session expired. Please log in again.")
        return None
    except jwt.InvalidTokenError as e:
        st.error(f"Invalid token. Please log in again. ({e})")
        return None

def check_premium_subscription() -> bool:
    """Check if premium subscription is active"""
    if st.session_state.paid_user or st.session_state.get("premium_user", False):
        current_time = int(datetime.now().timestamp())
        
        if (st.session_state.subscription_expires_at and 
            current_time > int(st.session_state.subscription_expires_at)):
            st.session_state.paid_user = False
            st.session_state.premium_user = False
            return False
        
        elif st.session_state.premium_usage_count >= PREMIUM_USAGE_LIMIT:
            st.session_state.paid_user = False
            st.session_state.premium_user = False
            return False
            
        return True
    return False

def get_premium_status() -> Dict:
    """Get premium subscription status"""
    if st.session_state.paid_user or st.session_state.get("premium_user", False):
        remaining_uses = PREMIUM_USAGE_LIMIT - st.session_state.premium_usage_count
        return {
            "active": True,
            "uses_remaining": remaining_uses,
            "max_uses": PREMIUM_USAGE_LIMIT
        }
    return {"active": False, "message": "Free account"}

def check_usage_limit() -> bool:
    """Check if user has reached usage limit"""
    check_premium_subscription()
    
    if st.session_state.paid_user or st.session_state.get("premium_user", False):
        return st.session_state.premium_usage_count < PREMIUM_USAGE_LIMIT
    
    return st.session_state.usage_count < FREE_USAGE_LIMIT

def handle_signout():
    """Handle user sign out"""
    # Define the exact logout URL
    LOGOUT_URL = "http://bellblaze-dev.s3-website.ap-south-1.amazonaws.com/our-solutions"
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Initialize new session
    init_session_state()
    
    # Redirect to login page using multiple methods
    st.markdown(f"""
    <script>
    // Clear all storage
    sessionStorage.clear();
    localStorage.clear();
    
    // Redirect to login page
    window.location.href = "{LOGOUT_URL}";
    window.location.replace("{LOGOUT_URL}");
    </script>
    """, unsafe_allow_html=True)
    
    # Fallback meta refresh
    st.markdown(f"""
    <meta http-equiv="refresh" content="0; url={LOGOUT_URL}" />
    """, unsafe_allow_html=True)
    
    # Ensure the app stops execution
    st.stop()

def create_subscription_url(app_id: str, token: str) -> str:
    """Create subscription payment URL"""
    return (
        "https://paymentdocumentchatbot.s3.ap-south-1.amazonaws.com/razorpay-payment/razorpay-payment.html?"
        + urllib.parse.urlencode({"app_id": app_id, "token": token})
    )
