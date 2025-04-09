# Week 5

- [Week 5](#week-5)
  - [Configuring TTS with Google Text-to-Speech](#configuring-tts-with-google-text-to-speech)
    - [Create a Google Cloud Project (If You Don't Already Have One)\*\*](#create-a-google-cloud-project-if-you-dont-already-have-one)
    - [Enable the Text-to-Speech API](#enable-the-text-to-speech-api)
    - [Create a Service Account](#create-a-service-account)
    - [Create a Service Account Key (JSON File)\*\*](#create-a-service-account-key-json-file)
    - [Set the GOOGLE\_APPLICATION\_CREDENTIALS Environment Variable\*\*](#set-the-google_application_credentials-environment-variable)
      - [Set the environment variable](#set-the-environment-variable)
        - [Linux/macOS](#linuxmacos)
        - [For Windows](#for-windows)
      - [Important Notes](#important-notes)
    - [Sample Code to Implement Google Text to Speech](#sample-code-to-implement-google-text-to-speech)

## Configuring TTS with Google Text-to-Speech

I had been using Amazon Polly for Text-to-Speech (TTS) generation. However, I found that it was not working well for Urdu. I decided to switch to Google Text-to-Speech (TTS) generation.

I followed the instructions in the [Google Cloud documentation](https://cloud.google.com/text-to-speech/docs/quickstart) to set up the TTS service.

Okay, here's how to create and set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to authenticate with Google Cloud Platform (GCP) using a service account:

### Create a Google Cloud Project (If You Don't Already Have One)**

- Go to the Google Cloud Console: [https://console.cloud.google.com/](https://console.cloud.google.com/)
- If you don't have a project, create one:
  - Click the project selection dropdown at the top.
  - Click "New Project".
  - Enter a project name and optionally a project ID.
  - Click "Create".

### Enable the Text-to-Speech API

- In the Google Cloud Console, go to the API Library: [https://console.cloud.google.com/apis/library](https://console.cloud.google.com/apis/library)
- Search for "Cloud Text-to-Speech API".
- Select the API.
- Click "Enable".

### Create a Service Account

- In the Google Cloud Console, go to the Service Accounts page: [https://console.cloud.google.com/iam-admin/serviceaccounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
- Click "Create Service Account".
- **Service account details:**
  - Enter a service account name (e.g., "urdu-tts-service-account").
  - Optionally, enter a description.
  - Click "Create".
- **Grant this service account access to the project (Important!).**
  - Select a role that has access to the Cloud Text-to-Speech API.  **The "Cloud Text-to-Speech API Client" role is usually sufficient.**  If you need broader access, you could use "Editor" but be aware of the principle of least privilege (granting only the necessary permissions).
  - Click "Continue".
- **Grant users access to this service account (Optional):**
  - You can optionally grant other users or service accounts access to impersonate this service account.  This is typically not needed for a basic setup.
  - Click "Done".

### Create a Service Account Key (JSON File)**

- In the Service Accounts page, find the service account you just created.
- Click on the service account's email address (the identifier that looks like `your-service-account@your-project-id.iam.gserviceaccount.com`).
- Go to the "Keys" tab.
- Click "Add Key" and select "Create new key".
- Choose **JSON** as the key type.  This is the most common and recommended format for local development.
- Click "Create".

A JSON file containing the service account credentials will be downloaded to your computer.  **Treat this file with extreme care.  It's equivalent to a password.  Do not share it publicly, commit it to version control, or store it in an insecure location.**

### Set the GOOGLE_APPLICATION_CREDENTIALS Environment Variable**

This is the final step.  You need to tell your Python application where to find the JSON key file.

**Determine the path to the JSON file.**  Make sure you know the absolute path to the downloaded file on your system (e.g., `/Users/yourname/Downloads/your-project-id-1234567890ab.json`).

#### Set the environment variable

##### Linux/macOS

    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
    ```

    Replace `/path/to/your/service-account-key.json` with the actual path to your JSON file.  **Important:**  This will only set the environment variable for the *current* terminal session.  To make it permanent, add this line to your `.bashrc`, `.zshrc`, or other shell configuration file and then source the file (e.g., `source ~/.bashrc`).

##### For Windows

    * **Using the Command Prompt:**

        ```cmd
        set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account-key.json
        ```

        Replace `C:\path\to\your\service-account-key.json` with the actual path.  This will only set the variable for the current command prompt session.
    * **Using the System Properties (Permanent):**

        1. Search for "Environment Variables" in the Windows search bar.
        2. Click "Edit the system environment variables".
        3. Click "Environment Variables...".
        4. Under "System variables", click "New...".
        5. Variable name: `GOOGLE_APPLICATION_CREDENTIALS`
        6. Variable value: `C:\path\to\your\service-account-key.json`
        7. Click "OK" on all the dialogs.

#### Important Notes

- **Security:** Keep the JSON key file secure.
- **Scope:**  Double-check the role you assigned to the service account to ensure it has the necessary permissions to call the Text-to-Speech API.
- **Restart:**  After setting the environment variable, you might need to restart your terminal or IDE for the changes to take effect.
- **Multiple Projects:** If you're working with multiple GCP projects, make sure you're using the correct service account key for the project you're accessing.
- **Alternative Authentication:** While `GOOGLE_APPLICATION_CREDENTIALS` is the recommended way for local development and many server-side applications, there are other authentication methods for different environments (e.g., using the Metadata Server on Google Compute Engine).
- **Python Code:** In your Python code, if you don't set the environment variable, you can authenticate directly (but less securely) within the code:

      ```python
      from google.oauth2 import service_account

      credentials = service_account.Credentials.from_service_account_file("path/to/your/service-account-key.json")

      # Now use the `credentials` object when instantiating the client
      client = texttospeech.TextToSpeechClient(credentials=credentials)
      ```

**However, as mentioned before, avoid hardcoding credentials in your code whenever possible.  Use the environment variable approach for better security.**

By following these steps, you'll create a service account, generate a key file, and set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable, allowing your Python application to authenticate with Google Cloud and use the Text-to-Speech API.

### Sample Code to Implement Google Text to Speech

Once you have configured TTS in Google, you can run the following code which will generate a MP3 file from a Urdu text.

Make sure that you do not commit the file `service-account-key.json` to version control. You should add it to your GitIgnore file to do so.

    ```python
    from google.cloud import texttospeech
    import os

    # Set your Google Cloud credentials (follow GCP instructions)
    # Method 1: Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
    # os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "path/to/your/service-account-key.json"

    # Method 2:  (Less secure, use only for testing) Authenticate in the code
    # from google.oauth2 import service_account
    # credentials = service_account.Credentials.from_service_account_file("path/to/your/service-account-key.json")

    def urdu_tts(text, output_filename="output.mp3"):
        """Converts Urdu text to speech and saves it to an MP3 file."""

        # Instantiates a client
        client = texttospeech.TextToSpeechClient()

        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request, select the language code ("ur-PK") and the ssml
        # voice gender ("neutral")
        voice = texttospeech.VoiceSelectionParams(
            language_code="ur-PK",  # Urdu (Pakistan)
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
        )

        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        # Perform the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # The response's audio_content is binary.
        with open(output_filename, "wb") as out:
            # Write the response to the output file.
            out.write(response.audio_content)
            print(f'Audio content written to file "{output_filename}"')


    # Example Usage:
    urdu_text = "یہ ایک اردو تحریر ہے جو تقریر میں تبدیل ہو جائے گی۔" # This is an Urdu text that will be converted to speech.
    urdu_tts(urdu_text, "urdu_output.mp3")
    ```
