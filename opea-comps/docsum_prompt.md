# Document Summary

## Overview

Create an application that summarises webpages in Urdu. Given a URL, the application should return a summary of the webpage in Urdu.

Create an audio version of the summary.

## Technical Requirements

- Use Docsum from [https://opea-project.github.io/latest/tutorial/DocSum/DocSum_Guide.html](https://opea-project.github.io/latest/tutorial/DocSum/DocSum_Guide.html)
- Use Intel® Xeon® Scalable processor on AWS
- Look at [https://github.com/opea-project/GenAIExamples/tree/main/DocSum](https://github.com/opea-project/GenAIExamples/tree/main/DocSum) for clarification
- Run on port 8002
- Use Amazon Polly for Text-to-Speech Generation
- Use Amazon Transcribe for Audio/Video Transcription
- Use Amazon Translate for Translation
- Target system is an AMD Ryzen Processor
- Target system has a NVIDIA GPU
- Create in a folder called `docsum_service`
- Use Vector Store
- Create cache to store summaries
- Use Guardrails
- Use AI Coding Assistant
- Use Frontend eg. Streamlit

## V2

### Requirements

- Generate a summary in English and Urdu
- Generate an audio version of the summary
- Support for freetext
- Support for documents
- Support for OCR/Images
- Support for audio
- Support for video
- Support for YouTube videos as these are readily available
- Support for structured datasets

These will then be summarised and the audio version will be generated.

### Interface

Create new tabs in the UI for the following in the UI:

- Support for freetext
- Support for documents
- Support for OCR/Images
- Support for audio
- Support for video
- Support for YouTube videos as these are readily available
- Support for structured datasets

## Python Packages

- fastapi - Web framework
- uvicorn - ASGI server
- streamlit - Frontend UI
- chromadb - Vector store
- boto3 - AWS SDK
- youtube-transcript-api - YouTube transcripts
- moviepy - Video processing
- pytesseract - OCR processing
- Pillow - Image processing
- pandas - Data manipulation
- PyPDF2 - PDF processing
- python-multipart - File uploads
- python-dotenv - Environment variables
- beautifulsoup4 - Web scraping
- requests - HTTP client
- pydantic - Data validation
- numpy - Numerical computing
- torch - Deep learning
- transformers - Text processing

## Reference Sources

These are used to test the application.

### Articles

- [From darkness to light: The promise of decentralised community-driven energy in northern Pakistan](https://www.dawn.com/news/1894059/from-darkness-to-light-the-promise-of-decentralised-community-driven-energy-in-northern-pakistan)
- [Running on empty](https://www.dawn.com/news/1899558/running-on-empty)
- [FIFA report finds wide discrepancy in women’s pay, contracts, attendance](https://images.dawn.com/news/1193388/fifa-report-finds-wide-discrepancy-in-womens-pay-contracts-attendance)

### Documents

- [A railway fit for Britain's future](https://assets.publishing.service.gov.uk/media/67b30e36b56d8b0856c2fd49/a-railway-fit-for-britains-future.pdf)
- [RFC 1035 - Domain names - implementation and experience](https://www.ietf.org/rfc/rfc1035.txt)

### Audio/Video

- [Dawn - Darkness To Light](../sample_data/dawn_darkness_to_light.mp3)
- [Fair Use - Copyright on YouTube](../sample_data/fair_use.mp4)

### YouTube Videos

- [Fair Use - Copyright on YouTube](https://www.youtube.com/watch?v=1PvjRIkwIl8&t=2s&ab_channel=YouTubeCreators)
- [Guz Khan - Pakisaurus](https://www.youtube.com/watch?v=xd4ygI0GHV8&ab_channel=GuzKhanOfficial)

### Structured Datasets

- [News Articles JSON](../sample_data/news_articles.csv)
- [News Articles CSV](../sample_data/news_articles.csv)

## References

- [Docsum](https://opea-project.github.io/latest/tutorial/DocSum/DocSum_Guide.html)
- [Docsum GitHub](https://github.com/opea-project/GenAIExamples/tree/main/DocSum)
- [Docsum - Single node on-prem deployment with TGI on Intel® Xeon® Scalable processor¶](https://opea-project.github.io/latest/tutorial/DocSum/deploy/xeon.html)
