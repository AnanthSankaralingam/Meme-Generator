# sanity check for chroma db server
import os
from chromadb.config import Settings
import chromadb
import logging
import requests

logging.basicConfig(level=logging.DEBUG)

from dotenv import load_dotenv

load_dotenv()
# need to downgrade chroma so client server same versions

if __name__ == '__main__':
    # need to create client with custom ip to reroute to EC2 instance
    client = chromadb.HttpClient(
        host=os.getenv('CHROMA_HOST_IP_ADDRESS'),
        port=8000,
        ssl=False,
        headers=None,
        settings=Settings(),
    )

    # Verify server connection
    try:
        response = client.heartbeat()
        print("Server heartbeat response:", response)
    except Exception as e:
        logging.exception("Error during heartbeat")
        raise

    # Try to get the collection using the client
    try:
        blue_collection = client.get_or_create_collection(name="Blue")
        red_collection = client.get_or_create_collection(name="Red")

        blue_collection.upsert(
                            documents=["Test"],
                            ids=["1"]  # must be unique ids
                        )
    except Exception as e:
        logging.exception("Error while getting collection")
        raise

    print("Chroma DB client version:", chromadb.__version__)