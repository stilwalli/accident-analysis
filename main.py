# main.py
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import os
import base64
import mimetypes
import shutil
from pathlib import Path
from werkzeug.utils import secure_filename
from google.cloud import aiplatform
from google.cloud import storage
import vertexai
from vertexai.generative_models import GenerativeModel, Part
# For actual implementation, you would use these imports
# from google.cloud import aiplatform
# from google.protobuf import json_format
# from google.protobuf.struct_pb2 import Value

app = FastAPI(title="Video Analysis App")

# Configuration
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"mp4", "avi", "mov", "wmv", "mkv"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/img', exist_ok=True)
os.makedirs('static/demo', exist_ok=True)  # For the demo video

# Set up static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Create default CSS file if it doesn't exist
css_path = 'static/css/style.css'
if not os.path.exists(css_path):
    with open(css_path, 'w') as f:
        f.write("""
.logo {
    max-height: 80px;
    margin-bottom: 15px;
}

.card {
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    margin-bottom: 20px;
}

.analysis-results {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 5px;
    border: 1px solid #dee2e6;
    max-height: 300px;
    overflow-y: auto;
    white-space: pre-wrap;
}
""")

# Create default logo file if it doesn't exist
logo_path = 'static/img/car-logo.png'
if not os.path.exists(logo_path):
    # Create a simple car logo SVG
    svg_content = """<svg width="200" height="100" xmlns="http://www.w3.org/2000/svg">
  <path d="M20,70 Q40,80 100,80 Q160,80 180,70 L180,60 Q160,50 100,50 Q40,50 20,60 Z" fill="#0066cc" />
  <path d="M50,50 Q75,30 100,30 Q125,30 150,50" fill="none" stroke="#0066cc" stroke-width="4" />
  <circle cx="50" cy="80" r="10" fill="#333" />
  <circle cx="150" cy="80" r="10" fill="#333" />
  <circle cx="50" cy="80" r="5" fill="#777" />
  <circle cx="150" cy="80" r="5" fill="#777" />
  <text x="100" y="65" text-anchor="middle" font-family="Arial, sans-serif" font-weight="bold" font-size="14" fill="white">TURBO</text>
  <text x="100" y="95" text-anchor="middle" font-family="Arial, sans-serif" font-weight="bold" font-size="14" fill="#333">MOTORS</text>
</svg>"""
    
    # Write the SVG to a file with .png extension
    with open(logo_path, 'w') as f:
        f.write(svg_content)
    
    print(f"Created placeholder logo at {logo_path}. In a production app, you would want to convert this SVG to PNG.")

# Create a sample demo video file if it doesn't exist
demo_video_path = 'static/demo/sample-video.mp4'
if not os.path.exists(demo_video_path):
    # Create an empty file as a placeholder
    # In a production app, you'd want to include a real sample video
    with open(demo_video_path, 'w') as f:
        f.write("This is a placeholder for a demo video. Replace with a real MP4 file.")
    
    print(f"Created placeholder demo video at {demo_video_path}. Replace with a real MP4 file.")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def upload_to_gcs(local_file_path, bucket_name, destination_blob_name=None):
    """
    Uploads a file to Google Cloud Storage and returns the full GCS path.
    
    Args:
        local_file_path: Path to the local file to upload
        bucket_name: Name of the GCS bucket
        destination_blob_name: Name for the file in GCS (defaults to filename)
    
    Returns:
        Full GCS path to the uploaded file (gs://bucket-name/file-path)
    """
    try:
        # Initialize logging
        print(f"Starting upload for: {local_file_path}")
        
        # Create the storage client
        storage_client = storage.Client()
        print(1)
        
        # Get the bucket
        bucket = storage_client.bucket(bucket_name)
        print(2)
        # If no destination name provided, use the original filename
        if not destination_blob_name:
            destination_blob_name = os.path.basename(local_file_path)
        
        # Create a blob and upload the file
        blob = bucket.blob(destination_blob_name)
        print(3)
        blob.upload_from_filename(local_file_path)
        
        # Generate the full GCS path
        gcs_path = f"gs://{bucket_name}/{destination_blob_name}"
        
        print(f"File {local_file_path} uploaded to {gcs_path}")
        
        return gcs_path
    
    except Exception as e:
        error_msg = f"Error uploading file to GCS: {str(e)}"
        print(error_msg, exc_info=True)
        raise Exception(error_msg)
    
def upload(video_path):
    upload_to_gcs(video_path, "video-anal0424")

def analyze_video_with_vertex_ai(video_path):
    """
    Analyze a video using Google's Vertex AI Gemini model.
    """
    # Vertex AI settings
    PROJECT_ID = "scratchzone"  # Replace with your Google Cloud project ID
    LOCATION = "us-central1"  # Replace with your preferred region
    MODEL_NAME = "gemini-2.0-flash-001"
    RES = ""
    
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        model = GenerativeModel(MODEL_NAME)

        video_part = Part.from_uri(
        uri=video_path,
        mime_type="video/mp4"  # Specify the MIME type for the video
        )

     # 4. Define your prompt
        prompt_text = """As a visual inspector for Rent-A-Car, you are meticulously examining a [Specify if before or after rental] [Specify the Color, e.g., silver, deep blue, matte black] [Specify the Brand, e.g., Toyota, Ford, BMW] [Specify the Model, e.g., Camry, F-150, 3 Series].

        Describe the exterior condition in detail, focusing on the following:



        Body Panels: Note any scratches (describe location, length, and depth - e.g., 'light scratch, 2 inches long, near the driver's side rear door handle'), dents (describe size and location - e.g., 'small dent, about the size of a quarter, on the front bumper'), paint chips (describe location and size), or misaligned panels. Pay close attention to the bumpers, doors, hood, trunk, and roof.

        Glass: Inspect the windshield, side windows, and rear window for any cracks (describe length and location), chips, or excessive scratches. Check the condition of the wiper blades.

        Lights: Examine all headlights, taillights, brake lights, and turn signals for cracks, damage, or if they are functioning properly (if applicable at this stage). Note any condensation inside the light housings.

        Wheels and Tires: Describe the condition of the wheels (e.g., curb rash, scratches, dents). Assess the tire tread depth (general assessment - good, fair, low) and note any visible damage to the sidewalls (cuts, bulges).

        Trim and Details: Check the condition of the side mirrors (cracks, functionality), door handles, badges, and any other exterior trim pieces for damage or missing parts."""

            # 5. Generate content
    
            # For multimodal prompts, pass a list of parts (video, text, etc.)
        response = model.generate_content([video_part, prompt_text])

        # 6. Print the response
        print("\n--- Analysis Result ---")
        if response.candidates and response.candidates[0].content.parts:
            print(response.text)
            RES = response.text
        else:
            print("No text response received or response structure unexpected.")
            print("Full response:", response)
            RES = response
        
        # Extract the text response
        analysis_result = RES
        print("Analysis completed successfully")
        
        return analysis_result
       
            
    except Exception as e:
        error_msg = f"Error analyzing video: {str(e)}"
        print(error_msg, exc_info=True)
        return error_msg

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "show_results": False}
    )

@app.post("/upload")
async def upload_file(
    request: Request,
    video: UploadFile = File(...),
):
    print(111)
    # Save the uploaded file
    filename = secure_filename(video.filename)
    print(":filename", filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    print("file_path: ", file_path)

    print("test2232332")
    
    # Analyze the video
    #analysis_result = analyze_video_with_vertex_ai(file_path)
    uploadPath = upload_to_gcs(file_path, "video-anal0424")
    print(":Upload Path: ", uploadPath)
    analysis_result = analyze_video_with_vertex_ai(uploadPath)
    
    # Render the template with results
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "filename": filename,
            "analysis": analysis_result,
            "show_results": True
        }
    )

# For development server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)