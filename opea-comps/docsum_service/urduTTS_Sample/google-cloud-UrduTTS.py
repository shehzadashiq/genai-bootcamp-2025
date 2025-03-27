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
urdu_text = '''
خلاصہ:

اسپیکر اور اس کا دوست جوراسک ورلڈ دیکھنے گئے۔ فلم کے پہلے چند منٹ میں، ایک کردار سے مراد ایک ڈایناسور ہے جسے “پاکیسورس” کہا جاتا ہے جو ڈھیلا ہوچکا ہے۔ اس سے اسپیکر اور اس کے دوست کو ناراض کیا گیا ہے، جو پاکستانی ہیں۔ انہیں لگتا ہے کہ یہ منفی سٹیریٹائپ کو فروغ دیتا پوری فلم میں وہ ایک سفید جوڑے اور ایک بوڑھے سفید آدمی کی ناراض نظر آتی ہیں۔ فلم کے بعد، اسپیکر زور سے اعلان کرتا ہے کہ پاکیسورس جیسی کوئی چیز نہیں ہے، اور بوڑھا آدمی اسے دیکھتا ہے اور دکھاتا ہے کہ وہاں موجود ہے۔ اسپیکر بہت ناراض ہوجاتا ہے، کہتا ہے کہ یہ ناقابل قبول ہے، اور لوگوں کو اس نسل پرستی کی تصویر پر جوراسک ورلڈ کو بائیکاٹ کرنے کا مطالبہ کرتا ہے۔ انہوں نے زور دیا کہ صرف اس وجہ سے کہ پاکستانیوں کو دانتوں کے مسائل ہوسکتے ہیں اس کا مطلب یہ نہیں ہے کہ آپ ان کے نام سے ڈایناسور کا نام دے سکتے ہیں۔
'''
urdu_tts(urdu_text, "urdu_output.mp3")