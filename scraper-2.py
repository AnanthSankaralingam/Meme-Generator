import requests
from bs4 import BeautifulSoup
import openai
import os
import json
import time
from dotenv import load_dotenv
import uuid
import chromadb
from chromadb.config import Settings
from octoai.text_gen import ChatMessage
from octoai.client import OctoAI

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
client_octo = OctoAI(api_key=os.environ['OCTO_API'])

# use beautiful soup to get all p tags and extract as raw text
def scrape_article(url):
    response = requests.get(url, timeout=15)  # Set timeout to 15 seconds
    response.raise_for_status()  # Raise an exception for HTTP errors
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract the main content of the article
    article_text = ' '.join([p.text for p in soup.find_all('p')])
    
    return article_text

def llm_call(system_message='If there is no context, respond with N/A', user_message='Respond with N/A'):
    time.sleep(4)
    completion = client_octo.text_gen.create_chat_completion(
        max_tokens=128,
        messages=[
            ChatMessage(content=system_message, role="system"),
            ChatMessage(content=user_message, role="user")
        ],
        model="meta-llama-3.1-8b-instruct",
        presence_penalty=0,
        temperature=0.3, # low to be factual
        top_p=1
    )
    return completion.choices[0].message.content

def run_scraper(url, prompt):
    article_text = scrape_article(url)
    summary = llm_call(system_message=prompt, user_message=article_text)
    return json.dumps({"summary": summary}, indent=2)

if __name__ == '__main__':
    client = chromadb.HttpClient(
        host=os.getenv('CHROMA_HOST_IP_ADDRESS'),
        port=8000,
        ssl=False,
        headers=None,
        settings=Settings(),
    )
    red_collection = client.get_or_create_collection(name="Red")
    blue_collection = client.get_or_create_collection(name="Blue")

    red_prompt ="""You are a political reporter, skilled in answering questions based on the context of campaign
                    policies. Clearly describe Donald Trump's political stances on topics covered in this article
                    in a few brief bullet points. Do not say anything based on general knowledge. If there is no relevant information in the context, respond with N/A:
                """
    blue_prompt = """You are a political reporter, skilled in answering questions based on the context of campaign
                    policies. Clearly describe Kamala Harris's political stances on topics covered in this article
                    in a few briefbullet points. Do not say anything based on general knowledge. If there is no relevant information or link in the context, respond with N/A:
      """

    def process_links(file_path, collection, prompt):
        with open(file_path, 'r') as f:
            links = f.readlines()
            for link in links:
                link = link.strip()
                if link:
                    try:
                        summary = run_scraper(url=link, prompt=prompt)
                        if summary:
                            collection.add(
                                documents=[summary],
                                metadatas={'source': link},
                                ids=[str(uuid.uuid4())]
                            )
                            print(f"Added doc: {link}")
                        else:
                            print(f"Couldn't summarize {link}")
                            time.sleep(10)
                    except Exception as e:
                        print(f"Error processing: {link}")
                        print(f"Error: {str(e)}")
                        print("Waiting 10s to restart")
                        time.sleep(3) # wait a minute to restart scraping in case of API limits

    print("Starting RED links")
    # process_links('red_links.txt', red_collection, red_prompt)
    process_links('red_links-v1.txt', red_collection, red_prompt)
    process_links('red_links-v2.txt', red_collection, red_prompt)
    print("FINISHED RED LINKS")

    print("Starting BLUE links")
    # process_links('blue_links.txt', blue_collection, blue_prompt)
    process_links('blue_links-v1.txt', blue_collection, blue_prompt)
    process_links('blue_links-v2.txt', blue_collection, blue_prompt)
    print("FINISHED BLUE LINKS")