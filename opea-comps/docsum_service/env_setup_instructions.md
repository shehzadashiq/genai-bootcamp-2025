# Document Summary Service Environment Setup

To fix the error `AWS_BUCKET_NAME environment variable is required`, you need to create a `.env` file in this directory with the following content:

```
# AWS Credentials - Required for AWS services
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_DEFAULT_REGION=us-east-1
AWS_REGION=us-east-1
AWS_BUCKET_NAME=your-bucket-name  # This is the missing variable causing the error

# Bedrock Configuration - Required for LLM services
BEDROCK_MODEL_ID=anthropic.claude-v2
BEDROCK_REGION=us-east-1

# Other configuration variables as needed
```

## Instructions:

1. Create a new file named `.env` in this directory
2. Copy the above content into the file
3. Replace the placeholder values with your actual AWS credentials
4. Make sure to set a valid S3 bucket name for `AWS_BUCKET_NAME`
5. Restart your Docker containers with `docker-compose down` and `docker-compose up`

Note: The `.env` file is excluded from version control for security reasons, so you'll need to create it manually.
