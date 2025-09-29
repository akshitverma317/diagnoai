import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
from typing import Optional
from datetime import datetime, timedelta

# Import AWS Secrets Manager utility
from aws_secrets_utils import get_secret

def get_db_connection():
    """Create and return a database connection"""
    try:
        # Retrieve database secrets from AWS Secrets Manager
        secrets = get_secret("diagnoai-secrets")
        
        conn = psycopg2.connect(
            host=secrets.get("DB_HOST"),
            database=secrets.get("DB_NAME"),
            user=secrets.get("DB_USER"),
            password=secrets.get("DB_PASSWORD"),
            port=secrets.get("DB_PORT")
        )
        return conn
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
        return None

def get_user_usage_from_db(email: str) -> int:
    """Get user's usage count from database"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return 0
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT usage_count 
            FROM bbt_user_doctorai 
            WHERE email = %s
        """
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        
        if result:
            return result['usage_count'] or 0
        return 0
        
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return 0
    finally:
        if conn:
            conn.close()

def update_user_usage_in_db(email: str, new_count: int) -> bool:
    """Update user's usage count in database"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # Check if user exists
        check_query = "SELECT email FROM bbt_user_doctorai WHERE email = %s"
        cursor.execute(check_query, (email,))
        user_exists = cursor.fetchone()
        
        if user_exists:
            query = """
                UPDATE bbt_user_doctorai 
                SET usage_count = %s 
                WHERE email = %s
                RETURNING usage_count
            """
            cursor.execute(query, (new_count, email))
            conn.commit()
            return True
        else:
            st.error(f"User with email {email} not found in database")
            return False
        
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def ensure_user_exists(email: str, name: str) -> bool:
    """Create user if not exists in database"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # Check if user exists
        check_query = "SELECT email FROM bbt_user_doctorai WHERE email = %s"
        cursor.execute(check_query, (email,))
        user_exists = cursor.fetchone()
        
        if not user_exists:
            insert_query = """
                INSERT INTO bbt_user_doctorai 
                (email, name, usage_count, premium_usage_count, paid_user, password_hash)
                VALUES (%s, %s, 0, 0, 0, 'none')
            """
            cursor.execute(insert_query, (email, name))
            conn.commit()
            st.info(f"Created new user account for {email}")
            return True
        
        return True
        
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def increment_usage(user_email: Optional[str] = None) -> bool:
    """Increment usage count in both session state and database"""
    try:
        if st.session_state.paid_user or st.session_state.get("premium_user", False):
            st.session_state.premium_usage_count += 1
            return True
            
        if not user_email:
            user_email = st.session_state.get("user_email")
        
        if not user_email:
            st.error("No user email found in session")
            return False
            
        current_db_count = get_user_usage_from_db(user_email)
        new_count = current_db_count + 1
        st.session_state.usage_count = new_count
        
        return update_user_usage_in_db(user_email, new_count)
            
    except Exception as e:
        st.error(f"Error in increment_usage: {str(e)}")
        return False

def get_user_status_from_db(email: str) -> dict:
    """Get complete user status from database"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return {"usage_count": 0, "paid_user": False, "premium_usage_count": 0}
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT usage_count, paid_user, premium_usage_count, subscription_expires_at
            FROM bbt_user_doctorai 
            WHERE email = %s
        """
        cursor.execute(query, (email,))
        result = cursor.fetchone()
        
        if result:
            return {
                "usage_count": result['usage_count'] or 0,
                "paid_user": bool(result['paid_user']),
                "premium_usage_count": result['premium_usage_count'] or 0,
                "subscription_expires_at": result['subscription_expires_at']
            }
        return {"usage_count": 0, "paid_user": False, "premium_usage_count": 0}
        
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return {"usage_count": 0, "paid_user": False, "premium_usage_count": 0}
    finally:
        if conn:
            conn.close()

def init_user_session(email: str):
    """Initialize user session with database values"""
    user_status = get_user_status_from_db(email)
    st.session_state.usage_count = user_status["usage_count"]
    st.session_state.paid_user = user_status["paid_user"]
    st.session_state.premium_usage_count = user_status["premium_usage_count"]
    st.session_state.subscription_expires_at = user_status["subscription_expires_at"]

def update_user_subscription(email: str, is_paid: bool = False, expires_at: Optional[datetime] = None):
    """Update user's subscription status in the database"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # Update subscription details
        query = """
            UPDATE bbt_user_doctorai 
            SET paid_user = %s, 
                subscription_expires_at = %s, 
                premium_usage_count = 0
            WHERE email = %s
        """
        cursor.execute(query, (is_paid, expires_at, email))
        conn.commit()
        return True
        
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
