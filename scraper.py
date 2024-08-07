import os
import json
import re
import requests

from crewai import Agent, Task, Crew, Process #TODO: run with a different venv
from crewai_tools import SerperDevTool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

import uuid

import chromadb
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
from chromadb.utils import embedding_functions

from langchain_openai import ChatOpenAI

'''
Script to scrape data for official campaign data from 2024 election. Use serper dev tool to 
get links for google queries generated by gpt. With the links, use SmartScraperGraph which
uses openai/GEMINI to answer custom queries based on html of links, prompt engineered for best
data quality.
'''

load_dotenv()

# set api keys
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
os.environ['SERPER_API_KEY'] = os.getenv('SERPER_API_KEY')

# Initialize the tool for internet searching capabilities
search_tool = SerperDevTool(api_key=os.getenv('SERPER_API_KEY'))

#querys to scrape from google
queries = [
    "Joe Biden 2024 economic policies",
]

# agent to summarize info from articles parsed online
writer_agent = Agent(
    role='Political newsletter writer',
    goal='deliver unbiased summary of political data',
    backstory="""You are a renowned author in a political newsletter, known for your unbiased papers.
    You clearly answer questions about politics and the 2024 election between Donald Trump and 
    Joe Biden/Kamala Harris.""",
    verbose=True,
    allow_delegation=False,
    llm=ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.3),
    # tools=[search_tool] # uses serper to search internet for answers
)

# get raw api results for online query to google- gets top 10 results 
def get_serper_api_results(prompt):
    url = "https://google.serper.dev/search" #TODO: get title too
    payload = json.dumps({"q": prompt})
    headers = {
        'X-API-KEY': os.getenv('SERPER_API_KEY'),
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        print(f"Response body: {response.text}")
        return None
    
    return response.json()

# metadata to include sources for vector db; generate links to scrape
def get_top_5_links_with_metadata(response_data):
    organic_results = response_data.get('organic', []) # TODO: get title as well
    top_5_links = [result.get('link', '') for result in organic_results[:5]]
    return top_5_links 

# use agent(s) created before. runs faster without delegation agent
def get_summary(query):
    try:
        task = Task(
            description=f"Write in an unbiased and professional manner, focusing on facts. Summarize the following information about '{query}'",
            expected_output="Conduct comprehensive analysis and summarize in a few bullet points",
            agent=writer_agent
        )
        print(f"Created task: {task}")
        result = task.execute_sync()
        print(f"Task result: {result}")
        return result
    except Exception as e:
        print(f"Error executing task for query '{query}': {e}")
        return None

# gets candidate based on prompt
def extract_info_from_query(query):
    candidate = "Kamala Harris" if "Harris" in query else "Donald Trump"
    return candidate  

# create json file for testing- delete in prod
def create_json_file(data):
    with open('political_search_results.json', 'w') as f:
        json.dump(data, f, indent=2)

# initialize embedding model, optimizing for data type
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=os.environ.get('OPENAI_API_KEY'),
                model_name="text-embedding-ada-002"
            )
# get embeddings from an open source module. OctoAI
def get_embedding(text):
    return openai_ef(text)

# execute scraper and store results in vector db, as needed for rag system 
if __name__ == '__main__':
    # create client for db, using duck db for persistent db --> will live after scraper done/process killed
    # client = chromadb.HttpClient(
    #     host=os.getenv('CHROMA_HOST_IP_ADDRESS'),
    #     port=8000,
    #     ssl=False,
    #     headers=None,
    #     settings=Settings(),
    # )
    # print("Status:", client.heartbeat())

    # client = chromadb.PersistentClient(path="rag-meme-db/")
    # client = chromadb.HttpClient(host='localhost', port=8000)

    # 2 collections: red and blue. threads to input into each efficiently?
    # blue_collection = client.create_collection(name="Blue")
    # red_collection = client.create_collection(name="Red")
    
    '''
    process data by reading queries generated by gpt to scrape internet for relevant info. run serper tool to 
    get links and agents to summarize articles, creating entries with question-summary answer pairs and sources 
    for each.
    '''
    red_links = [] 
    blue_links = []
    test = 3
    with open('queries.txt', 'r') as file:
        for line in file:
            if test == 0:
                break
            test -= 1
            query = str(line.strip())
            if query: 
                try:
                    response_data = get_serper_api_results(query)
                    summary = get_summary(query)
                    candidate = extract_info_from_query(query)

                    # document = {
                    #     "query": query,
                    #     "summary": summary,
                    # }
                    top_5_links = get_top_5_links_with_metadata(response_data)
                except Exception as e:
                    print(f"Error during function calls: {e}")

                try:
                    # TODO: Use custom embed class.
                    if candidate == "Donald Trump":
                        # red_collection.upsert(
                        #     documents=[str(document)],
                        #     metadatas={'source': top_5_links[0]},
                        #     ids=[str(uuid.uuid4())]
                        # )
                        red_links.extend(top_5_links)
                        print("Added red doc")
                    else:
                        # blue_collection.upsert(
                        #     documents=[str(document)],
                        #     metadatas={'source': top_5_links[0]},
                        #     ids=[str(uuid.uuid4())]  # must be unique ids
                        # )
                        blue_links.extend(top_5_links)
                        print("Added blue doc")
                except Exception as e:
                    print(f"Error adding document to the database: {e}")

    # Write all the links to a new text file
    with open('blue_links.txt', 'w') as file:
        for link in blue_links:
            file.write(link + '\n')

    with open('red_links.txt', 'w') as file:
        for link in red_links:
            file.write(link + '\n')