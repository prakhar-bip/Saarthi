import os
from google import genai
from google.genai import types

project_id = "project-e3e4dcb5-593d-4e61-9a8"
location = "us-central1"

print("Setting environment variables...")
os.environ["GEMINI_VERTEX_PROJECT"] = project_id
os.environ["GEMINI_VERTEX_LOCATION"] = location
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"

if "GEMINI_API_KEY" in os.environ:
    del os.environ["GEMINI_API_KEY"]

print("Initializing GenAI Client with vertexai=True...")
try:
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location
    )
    print("GenAI Client initialized successfully!")
    
    # Try generating a simple test
    print("Testing generate_content with gemini-2.5-flash...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Hi, say hello!",
    )
    print("Response text:", response.text)
except Exception as e:
    print("Error during Vertex AI test:", e)
