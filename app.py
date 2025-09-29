import streamlit as st
import tensorflow as tf
from tensorflow.keras.preprocessing import image
import numpy as np
import pydicom
import os
import io
import urllib.parse
import jwt
import webbrowser  # Add this import

# Import custom modules
from auth_utils import (
    init_session_state, 
    handle_signout, 
    create_subscription_url, 
    check_usage_limit, 
    get_premium_status,
    handle_token_authentication
)
from db_utils import increment_usage, ensure_user_exists
from ui_utils import (
    apply_custom_styles, 
    blue_button, 
    blue_download_button, 
    blue_file_uploader,
    render_sidebar_user_info,
    is_xray_image
)

# Import AWS Secrets Manager utility
from aws_secrets_utils import get_secret

# Get secret key from AWS Secrets Manager
try:
    secrets = get_secret("diagnoai-secrets")
    SECRET_KEY = secrets.get("SECRET_KEY")
except Exception as e:
    st.error(f"Failed to retrieve secrets: {e}")
    SECRET_KEY = None

# Define the image size and class names
IMAGE_SIZE = (224, 224)
MULTI_CLASS_NAMES = ['Edema', 'Normal', 'Pneumonia', 'Tuberculosis','Effusion']
BINARY_CLASS_NAMES = ['NotEdema', 'Edema']

# Load both of our trained models
@st.cache_resource
def load_models():
    multi_model = tf.keras.models.load_model('disease_classifier_model.h5')
    edema_model = tf.keras.models.load_model('edema_classifier_model.h5')
    return multi_model, edema_model

multi_model, edema_model = load_models()

# Initialize session state
init_session_state()

# Apply custom styles
apply_custom_styles()

# Check for token in query parameters
params = st.query_params
token = params.get("token", "")
app_id = params.get("app_id", "diagnoai")

# Handle token authentication if token is present
if token and SECRET_KEY:
    handle_token_authentication(token, SECRET_KEY)

# Sidebar content
def render_sidebar():
    # Display user information and subscription status
    with st.sidebar:
        # Calculate remaining uses
        if st.session_state.paid_user or st.session_state.get("premium_user", False):
            premium_status = get_premium_status()
            if premium_status["active"]:
                uses_remaining = premium_status['uses_remaining']
            else:
                uses_remaining = 0
        else:
            uses_remaining = max(0, 6 - st.session_state.usage_count)
        
        # Render sidebar logo and user info
        render_sidebar_user_info(
            user_name=st.session_state.user_name or 'Guest', 
            is_premium=st.session_state.get("premium_user", False),
            logo_path="logo.png",  # Make sure to replace with your actual logo path
            uses_remaining=uses_remaining
        )
        
        st.markdown("---")
        
        # Premium subscription button
        if not st.session_state.get("premium_user", False):
            if blue_button("⚡Subscribe"):
                token = st.session_state.get("user_token", "")
                if not token:
                    st.warning("Please log in first.")
                else:
                    url = create_subscription_url("doctorai", token)
                    st.markdown(
                        f"""
                        <meta http-equiv="refresh" content="0; url={url}">
                        <script>
                            window.location.href = "{url}";
                        </script>
                        """,
                        unsafe_allow_html=True
                    )
        
        # Sign out button
        if blue_button("🚪 Sign Out"):
            handle_signout()

# Main Streamlit app
def main():
    # Check if user is authenticated
    if not st.session_state.get("authenticated", False):
        # Add a session state variable to control link visibility
        if 'hide_unauthorized_link' not in st.session_state:
            st.session_state.hide_unauthorized_link = False
        
        # Login URL
        login_url = "http://bellblaze-dev.s3-website.ap-south-1.amazonaws.com/login?DomainPath=/doctorai"
        
        # Error message with login button
        col1, col2 = st.columns([3, 1])
        with col1:
            st.error("🔒 Unauthorized. Please log in on the original tab to continue.")
        
        with col2:
            if st.button("Login", key="login_redirect_btn"):
                # Open URL in default browser
                webbrowser.open(login_url)
                # st.info("Login page opened in your default browser.")
        
       
        st.stop()

    st.title("🩺 DiagnoAI")
    st.write("Upload a chest X-ray image (JPG, JPEG, PNG, or DICOM) to get a disease prediction.")

    # Render sidebar
    render_sidebar()

    # File Upload Section
    uploaded_file = blue_file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "dcm"])

    if uploaded_file is not None:
        # Check usage limits
        if not check_usage_limit():
            st.error("You have reached your usage limit. Please upgrade to premium to continue.")
            return

        # Increment usage
        if not increment_usage():
            st.error("Failed to track usage. Please try again.")
            return

        # Handle DICOM files
        if uploaded_file.name.endswith('.dcm'):
            dicom_data = pydicom.dcmread(io.BytesIO(uploaded_file.getvalue()))
            img = dicom_data.pixel_array
            img = (np.maximum(img, 0) / img.max()) * 255.0 
            img = np.uint8(img)
            if len(img.shape) == 2:
                img = np.stack((img,)*3, axis=-1)
            img_for_model = tf.image.resize(img, IMAGE_SIZE)
            
        # Handle normal image files (JPG, PNG)
        else:
            img_for_model = image.load_img(uploaded_file, target_size=IMAGE_SIZE)
            img_for_model = image.img_to_array(img_for_model)
        
        # Display the uploaded image
        st.image(uploaded_file, caption='Uploaded Image.', use_container_width=True)
        
        # Check if the image is an X-ray
        if not is_xray_image(img_for_model):
            st.error("⚠️ The uploaded image does not appear to be an X-ray image. Please upload a valid chest X-ray image.")
            return

        # Preprocess the image for the models
        img_array = np.expand_dims(img_for_model, axis=0) 
        img_array = img_array / 255.0 

        # Make a Prediction with the Multi-Class Model
        multi_prediction = multi_model.predict(img_array)
        predicted_class_index = np.argmax(multi_prediction)
        predicted_class_name = MULTI_CLASS_NAMES[predicted_class_index]
        confidence = multi_prediction[0][predicted_class_index]

        # Use the Binary Classifier for Edema if needed
        edema_prediction = None
        if predicted_class_name == 'Edema':
            edema_prediction = edema_model.predict(img_array)[0][0]
        
        # Display the Results
        st.write("")
        st.write("### Prediction")
        
        if predicted_class_name == 'Normal':
            st.success(f"The model predicts: **{predicted_class_name}** with {confidence*100:.2f}% confidence.")
            st.info("No signs of disease detected based on the analysis.")
        else:
            if predicted_class_name == 'Edema' and edema_prediction is not None:
                edema_confidence = edema_prediction * 100
                if edema_prediction >= 0.5:
                    st.error(f"The model predicts: **Edema** with {edema_confidence:.2f}% confidence (specialist opinion).")
                    st.warning("Please consult a medical professional for an accurate diagnosis.")
                else:
                    st.error(f"The model predicts: **{predicted_class_name}** with {confidence*100:.2f}% confidence.")
                    st.info("A second opinion suggests this is likely not Edema.")
            else:
                st.error(f"The model predicts: **{predicted_class_name}** with {confidence*100:.2f}% confidence.")
                st.warning("Please consult a medical professional for an accurate diagnosis.")

# Run the main function
if __name__ == "__main__":
    main()

