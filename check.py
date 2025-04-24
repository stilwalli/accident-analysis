import vertexai
from vertexai.generative_models import GenerativeModel, Part

# --- Configuration ---
PROJECT_ID = "scratchzone"  # <--- REPLACE with your Google Cloud Project ID
LOCATION = "us-central1"      # <--- REPLACE with your GCP region (e.g., "us-central1")
VIDEO_GCS_URI = "gs://video-anal0424/download_2.mp4"  # <--- REPLACE with GCS path to your MP4

# Specify a Gemini 1.5 model.
# Use "gemini-1.5-flash-001" for faster, cost-effective responses for many tasks,
# or "gemini-1.5-pro-001" for more complex tasks.
MODEL_NAME = "gemini-2.0-flash-001"

# --- Main Script ---
try:
    # 1. Initialize Vertex AI
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # 2. Load the generative model
    model = GenerativeModel(MODEL_NAME)

    # 3. Prepare the video input from GCS URI
    video_part = Part.from_uri(
        uri=VIDEO_GCS_URI,
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
    print(f"Analyzing video: {VIDEO_GCS_URI} with model {MODEL_NAME}...")
    # For multimodal prompts, pass a list of parts (video, text, etc.)
    response = model.generate_content([video_part, prompt_text])

    # 6. Print the response
    print("\n--- Analysis Result ---")
    if response.candidates and response.candidates[0].content.parts:
        print(response.text)
    else:
        print("No text response received or response structure unexpected.")
        print("Full response:", response)


except Exception as e:
    print(f"An error occurred: {e}")
