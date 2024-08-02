import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

'''
Configuration of all db/clients: Chroma, embedding models, image gen
'''

load_dotenv()

# Initialize ChromaDB client
client = chromadb.PersistentClient(path="rag-meme-db")
red_collection = client.get_or_create_collection(name="Red")
blue_collection = client.get_or_create_collection(name="Blue")
