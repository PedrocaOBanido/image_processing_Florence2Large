import os
import requests
from bs4 import BeautifulSoup
import base64
import json
import re 
from urllib.parse import urljoin 

# --- Configuration ---
SCRAPE_URL = "https://intern.aiaxuropenings.com/scrape/e0681d59-2dbb-4b32-91b6-1e4da0c4a0f4"
API_CHAT_COMPLETIONS_URL = "https://intern.aiaxuropenings.com/v1/chat/completions"
API_SUBMIT_RESPONSE_URL = "https://intern.aiaxuropenings.com/api/submit-response"
TOKEN = os.getenv("AUTH_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

MODEL_NAME = "microsoft-florence-2-large"
PROMPT_TAG = "<DETAILED_CAPTION>"

def scrape_image():
    """
    Scrapes the image from the specified URL.
    Returns the image content (bytes) and its content type.
    """
    print(f"Step 1: Scraping image from {SCRAPE_URL}...")
    try:
        response = requests.get(SCRAPE_URL, timeout=30)
        response.raise_for_status() # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the image tag - adjust if the structure is different
        img_tag = soup.find('img')
        if not img_tag or not img_tag.get('src'):
            print("ERROR: Image tag or src attribute not found on the page.")
            return None, None

        image_src = img_tag['src']
        print(f"Found image src (first 100 chars): {image_src[:100]}...")

        if image_src.startswith('data:'):
            print("Image source is a data URL. Parsing directly.")
            try:
                # Format: data:[<mediatype>][;base64],<data>
                header, encoded_data = image_src.split(',', 1)
                
                # Extract mediatype using regex
                match = re.search(r'data:([^;]+)(;base64)?', header)
                if not match:
                    print("ERROR: Could not extract mediatype from data URL header.")
                    return None, None
                
                content_type = match.group(1).strip() # e.g., "image/jpeg"
                
                if ';base64' in header:
                    image_content = base64.b64decode(encoded_data)
                    print(f"Image parsed from base64 data URL successfully ({len(image_content)} bytes, type: {content_type}).")
                    return image_content, content_type
                else:
                    # Handle URL-encoded data if necessary (less common for images this large)
                    from urllib.parse import unquote_to_bytes # Local import for less common case
                    image_content = unquote_to_bytes(encoded_data)
                    print(f"Image parsed from URL-encoded data URL successfully ({len(image_content)} bytes, type: {content_type}).")
                    return image_content, content_type

            except ValueError as e:
                print(f"ERROR parsing data URL (ValueError): {e}")
                return None, None
            except Exception as e:
                print(f"An unexpected error occurred while parsing data URL: {e}")
                return None, None
        else:
            # It's a regular URL (absolute or relative)
            image_url_absolute = urljoin(SCRAPE_URL, image_src) # Use urljoin for robust URL construction
            print(f"Image source is a standard URL. Downloading from: {image_url_absolute}")
            
            image_response = requests.get(image_url_absolute, timeout=30)
            image_response.raise_for_status()
            image_content = image_response.content
            # Try to get content_type from header, default to 'image/jpeg' or try to infer if possible
            content_type = image_response.headers.get('Content-Type', 'image/jpeg') 
            
            print(f"Image downloaded successfully ({len(image_content)} bytes, type: {content_type}).")
            return image_content, content_type

    except requests.exceptions.RequestException as e:
        print(f"ERROR in Step 1 (Scraping/Downloading): {e}")
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred in Step 1: {e}")
        return None, None

def send_image_for_inference(image_content, image_content_type):
    """
    Sends the image to the AI model for inference.
    Returns the JSON response from the model.
    """
    if not image_content or not image_content_type:
        print("ERROR: Cannot proceed to Step 2 without image content.")
        return None

    print(f"Step 2: Sending image for inference to {API_CHAT_COMPLETIONS_URL}...")
    try:
        base64_image = base64.b64encode(image_content).decode('utf-8')
        image_data_url = f"data:{image_content_type};base64,{base64_image}"

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": PROMPT_TAG},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data_url
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500 
        }

        response = requests.post(API_CHAT_COMPLETIONS_URL, headers=HEADERS, json=payload, timeout=60)
        print(f"API Chat Completions Status Code: {response.status_code}")

        response.raise_for_status()
        model_response_json = response.json()
        print("Inference successful. Model response received.")
        return model_response_json

    except requests.exceptions.RequestException as e:
        print(f"ERROR in Step 2 (Inference): {e}")
        if 'response' in locals() and response is not None:
            print(f"Response content: {response.text}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR in Step 2 (JSON Decode): {e}")
        if 'response' in locals() and response is not None:
            print(f"Response content that failed to parse: {response.text}")
        return None


def submit_model_response(model_response_json):
    """
    Submits the model's JSON response to the submission URL.
    """
    if not model_response_json:
        print("ERROR: Cannot proceed to Step 3 without model response.")
        return False

    print(f"Step 3: Submitting model response to {API_SUBMIT_RESPONSE_URL}...")
    try:
        response = requests.post(API_SUBMIT_RESPONSE_URL, headers=HEADERS, json=model_response_json, timeout=30)
        print(f"API Submit Response Status Code: {response.status_code}")
        print(f"API Submit Response Text: {response.text}") 

        response.raise_for_status()
        print("Model response submitted successfully.")
        
        if "sucesso" in response.text.lower() or "correct" in response.text.lower() or response.status_code == 200:
             print("Submission seems to be confirmed as correct by the server.")
             return True
        else:
            print("Submission response received, but success not explicitly confirmed. Please check server message.")
            return False 

    except requests.exceptions.RequestException as e:
        print(f"ERROR in Step 3 (Submission): {e}")
        if 'response' in locals() and response is not None:
            print(f"Response content: {response.text}")
        return False
    except json.JSONDecodeError as e: 
        print(f"ERROR in Step 3 (JSON Decode of server response): {e}")
        print(f"Response content that failed to parse: {response.text}")
        return False

def main():
    print("--- Starting Technical Evaluation Script ---")

    image_bytes, image_type = scrape_image()

    if image_bytes and image_type:
        model_output_json = send_image_for_inference(image_bytes, image_type)

        if model_output_json:
            submission_successful = submit_model_response(model_output_json)

            if submission_successful:
                print("\n--- Script Execution Completed Successfully! ---")
            else:
                print("Please review the logs and the API response for Step 3.")
        else:
            print("\n--- Script Execution Failed at Step 2 (Model Inference). ---")
    else:
        print("\n--- Script Execution Failed at Step 1 (Image Scraping/Parsing). ---")

    print("\n--- End of Script ---")

if __name__ == "__main__":
    main()