import streamlit as st
from PIL import Image
import io
import base64
import numpy as np

def render_sidebar_logo(logo_path, width=None, max_width=None):
    """
    Render a logo at the top of the sidebar
    
    Args:
        logo_path (str): Path to the logo image file
        width (int, optional): Specific width for the logo
        max_width (int, optional): Maximum width for the logo
    """
    try:
        # Open the logo image
        logo = Image.open(logo_path)
        
        # Prepare logo styling
        logo_style = "display: block; margin: 0 auto; "
        
        # Apply width if specified
        if width:
            logo_style += f"width: {width}px; "
        
        # Apply max-width if specified
        if max_width:
            logo_style += f"max-width: {max_width}px; "
        else:
            logo_style += "max-width: 100%; "
        
        # Add additional styling
        logo_style += "border-radius: 8px; padding: 10px; background-color: rgba(255,255,255,0.1);"
        
        # Convert image to base64 for inline display
        buffered = io.BytesIO()
        logo.save(buffered, format="PNG")
        logo_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Create markdown with logo
        st.sidebar.markdown(f"""
        <div style="{logo_style}">
            <img src="data:image/png;base64,{logo_base64}" style="width: 100%; height: auto;">
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.sidebar.error(f"Error loading logo: {str(e)}")

def render_sidebar_user_info(user_name, is_premium=False, logo_path=None, uses_remaining=None):
    """
    Render a custom sidebar user information section with optional logo
    
    Args:
        user_name (str): Name of the user
        is_premium (bool, optional): Whether the user is a premium user
        logo_path (str, optional): Path to the logo image file
        uses_remaining (int, optional): Number of uses remaining
    """
    # Render logo if path is provided
    if logo_path:
        render_sidebar_logo(logo_path, max_width=250)
    
    # Render user info
    st.sidebar.markdown(f"""
    <div class="sidebar-user-info">
        <h4>Hi, {user_name}!</h4>
        {f'<span class="sidebar-premium-badge">Premium</span>' if is_premium else ''}
    </div>
    """, unsafe_allow_html=True)
    
    # Render uses remaining if provided
    if uses_remaining is not None:
        st.sidebar.markdown(f"""
        <div class="sidebar-uses-remaining">
            {uses_remaining} free uses remaining
        </div>
        """, unsafe_allow_html=True)

def apply_custom_styles():
    """Apply professional CSS styles to Streamlit app"""
    st.markdown("""
    <style>
    /* Professional Button Base Styling */
    .stButton>button, 
    .stDownloadButton>button, 
    .stFileUploader>div>div>button {
        /* Advanced button styling */
        background-color: #2196F3 !important;  /* Primary blue */
        color: white !important;
        border: none !important;
        border-radius: 6px !important;  /* Slightly rounded corners */
        
        /* Professional typography */
        font-family: 'Inter', 'Segoe UI', Roboto, sans-serif !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        
        /* Responsive sizing */
        padding: 12px 24px !important;
        font-size: 14px !important;
        
        /* Smooth transitions */
        transition: all 0.3s ease !important;
        
        /* Subtle shadow for depth */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        
        /* Cursor indication */
        cursor: pointer !important;
        
        /* Prevent text selection */
        user-select: none !important;
        
        /* Position for pseudo-element effects */
        position: relative !important;
        overflow: hidden !important;
    }

    /* Hover Effect with Depth */
    .stButton>button:hover, 
    .stDownloadButton>button:hover, 
    .stFileUploader>div>div>button:hover {
        background-color: #1E88E5 !important;  /* Slightly darker blue */
        box-shadow: 0 6px 8px rgba(0,0,0,0.15) !important;
        transform: translateY(-2px) !important;
    }

    /* Active/Pressed State */
    .stButton>button:active, 
    .stDownloadButton>button:active, 
    .stFileUploader>div>div>button:active {
        background-color: #1976D2 !important;  /* Even darker blue */
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        transform: translateY(1px) !important;
    }

    /* Ripple Effect Pseudo-Element */
    .stButton>button::before, 
    .stDownloadButton>button::before, 
    .stFileUploader>div>div>button::before {
        content: '' !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) scale(0) !important;
        width: 0 !important;
        height: 0 !important;
        border-radius: 50% !important;
        background-color: rgba(255,255,255,0.2) !important;
        opacity: 0 !important;
        transition: all 0.3s ease !important;
    }

    .stButton>button:active::before, 
    .stDownloadButton>button:active::before, 
    .stFileUploader>div>div>button:active::before {
        width: 200% !important;
        height: 200% !important;
        opacity: 1 !important;
        transform: translate(-50%, -50%) scale(1) !important;
    }

    /* Sidebar Button Specific Styling */
    .sidebar .stButton>button, 
    .sidebar .stDownloadButton>button {
        width: 100% !important;
        margin: 8px 0 !important;
        font-size: 13px !important;
    }

    /* Responsive Design */
    @media screen and (max-width: 600px) {
        .stButton>button, 
        .stDownloadButton>button, 
        .stFileUploader>div>div>button {
            padding: 10px 18px !important;
            font-size: 12px !important;
        }
    }

    /* Disabled State */
    .stButton>button:disabled, 
    .stDownloadButton>button:disabled, 
    .stFileUploader>div>div>button:disabled {
        background-color: #B0BEC5 !important;
        color: rgba(255,255,255,0.7) !important;
        cursor: not-allowed !important;
        box-shadow: none !important;
        transform: none !important;
    }

    /* Sidebar User Info Styling */
    .sidebar-user-info {
        background-color: #2196F3 !important;  /* Blue background */
        color: white !important;
        padding: 15px !important;
        border-radius: 8px !important;
        margin-top: 15px !important;
        text-align: center !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }

    .sidebar-user-info h4 {
        margin: 0 !important;
        color: white !important;
        font-size: 18px !important;
    }

    .sidebar-premium-badge {
        background-color: #1E88E5 !important;  /* Slightly darker blue for premium badge */
        color: white !important;
        padding: 3px 10px !important;
        border-radius: 20px !important;
        font-size: 12px !important;
        margin-top: 5px !important;
        display: inline-block !important;
    }

    /* Sidebar Uses Remaining Styling */
    .sidebar-uses-remaining {
        background-color: rgba(33, 150, 243, 0.1) !important;  /* Light blue background */
        color: #2196F3 !important;  /* Blue text */
        padding: 10px 15px !important;
        border-radius: 8px !important;
        margin-top: 15px !important;  /* Gap between user info and uses remaining */
        text-align: center !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    </style>
    """, unsafe_allow_html=True)

def blue_button(label, key=None, on_click=None, disabled=False, help=None):
    """
    Create a professional blue-styled Streamlit button
    
    Args:
        label (str): Button text
        key (str, optional): Unique key for the button
        on_click (callable, optional): Function to call when button is clicked
        disabled (bool, optional): Disable the button
        help (str, optional): Tooltip text
    
    Returns:
        bool: True if button is clicked, False otherwise
    """
    if on_click:
        return st.button(
            label, 
            key=key, 
            on_click=on_click, 
            disabled=disabled, 
            help=help
        )
    else:
        return st.button(
            label, 
            key=key, 
            disabled=disabled, 
            help=help
        )

def blue_download_button(
    label, 
    data, 
    file_name, 
    mime=None, 
    key=None, 
    disabled=False, 
    help=None
):
    """
    Create a professional blue-styled download button
    
    Args:
        label (str): Button text
        data: Data to be downloaded
        file_name (str): Name of the file to download
        mime (str, optional): MIME type of the file
        key (str, optional): Unique key for the button
        disabled (bool, optional): Disable the button
        help (str, optional): Tooltip text
    
    Returns:
        bool: True if button is clicked, False otherwise
    """
    return st.download_button(
        label=label, 
        data=data, 
        file_name=file_name, 
        mime=mime, 
        key=key,
        disabled=disabled,
        help=help
    )

def blue_file_uploader(
    label, 
    type=None, 
    accept_multiple_files=False, 
    key=None, 
    help=None
):
    """
    Create a professional blue-styled file uploader
    
    Args:
        label (str): Uploader label
        type (list, optional): Allowed file types
        accept_multiple_files (bool, optional): Allow multiple file upload
        key (str, optional): Unique key for the uploader
        help (str, optional): Tooltip text
    
    Returns:
        Uploaded file(s)
    """
    return st.file_uploader(
        label=label, 
        type=type, 
        accept_multiple_files=accept_multiple_files, 
        key=key,
        help=help
    )

def is_xray_image(img_array):
    """
    Check if the given image is likely to be an X-ray image.
    
    Args:
        img_array (numpy.ndarray): Image array to check
        
    Returns:
        bool: True if the image is likely an X-ray, False otherwise
    """
    # Convert to grayscale if it's a color image
    if len(img_array.shape) == 3:
        # Check if the image has high color variation (typical of natural images)
        color_variation = np.std(img_array - np.mean(img_array, axis=2, keepdims=True))
        if color_variation > 25:  # High color variation indicates non-medical image
            return False
            
        # Convert to grayscale by taking mean of RGB channels
        gray_img = np.mean(img_array, axis=2)
    else:
        gray_img = img_array
    
    # X-ray characteristics checks
    mean_intensity = np.mean(gray_img)
    std_intensity = np.std(gray_img)
    
    # Calculate local contrast variance (X-rays have smooth transitions)
    local_contrast = np.std([np.roll(gray_img, i) - gray_img for i in [1, -1, gray_img.shape[1], -gray_img.shape[1]]], axis=0)
    local_contrast_mean = np.mean(local_contrast)
    
    # Calculate histogram features
    hist_range = (20, 235)
    histogram = np.histogram(gray_img, bins=256, range=hist_range)[0]
    smoothed_hist = np.convolve(histogram, np.ones(5)/5, mode='valid')
    
    # Medical X-rays typically have specific histogram characteristics
    hist_peaks = np.where(smoothed_hist > np.mean(smoothed_hist) + 0.5 * np.std(smoothed_hist))[0]
    peak_spread = np.max(hist_peaks) - np.min(hist_peaks) if len(hist_peaks) > 1 else 0
    
    # Calculate symmetry - medical X-rays often have roughly symmetric intensity distribution
    hist_midpoint = len(smoothed_hist) // 2
    symmetry_score = np.corrcoef(smoothed_hist[:hist_midpoint], smoothed_hist[hist_midpoint:][::-1])[0,1]
    
    # More sophisticated conditions for X-ray detection
    conditions = [
        20 < mean_intensity < 235,      # Typical X-ray intensity range
        15 < std_intensity < 80,        # Appropriate contrast range for medical images
        local_contrast_mean < 25,       # Smooth transitions characteristic of X-rays
        len(hist_peaks) >= 2,           # Multiple distinct tissue densities
        peak_spread > 30,               # Good separation between tissue densities
        symmetry_score > -0.3,          # Some degree of histogram symmetry
        np.max(histogram) < np.prod(gray_img.shape) * 0.3  # No overwhelming single intensity
    ]
    
    # Check edge characteristics (X-rays have smoother edges)
    edges_x = np.diff(gray_img, axis=1)
    edges_y = np.diff(gray_img, axis=0)
    edge_intensity = np.mean(np.abs(edges_x)) + np.mean(np.abs(edges_y))
    if edge_intensity > 30:  # Too many sharp edges indicate non-medical image
        return False
    
    return all(conditions)

