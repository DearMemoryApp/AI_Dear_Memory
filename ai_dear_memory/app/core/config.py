import google.generativeai as genai
from pydantic_settings import BaseSettings
from pinecone import Pinecone, ServerlessSpec


class Settings(BaseSettings):
    # MySQL Database Config
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    # Pinecone Config
    PINECONE_API_KEY: str
    INDEX_NAME: str = "dear-memory-project-index"
    INDEX_DIMENSION: int = 3072
    PINECONE_CLOUD: str = "aws"
    PINECONE_REGION: str = "us-east1"

    # Gemini AI Config
    GEMINI_API_KEY: str

    @property
    def mysql_uri(self) -> str:
        """Construct MySQL URI dynamically."""
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"


# Load settings
settings = Settings()

genai.configure(api_key=settings.GEMINI_API_KEY)

# Initialize Pinecone
pinecone_client = Pinecone(api_key=settings.PINECONE_API_KEY)

existing_indexes = [index["name"] for index in pinecone_client.list_indexes()]

# Check and create index only if needed
if settings.INDEX_NAME not in existing_indexes:
    pinecone_client.create_index(
        name=settings.INDEX_NAME,
        dimension=settings.INDEX_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(
            cloud=settings.PINECONE_CLOUD, region=settings.PINECONE_REGION
        ),
    )

# Connect to Pinecone index
index = pinecone_client.Index(settings.INDEX_NAME)
