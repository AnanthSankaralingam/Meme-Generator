import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings

'''
Configuration of all db/clients: Chroma, embedding models, image gen
'''

load_dotenv()

# Initialize ChromaDB client
client = chromadb.HttpClient(
        host=os.getenv('CHROMA_HOST_IP_ADDRESS'),
        port=8000,
        ssl=False,
        headers=None,
        settings=Settings(),
    )
red_collection = client.get_or_create_collection(name="Red")
blue_collection = client.get_or_create_collection(name="Blue")
