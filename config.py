import os
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

'''
Configuration of all db/clients: Chroma, embedding models, image gen
'''

load_dotenv()

settings = Settings(
    chroma_server_host=os.getenv('CHROMA_HOST_IP_ADDRESS'),
    chroma_server_port=8000,  # if needed
    # Other settings if needed
)

# Initialize ChromaDB client
client = chromadb.HttpClient(
        host=os.getenv('CHROMA_HOST_IP_ADDRESS'),
        port=8000,
        ssl=False,
        headers=None,
        settings=settings,
    )
red_collection = client.get_collection(name="Red")
blue_collection = client.get_collection(name="Blue")
