"""
Test AWS service access for the Language Listening Application.
Tests Bedrock, Polly, and Translate services.
"""
import boto3
from botocore.exceptions import ClientError
import json
from config import aws_config

def test_bedrock_access():
    """Test access to AWS Bedrock service."""
    try:
        print("\nTesting Bedrock Access...")
        
        # Test base Bedrock service
        bedrock = boto3.client(
            'bedrock',
            region_name=aws_config.AWS_REGION
        )
        response = bedrock.list_foundation_models()
        models = [m['modelId'] for m in response.get('modelSummaries', [])]
        print(f"✓ Successfully listed Bedrock models")
        print(f"Available models: {json.dumps(models, indent=2)}")
        
        # Test Bedrock Runtime
        bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=aws_config.AWS_REGION
        )
        print("✓ Successfully initialized Bedrock Runtime")
        
        return True, "Bedrock access verified"
    except ClientError as e:
        error = e.response['Error']
        return False, f"Bedrock error: {error['Code']} - {error['Message']}"
    except Exception as e:
        return False, f"Bedrock error: {str(e)}"

def test_polly_access():
    """Test access to AWS Polly service."""
    try:
        print("\nTesting Polly Access...")
        polly = boto3.client(
            'polly',
            region_name=aws_config.AWS_REGION
        )
        voices = polly.describe_voices()
        print(f"✓ Successfully listed Polly voices")
        print(f"Number of available voices: {len(voices['Voices'])}")
        return True, "Polly access verified"
    except ClientError as e:
        error = e.response['Error']
        return False, f"Polly error: {error['Code']} - {error['Message']}"
    except Exception as e:
        return False, f"Polly error: {str(e)}"

def test_translate_access():
    """Test access to AWS Translate service."""
    try:
        print("\nTesting Translate Access...")
        translate = boto3.client(
            'translate',
            region_name=aws_config.AWS_REGION
        )
        languages = translate.list_languages()
        print(f"✓ Successfully listed supported languages")
        print(f"Number of supported languages: {len(languages['Languages'])}")
        return True, "Translate access verified"
    except ClientError as e:
        error = e.response['Error']
        return False, f"Translate error: {error['Code']} - {error['Message']}"
    except Exception as e:
        return False, f"Translate error: {str(e)}"

def main():
    """Run all AWS service tests."""
    print("Testing AWS Service Access")
    print("=" * 50)
    
    # Test Bedrock
    success, message = test_bedrock_access()
    if not success:
        print(f"❌ {message}")
        return
    
    # Test Polly
    success, message = test_polly_access()
    if not success:
        print(f"❌ {message}")
        return
    
    # Test Translate
    success, message = test_translate_access()
    if not success:
        print(f"❌ {message}")
        return
    
    print("\n✓ All AWS services verified successfully!")

if __name__ == "__main__":
    main()
