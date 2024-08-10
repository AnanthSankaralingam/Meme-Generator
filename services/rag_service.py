# process all text and image generation, and vector db queries
from config import red_collection, blue_collection
import openai
import os
import json
import requests
from octoai.text_gen import ChatMessage
from octoai.client import OctoAI

import asyncio
from functools import lru_cache
import logging


client_openai = openai.Client(api_key=os.getenv('OPENAI_API_KEY'))
client_octo = OctoAI(api_key=os.environ['OCTO_API'])

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Implement caching for LLM calls - optimize for same inputs
@lru_cache(maxsize=50)
def cached_llm_call(system_message, user_message):
    return llm_call(system_message, user_message)

# system prompts 
system_prompt = f"""
You are a political reporter, skilled in answering questions based on the context of campaign policies. 
Given the context from Kamala Harris's or Donald Trump's campaign, provide a clear and factual answer to the question posed.
If the context is not relevant, do not use it. Here is an example:

Question: What will gas prices be like?

Kamala Harris:
- focusing on climate change

Donald Trump:
- focusing on the economy

Briefly state the key points of the policies in a few bullet points without using second-person perspective. Return 3 bullet points (using •), don't preface the answer.
"""

# depracated, adjusted glif to use one context input
system_prompt_image_trump = f"""
Generate an image idea that includes Donald Trump's campaign policy and something specific about the 
concept/profession/question in relation to his policies. If Donald Trump wins the election, the image should make a joke 
about his policies in relation to the concept/profession/question. Ensure that Donald Trump is included in the image.
"""
system_prompt_image_harris = f"""
Generate an image idea that includes Kamala Harris's campaign policy and something specific about the
concept/profession/question in relation to her policies. If Kamala Harris wins the election, the image should make a joke
about her policies in relation to the concept/profession/question. Ensure that Kamala Harris is included in the image.
"""

'''
All processing: query collections and generate outputs for server.py to use. Use
to generate responses with GPT and image gen.
'''

# call octo's llama 3.1 with context
def llm_call(system_message=system_prompt, user_message=''):
    completion = client_octo.text_gen.create_chat_completion(
        max_tokens=128,
        messages=[
            ChatMessage(content=system_message, role="system"),
            ChatMessage(content=user_message, role="user")
        ],
        model="meta-llama-3.1-8b-instruct",
        presence_penalty=0,
        temperature=0.8, # adjust based on humor
        top_p=1
    )
    return completion.choices[0].message.content

# Asynchronous processing for Chroma queries and LLM calls
async def async_query_collection(collection, query_text):
    return collection.query(query_texts=[query_text], n_results=1)

async def async_llm_call(system_message, user_message):
    return cached_llm_call(system_message, user_message)

# query rag db for context, then generate text content with it
async def process_rag_query_text_async(query):
    try:
        red_results_raw, blue_results_raw = await asyncio.gather(
            async_query_collection(red_collection, query),
            async_query_collection(blue_collection, query)
        )

        # extract chroma results for context
        red_str = red_results_raw['documents'][0][0]
        blue_str = blue_results_raw['documents'][0][0]
        red_link = red_results_raw['metadatas'][0][0]['source']
        blue_link = blue_results_raw['metadatas'][0][0]['source']

        red_response, blue_response = await asyncio.gather(
            async_llm_call(system_prompt, f"Context: {red_str}\n\nQuery: {query}\n\nResponse:"),
            async_llm_call(system_prompt, f"Context: {blue_str}\n\nQuery: {query}\n\nResponse:")
        )

        # return text with sources
        return {
            "blue_response": blue_response,
            "red_response": red_response,
            "blue_link": blue_link,
            "red_link": red_link
        }
    except Exception as e:
        logger.error(f"Error in process_rag_query_text_async: {str(e)}")
        raise
    
# call wojak glif. if api key runs out, fall back to another one
def glif_call(context, query):
    api_keys = [
        os.getenv('GLIF_API_KEY_1'),
        os.getenv('GLIF_API_KEY_2'),
        os.getenv('GLIF_API_KEY_3')
    ]
    
    payload = {
        "id": "clz4xb23q00071120ixtlgzr9", # custom glif
        "inputs": {
            "context": context,
            "query": query
        }
    }
    # in case on api key fails, roll back on others
    for api_key in api_keys:
        try:
            response = requests.post(
                "https://simple-api.glif.app",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"}, # paste key if error
            )
            
            response.raise_for_status()
            
            response_json = response.json()
            
            if 'error' in response_json:
                print(f"API Error with key: {response_json['error']}")
                continue
            
            output_url = response_json.get('output') # extract the image url
            return output_url
        
        except requests.exceptions.RequestException as e:
            print(f"HTTP Request failed with key: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON Decoding Error with key: {e}")
        except Exception as e:
            print(f"Unexpected Error with key: {e}")
    
    return None
    # response = client_octo.image_gen.generate_sdxl(

# get context from chroma, query Llama with document context, generate output with source
def process_rag_query_text(query):
    return asyncio.run(process_rag_query_text_async(query))

# generate image based on text displayed
async def process_rag_query_image_async(query, red_response, blue_response):
    # combine contexts from rag db and send as joint component to glif, along with query
    try:
        context = f"Trump: {red_response}\nHarris: {blue_response}"
        meme = await asyncio.to_thread(glif_call, context=context, query=query)
        if meme is None:
            logger.warning("Failed to generate meme")
        return {"meme": meme}
    except Exception as e:
        logger.error(f"Error in process_rag_query_image_async: {str(e)}")
        return f"Error in process_rag_query_image_async: {str(e)}"

# generate image async
def process_rag_query_image(query, red_response, blue_response):
    return asyncio.run(process_rag_query_image_async(query, red_response, blue_response))
