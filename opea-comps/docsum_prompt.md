# Document Summary

## Overview

Create an application that summarises webpages in Urdu. Given a URL, the application should return a summary of the webpage in Urdu.

Create an audio version of the summary.

## Technical Requirements

- Use Docsum from [https://opea-project.github.io/latest/tutorial/DocSum/DocSum_Guide.html](https://opea-project.github.io/latest/tutorial/DocSum/DocSum_Guide.html)
- Use Intel® Xeon® Scalable processor on AWS
- Look at [https://github.com/opea-project/GenAIExamples/tree/main/DocSum](https://github.com/opea-project/GenAIExamples/tree/main/DocSum) for clarification
- Target system is an AMD Ryzen Processor
- Target system has a NVIDIA GPU
- Create in a folder called `docsum_service`
- Use Vector Store
- Create cache to store summaries
- Use Guardrails
- Use AI Coding Assistant
- Use Frontend eg. Streamlit

## V2

Create new tabs in the UI for the following in the UI:

- Support for freetext
- Support for documents
- Support for OCR/Images
- Support for audio/video
- Support for YouTube videos as these are readily available
- Support for structured datasets

These will then be summarised and the audio version will be generated.

## Python Packages

- boto3
- youtube-transcript-api
- chromadb
- streamlit
- langchain
- faiss-cpu
- bedrock
- moviepy

## Reference Sources

- [https://www.dawn.com/news/1894059/from-darkness-to-light-the-promise-of-decentralised-community-driven-energy-in-northern-pakistan](https://www.dawn.com/news/1894059/from-darkness-to-light-the-promise-of-decentralised-community-driven-energy-in-northern-pakistan)
- [https://www.youtube.com/watch?v=1PvjRIkwIl8&t=2s&ab_channel=YouTubeCreators](https://www.youtube.com/watch?v=1PvjRIkwIl8&t=2s&ab_channel=YouTubeCreators)
- [https://www.youtube.com/watch?v=xd4ygI0GHV8&ab_channel=GuzKhanOfficial](https://www.youtube.com/watch?v=xd4ygI0GHV8&ab_channel=GuzKhanOfficial)