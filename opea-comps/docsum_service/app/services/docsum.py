import logging
import boto3
import os
import json
from typing import Optional
import re
from bs4 import BeautifulSoup
import requests
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class Summarizer:
    def __init__(self):
        self.client = boto3.client('bedrock-runtime',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        logger.info("Summarizer service initialized")

    def _clean_content(self, html_content: str) -> str:
        """Clean HTML content by removing navigation, footers, and suggested articles."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove common elements that contain links to other articles
            unwanted_selectors = [
                'nav', 'footer', 'header',  # Navigation and footer elements
                '[class*="related"]', '[class*="suggested"]', '[class*="recommendation"]',  # Related/suggested content
                '[class*="sidebar"]', '[class*="promo"]', '[class*="advertisement"]',  # Sidebars and ads
                '[class*="share"]', '[class*="social"]',  # Social sharing
                '[class*="nav"]', '[class*="menu"]',  # Navigation menus
                '[role="complementary"]'  # Complementary content
            ]
            
            for selector in unwanted_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # Extract main article content
            main_content = None
            content_selectors = [
                'article', '[role="main"]', 
                '[class*="article"]', '[class*="content"]', 
                '[class*="story"]', 'main'
            ]
            
            for selector in content_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup
            
            # Remove script and style elements
            for element in main_content(['script', 'style']):
                element.decompose()
            
            # Get text and clean it
            text = main_content.get_text(separator=' ', strip=True)
            
            # Remove extra whitespace and newlines
            text = re.sub(r'\s+', ' ', text)
            
            # Remove common article suggestion patterns
            text = re.sub(r'Read more:.*?(?=\w)', '', text)
            text = re.sub(r'Related:.*?(?=\w)', '', text)
            text = re.sub(r'You might also like:.*?(?=\w)', '', text)
            text = re.sub(r'More on this story:.*?(?=\w)', '', text)
            text = re.sub(r'More from BBC:.*?(?=\w)', '', text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error cleaning content: {str(e)}")
            return html_content  # Return original content if cleaning fails

    async def summarize(self, url: str) -> Optional[str]:
        """Generate a summary of the webpage content."""
        try:
            # Fetch webpage content
            response = requests.get(url)
            response.raise_for_status()
            
            # Clean the content
            cleaned_content = self._clean_content(response.text)
            logger.info("Successfully cleaned webpage content")
            
            # Prepare the prompt for Claude
            prompt = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens_to_sample": 512,
                "temperature": 0.7,
                "top_p": 0.9,
                "prompt": f"\n\nHuman: Summarize the following text in a clear and concise way, focusing on the main points and key information. Ignore any links to other articles or suggested content:\n\n{cleaned_content}\n\nAssistant: Here's a concise summary of the main points:"
            }
            
            # Call Bedrock with Claude model
            response = self.client.invoke_model(
                modelId="anthropic.claude-v2",
                body=json.dumps(prompt)
            )
            
            # Parse the response
            response_body = json.loads(response.get('body').read())
            summary = response_body.get('completion', '').strip()
            
            logger.info("Successfully generated summary")
            return summary
            
        except requests.RequestException as e:
            logger.error(f"Error fetching URL: {str(e)}")
            return None
        except ClientError as e:
            logger.error(f"Error calling Bedrock: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None
