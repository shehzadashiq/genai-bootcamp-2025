# genai-bootcamp-2025

- Cohort: 2025

GenAI Bootcamp 2025 is 6 Weeks Of Free Online GenAI Training And Hands-on Programming by Andrew Brown and various instructors

[Free GenAI Bootcamp](https://genai.cloudprojectbootcamp.com/)

- [genai-bootcamp-2025](#genai-bootcamp-2025)
  - [Journal](#journal)
  - [Overview](#overview)
  - [Components](#components)
  - [Running the Application](#running-the-application)
    - [Development](#development)
      - [Configure Environment Variables](#configure-environment-variables)
      - [Non Docker](#non-docker)
        - [Backend](#backend)
        - [Frontend](#frontend)
        - [Document Summary](#document-summary)
      - [Docker](#docker)
    - [Production](#production)
      - [Document Summary Service](#document-summary-service)
        - [Prerequisites](#prerequisites)
        - [Configuration](#configuration)
        - [Running Locally](#running-locally)
      - [Running with Docker](#running-with-docker)
      - [Usage](#usage)

## Journal

The `/journal` directory contains

- [Week 0](journal/week0.md)
- [Week 1](journal/week1.md)
- [Week 2](journal/week2.md)
- [Week 3](journal/week3.md)
- [Week 4](journal/week4.md)
- [Week 5](journal/week5.md)

## Overview

This project creates an application to aid Urdu learners by using different activities.

## Components

| Activity       |  Purpose                         |
|----------------|----------------------------------|
| Document Summary | Summarises a variety of media into Urdu, generating both Urdu/English text and Audio |
| Vocabulary Quiz | Test your vocabulary knowledge with interactive flashcards and quizzes. |
| Word Matching | Match Urdu words with their English translations in this fun memory game |
| Sentence Builder | Practice building sentences using the words you've learned |
| Flashcards | Learn and review vocabulary with interactive flashcards |
| Listening Practice | Improve your listening comprehension with real-world Urdu audio content |
| Urdu Conversations | Practice your Urdu conversation skills with an adaptive AI tutor that responds to your level |

### Document Summary

![image](https://github.com/user-attachments/assets/99d51d0e-aa3c-4d75-a566-260b2dff0778)

Sample Data is available in [Sample Data](./opea-comps/docsum_service/sample_data/)

#### URL

#### Text

![image](https://github.com/user-attachments/assets/b2cfd372-4939-4492-86b9-22c044eba5ef)

#### Document

![image](https://github.com/user-attachments/assets/7b3a7c16-c8d0-4d1c-b305-9ce85ee4ae1b)

#### Image

![image](https://github.com/user-attachments/assets/67f926b2-ec2c-48b7-91c5-ca2ba7b7ddb4)

#### Video

![image](https://github.com/user-attachments/assets/fdb8674c-9b05-48ef-9fcd-846a5707c533)

#### YouTube

##### V1

![image](https://github.com/user-attachments/assets/5acdf13b-05e3-4f4c-ae77-a84f7dba5281)

##### V2

![image](https://github.com/user-attachments/assets/824e16dc-e52c-473e-a07f-1aeaf5afeff6)

#### Dataset

![image](https://github.com/user-attachments/assets/4ba724a7-4f4a-4743-b8f8-5f4d612f0260)

### Study Activities

![image](https://github.com/user-attachments/assets/4a526bcd-861c-4feb-88eb-a241d53e9a62)

#### Vocabulary Quiz

![image](https://github.com/user-attachments/assets/a7af0152-1251-4ea9-8b52-e7ccf78960f8)

##### Quiz Question

![image](https://github.com/user-attachments/assets/124ddbe0-8dd1-4659-832d-a6cc097ab547)

##### Quiz Summary

![image](https://github.com/user-attachments/assets/97983508-10d5-4618-98a7-b7a428af4607)

#### Word Matching

#### Sentence Builder

![image](https://github.com/user-attachments/assets/c8f8b691-0c7d-4ecd-9631-24dfb6e6a919)

##### Incorrect Sentence

![image](https://github.com/user-attachments/assets/3cf87e74-239f-4a18-a203-80bfe4110376)

##### Correct Sentence

![image](https://github.com/user-attachments/assets/493ae327-dfbb-4c34-8aad-c9be5e8d9f48)

#### Flashcards

Front of flashcard with Urdu Word

![image](https://github.com/user-attachments/assets/a824bc03-09e6-46d3-b3ea-2a407d8898e9)

Reverse of flashcard with English Word and explanation

![image](https://github.com/user-attachments/assets/9bab8355-feb6-431b-92d0-56866bdece20)

#### Listening Practice

##### V1

![image](https://github.com/user-attachments/assets/2ac90ed2-5d30-477c-a8ce-629cd29865bf)

##### V2

This version displays the YouTube Video so it can be reviewed

![image](https://github.com/user-attachments/assets/b7b83935-ca57-4177-b3fa-3ffc705381cb)

######  Statistics

![image](https://github.com/user-attachments/assets/68799597-e5b5-4779-808e-359bda9b48ef)

##### Quiz Scored

![image](https://github.com/user-attachments/assets/1e45896c-2fa5-4a8a-bfff-282540282d9a)

#### Urdu Conversations

![image](https://github.com/user-attachments/assets/8acc5c59-e0f1-43aa-a07a-7d0e1a35aaf8)

## Running the Application

### Development

Clone the repository locally and navigate to the root directory.

#### Configure Environment Variables

Configure the environment variables by copying the example files:

```bash
cp .env.example .env
```

Update the environment variables in the `.env` file. Specifically:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION`
- `DJANGO_SECRET_KEY`

To configure `DJANGO_SECRET_KEY`, run:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

The other values can be left as is.

#### Non Docker

##### Backend

```bash
cd lang_portal_backend
source .venv/bin/activate
pip install -r requirements.txt
python manage.py runserver 8080
```

##### Frontend

```bash
cd lang_portal_frontend
npm install
npm run dev
```

##### Document Summary

```bash
cd opea-comps/docsum_service
python3 -m docsum_service
```

#### Docker

```bash
docker compose -f docker-compose.dev.yml up --build
```

### Production

```bash
docker compose -f docker-compose.yml up --build
```

#### Document Summary Service

The Document Summary Service is a component that summarizes various types of content (URLs, text, documents, images, YouTube videos) into Urdu, generating both text and audio.

##### Prerequisites

- AWS account with access to Bedrock and S3
- Google Cloud account (for text-to-speech capabilities)

##### Configuration

1. Navigate to the document summary service directory:

   ```bash
   cd opea-comps/docsum_service
   ```

2. Create an environment file by copying the example:

   ```bash
   cp .env_example .env
   ```

3. Update the following required variables in the `.env` file:

   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
   - `AWS_BUCKET_NAME`: Create an S3 bucket in your AWS account and enter its name here
   - `GOOGLE_APPLICATION_CREDENTIALS`: Path to your Google Cloud credentials JSON file

4. Create a credentials directory and add your Google Cloud credentials using the following instructions [Create access credentials](./journal/week5.md#create-a-service-account-key-json-file)

   ```bash
   mkdir -p credentials
   # Copy your Google Cloud credentials JSON file to the credentials directory
   ```

##### Running Locally

You can run the document summary service locally using Python:

```bash
cd opea-comps/docsum_service
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

In a separate terminal, run the Streamlit frontend:

```bash
cd opea-comps/docsum_service
streamlit run frontend/streamlit_app.py
```

#### Running with Docker

You can also run the document summary service using Docker Compose:

```bash
cd opea-comps/docsum_service
docker-compose up --build
```

This will start both the API service (on port 8002) and the Streamlit frontend (on port 8501).

#### Usage

Once running, you can access the document summary interface at:

- [http://localhost:8501](http://localhost:8501)

The service supports:

- URL summarization
- Text summarization
- Document processing (PDF, DOCX, TXT)
- Image OCR and summarization
- YouTube transcript extraction and summarization
