from setuptools import setup, find_packages

setup(
    name="comps",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-multipart",
        "aiohttp",
        "python-dotenv",
        "huggingface-hub<=0.24.0",
        "langchain-community",
        "langchain-huggingface",
        "opentelemetry-api",
        "opentelemetry-exporter-otlp",
        "opentelemetry-sdk",
        "prometheus-fastapi-instrumentator",
        "sentencepiece",
        "shortuuid",
    ],
)
