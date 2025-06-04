import gradio as gr
from PIL import Image
from rembg import remove
import numpy as np
import io
import torch
import traceback # Import traceback for detailed error logging

# Determine device
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {DEVICE}") # Use print for Gradio logs

def remove_background_gradio(image: Image.Image) -> Image.Image:
    """Remove background from image using rembg for Gradio"""
    if image is None:
        print("Received None image input, returning None")
        return None

    print(f"Received image input of type: {type(image)}")
    print(f"Image mode: {image.mode}, size: {image.size}")

    try:
        print("Starting background removal process")
        
        # Ensure image is in a compatible format for rembg if necessary
        # rembg works well with RGBA, but PIL Image might be in other modes.
        # Let's convert to RGBA just in case.
        if image.mode != 'RGBA':
             print(f"Converting image from {image.mode} to RGBA")
             image = image.convert('RGBA')

        # Convert PIL image to bytes (rembg input format)
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG') # rembg expects PNG bytes
        img_byte_arr = img_byte_arr.getvalue()
        print(f"Converted image to bytes, size: {len(img_byte_arr)}")

        # Remove background
        print(f"Calling rembg.remove with device: {DEVICE}")
        output_bytes = remove(img_byte_arr, device=DEVICE) # rembg returns bytes
        print(f"rembg.remove returned bytes, size: {len(output_bytes) if output_bytes is not None else 'None'}")

        # Convert back to PIL Image
        if output_bytes is not None:
            result_image = Image.open(io.BytesIO(output_bytes))
            print(f"Background removal completed successfully, result image mode: {result_image.mode}")
            return result_image
        else:
            print("rembg.remove returned None or empty bytes.")
            return None # Ensure we return None if rembg failed

    except Exception as e:
        print(f"Error during background removal: {e}")
        print(traceback.format_exc()) # Print full traceback
        return None # Always return None or an image in case of error


# Define the Gradio interface
# We'll have one input (image) and one output (image)
interface = gr.Interface(
    fn=remove_background_gradio,
    inputs=gr.Image(type="pil", label="Upload Image"),
    outputs=gr.Image(type="pil", label="Background Removed Image"),
    title="AI Background Remover",
    description="Upload an image to automatically remove the background using rembg.",
    allow_flagging=None # Changed from "never" to None
)

# Launch the interface
if __name__ == "__main__":
    interface.launch()
