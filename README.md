# Technical Evaluation Script Documentation

## Overview

This script automates a three-step process designed for a technical evaluation:
1.  **Scrape an image** from a specified URL.
2.  **Send the scraped image** to an AI model (Microsoft Florence-2 Large) for inference (e.g., to get a detailed caption).
3.  **Submit the AI model's response** to another API endpoint for validation.

The script uses the `requests` library for HTTP communication, `BeautifulSoup` for HTML parsing,
`base64` for image encoding, `json` for handling API payloads and responses, `re` for
parsing data URLs, and `urllib.parse` for URL manipulation.

## Configuration

The script requires several constants to be defined at the beginning:

-   `SCRAPE_URL`: The URL from which to scrape the image.
-   `API_CHAT_COMPLETIONS_URL`: The endpoint for the AI model's chat completion API.
-   `API_SUBMIT_RESPONSE_URL`: The endpoint to submit the AI model's response.
-   `TOKEN`: An authorization bearer token required for API authentication. **This is a critical piece of information and should be kept confidential.**
-   `HEADERS`: A dictionary containing HTTP headers, including the Authorization header formatted with the `TOKEN`.
-   `MODEL_NAME`: The specific AI model to be used for inference (e.g., `"microsoft-florence-2-large"`).
-   `PROMPT_TAG`: A specific tag or instruction sent to the AI model along with the image (e.g., `"<DETAILED_CAPTION>"`).

## Workflow

The script executes sequentially through its main functions:

1.  **`main()` function**: Orchestrates the entire process.
2.  **`step_1_scrape_image()`**:
    *   Fetches the HTML content from `SCRAPE_URL`.
    *   Parses the HTML to find an `<img>` tag.
    *   Extracts the image source (`src` attribute).
    *   Handles two types of image sources:
        *   **Data URLs** (e.g., `data:image/jpeg;base64,...`): Decodes the base64 or URL-encoded image data directly and determines the content type.
        *   **Standard URLs** (relative or absolute): Constructs an absolute URL if necessary and downloads the image content. The content type is typically inferred from the response headers or defaults to 'image/jpeg'.
    *   Returns the image content as bytes and its content type string.
3.  **`step_2_send_image_for_inference(image_content, image_content_type)`**:
    *   Takes the image bytes and content type from Step 1.
    *   Base64 encodes the image content.
    *   Constructs a data URL (e.g., `data:image/jpeg;base64,...`) from the encoded image.
    *   Prepares a JSON payload for the `API_CHAT_COMPLETIONS_URL`. This payload includes:
        *   The `MODEL_NAME`.
        *   A message structure containing the `PROMPT_TAG` as text and the image data URL.
        *   `max_tokens` to limit the response length.
    *   Sends a POST request to the AI model API with the payload and `HEADERS`.
    *   Returns the JSON response from the AI model.
4.  **`step_3_submit_model_response(model_response_json)`**:
    *   Takes the JSON response from the AI model (from Step 2).
    *   Sends this JSON response as a payload in a POST request to the `API_SUBMIT_RESPONSE_URL` with the `HEADERS`.
    *   Checks the API's response for success indicators (e.g., "sucesso", "correct", or HTTP status 200).
    *   Returns `True` if the submission appears successful, `False` otherwise.

The `main()` function prints status messages and error details to the console throughout its execution.
If all steps complete successfully, it provides instructions for the user to proceed with the next part of the evaluation,
which typically involves manually submitting the script file on a webpage.

## Functions

### `step_1_scrape_image()`
-   **Purpose**: Scrapes an image from `SCRAPE_URL`.
-   **Returns**: A tuple `(image_content, content_type)` where `image_content` is bytes and `content_type` is a string (e.g., 'image/png'), or `(None, None)` on failure.
-   **Details**: Handles both direct image URLs and base64 encoded data URLs within `<img>` tags. Uses `urljoin` for robust construction of absolute URLs from relative paths.

### `step_2_send_image_for_inference(image_content, image_content_type)`
-   **Purpose**: Sends the scraped image to an AI model for analysis.
-   **Args**:
    -   `image_content` (bytes): The raw bytes of the image.
    -   `image_content_type` (str): The MIME type of the image (e.g., 'image/jpeg').
-   **Returns**: A dictionary representing the JSON response from the AI model, or `None` on failure.
-   **Details**: Encodes the image to base64 and formats it as a data URL within the API request payload.

### `step_3_submit_model_response(model_response_json)`
-   **Purpose**: Submits the AI model's response to a validation endpoint.
-   **Args**:
    -   `model_response_json` (dict): The JSON response received from the AI model.
-   **Returns**: `True` if the submission is considered successful, `False` otherwise.
-   **Details**: Posts the model's JSON directly. Checks response text and status code for success.

### `main()`
-   **Purpose**: The main entry point of the script. Orchestrates the calls to the three steps.
-   **Details**: Prints progress and results to the console. Provides guidance on next steps if successful.

## Error Handling

Each step function includes `try-except` blocks to catch common errors:
-   `requests.exceptions.RequestException`: For network issues, HTTP errors, or timeouts.
-   `ValueError`: Specifically for issues parsing data URLs in `step_1`.
-   `json.JSONDecodeError`: If API responses are not valid JSON.
-   Generic `Exception`: For any other unexpected errors.

Error messages are printed to the console, often including the HTTP response text if available, to aid in debugging.

## Dependencies

-   `requests`: For making HTTP requests.
-   `beautifulsoup4`: For parsing HTML.
(Standard Python libraries: `base64`, `json`, `re`, `urllib.parse`)

## Usage

1.  Ensure all required libraries (`requests`, `beautifulsoup4`) are installed:
    ```bash
    pip install requests beautifulsoup4
    ```
2.  Verify and update the configuration constants at the top of the script, especially `TOKEN`.
3.  Run the script from the command line:
    ```bash
    python main.py
    ```
4.  Observe the console output for progress and any error messages. If successful, follow the on-screen instructions regarding the next part of the evaluation.