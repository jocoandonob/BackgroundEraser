import streamlit as st
import io
import base64
import numpy as np
from PIL import Image
from rembg import remove
import zipfile
import time

# Configure page
st.set_page_config(
    page_title="AI Background Remover",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def remove_background(image):
    """Remove background from image using rembg"""
    try:
        # Convert PIL image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # Remove background
        output = remove(img_byte_arr)
        
        # Convert back to PIL Image
        result_image = Image.open(io.BytesIO(output))
        return result_image
    except Exception as e:
        st.error(f"Error removing background: {str(e)}")
        return None

def composite_images(foreground_img, background_img):
    """Composite foreground (no-bg) image onto background image"""
    try:
        # Ensure both images are in RGBA mode
        if foreground_img.mode != 'RGBA':
            foreground_img = foreground_img.convert('RGBA')
        if background_img.mode != 'RGBA':
            background_img = background_img.convert('RGBA')
        
        # Resize background to match foreground if needed
        if background_img.size != foreground_img.size:
            background_img = background_img.resize(foreground_img.size, Image.Resampling.LANCZOS)
        
        # Composite the images
        result = Image.alpha_composite(background_img, foreground_img)
        return result.convert('RGB')
    except Exception as e:
        st.error(f"Error compositing images: {str(e)}")
        return None

def get_download_link(img, filename):
    """Generate download link for processed image"""
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:image/png;base64,{img_str}" download="{filename}">Download {filename}</a>'
    return href

def create_zip_download(processed_images, original_filenames):
    """Create a zip file containing all processed images"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, (img, original_name) in enumerate(zip(processed_images, original_filenames)):
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            
            # Generate filename
            name_without_ext = original_name.rsplit('.', 1)[0] if '.' in original_name else original_name
            filename = f"{name_without_ext}_no_bg.png"
            
            zip_file.writestr(filename, img_buffer.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

def validate_image(uploaded_file):
    """Validate uploaded image file"""
    try:
        # Check file size (limit to 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("File size too large. Please upload images smaller than 10MB.")
            return None
        
        # Try to open image
        image = Image.open(uploaded_file)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        return image
    except Exception as e:
        st.error(f"Invalid image file: {str(e)}")
        return None

# Main app
def main():
    st.title("🖼️ AI Background Remover")
    st.markdown("Upload your images and let AI remove the background automatically!")
    
    # Sidebar with instructions
    with st.sidebar:
        st.header("📋 Instructions")
        st.markdown("""
        1. **Upload Images**: Choose JPG, PNG, or JPEG files to remove backgrounds
        2. **Upload Backgrounds** (Optional): Choose new background images
        3. **Process**: Click 'Remove Background' button
        4. **Preview**: View original, no-background, and composited images
        5. **Download**: Save individual images or batch download
        
        **Supported Formats**: JPG, PNG, JPEG
        **Max File Size**: 10MB per image
        """)
        
        st.header("ℹ️ About")
        st.markdown("""
        This app uses AI-powered background removal technology to automatically detect and remove backgrounds from your images.
        
        Perfect for:
        - Product photography
        - Profile pictures
        - Design projects
        - Social media content
        """)
    
    # File upload section
    st.header("📤 Upload Images")
    uploaded_files = st.file_uploader(
        "Choose image files to remove background",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help="You can upload multiple images at once",
        key="main_upload"
    )
    
    # Background images upload section
    st.header("🖼️ Upload Background Images (Optional)")
    background_files = st.file_uploader(
        "Choose background images to replace removed backgrounds",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help="These images will be used as new backgrounds for your processed images",
        key="background_upload"
    )
    
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} image(s) uploaded successfully!")
        
        # Show background files info if uploaded
        if background_files:
            st.info(f"🎨 {len(background_files)} background image(s) uploaded for compositing!")
        
        # Process images button
        if st.button("🚀 Remove Background", type="primary", use_container_width=True):
            processed_images = []
            composited_images = []
            original_filenames = []
            
            # Create progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uploaded_file in enumerate(uploaded_files):
                # Update progress
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f"Processing image {i + 1} of {len(uploaded_files)}: {uploaded_file.name}")
                
                # Validate and process image
                image = validate_image(uploaded_file)
                if image is not None:
                    # Remove background
                    processed_image = remove_background(image)
                    if processed_image is not None:
                        processed_images.append(processed_image)
                        original_filenames.append(uploaded_file.name)
                        
                        # If background images are provided, create composited versions
                        if background_files:
                            # Use background images cyclically
                            bg_index = i % len(background_files)
                            background_image = validate_image(background_files[bg_index])
                            if background_image is not None:
                                composited = composite_images(processed_image, background_image)
                                if composited is not None:
                                    composited_images.append(composited)
                                else:
                                    composited_images.append(None)
                            else:
                                composited_images.append(None)
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            if processed_images:
                st.success(f"🎉 Successfully processed {len(processed_images)} image(s)!")
                
                # Store in session state for persistence
                st.session_state.processed_images = processed_images
                st.session_state.composited_images = composited_images if background_files else []
                st.session_state.original_filenames = original_filenames
                st.session_state.original_images = [validate_image(f) for f in uploaded_files if validate_image(f) is not None]
                st.session_state.background_files = background_files if background_files else []
        
        # Display results if available
        if hasattr(st.session_state, 'processed_images') and st.session_state.processed_images:
            st.header("🎨 Results")
            
            # Batch download option
            if len(st.session_state.processed_images) > 1:
                st.subheader("📦 Batch Download")
                zip_data = create_zip_download(st.session_state.processed_images, st.session_state.original_filenames)
                st.download_button(
                    label="⬇️ Download All Images (ZIP)",
                    data=zip_data,
                    file_name="background_removed_images.zip",
                    mime="application/zip",
                    use_container_width=True
                )
                st.divider()
            
            # Individual image results
            st.subheader("🔍 Individual Results")
            
            has_composited = hasattr(st.session_state, 'composited_images') and st.session_state.composited_images
            
            for i, (original_img, processed_img, filename) in enumerate(zip(
                st.session_state.original_images, 
                st.session_state.processed_images, 
                st.session_state.original_filenames
            )):
                st.markdown(f"**Image {i + 1}: {filename}**")
                
                # Create columns for comparison
                if has_composited and i < len(st.session_state.composited_images) and st.session_state.composited_images[i] is not None:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**Original**")
                        st.image(original_img, use_container_width=True)
                    
                    with col2:
                        st.markdown("**Background Removed**")
                        st.image(processed_img, use_container_width=True)
                    
                    with col3:
                        st.markdown("**With New Background**")
                        st.image(st.session_state.composited_images[i], use_container_width=True)
                    
                    # Download buttons for both versions
                    name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
                    
                    col_dl1, col_dl2 = st.columns(2)
                    
                    with col_dl1:
                        # Download no-background version
                        download_filename_nobg = f"{name_without_ext}_no_bg.png"
                        img_buffer_nobg = io.BytesIO()
                        processed_img.save(img_buffer_nobg, format='PNG')
                        
                        st.download_button(
                            label=f"⬇️ Download No Background",
                            data=img_buffer_nobg.getvalue(),
                            file_name=download_filename_nobg,
                            mime="image/png",
                            key=f"download_nobg_{i}"
                        )
                    
                    with col_dl2:
                        # Download composited version
                        download_filename_comp = f"{name_without_ext}_new_bg.png"
                        img_buffer_comp = io.BytesIO()
                        st.session_state.composited_images[i].save(img_buffer_comp, format='PNG')
                        
                        st.download_button(
                            label=f"⬇️ Download With Background",
                            data=img_buffer_comp.getvalue(),
                            file_name=download_filename_comp,
                            mime="image/png",
                            key=f"download_comp_{i}"
                        )
                else:
                    # Standard two-column layout when no background compositing
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Original**")
                        st.image(original_img, use_container_width=True)
                    
                    with col2:
                        st.markdown("**Background Removed**")
                        st.image(processed_img, use_container_width=True)
                    
                    # Download button for individual image
                    name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
                    download_filename = f"{name_without_ext}_no_bg.png"
                    
                    img_buffer = io.BytesIO()
                    processed_img.save(img_buffer, format='PNG')
                    
                    st.download_button(
                        label=f"⬇️ Download {download_filename}",
                        data=img_buffer.getvalue(),
                        file_name=download_filename,
                        mime="image/png",
                        key=f"download_{i}"
                    )
                
                if i < len(st.session_state.processed_images) - 1:
                    st.divider()
    
    else:
        # Show placeholder when no files uploaded
        st.info("👆 Please upload one or more images to get started!")
        
        # Example images section
        st.header("✨ What you can do")
        st.markdown("""
        **Perfect for:**
        - 🛍️ E-commerce product photos
        - 👤 Professional headshots
        - 🎨 Creative design projects
        - 📱 Social media content
        - 🖼️ Digital art and illustrations
        
        **Features:**
        - ⚡ Fast AI-powered processing
        - 🔄 Batch processing support
        - 📱 Mobile-friendly interface
        - 💾 High-quality PNG output
        - 🔒 Secure local processing
        """)

if __name__ == "__main__":
    main()
