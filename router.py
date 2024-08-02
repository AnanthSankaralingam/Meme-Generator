from flask import request, jsonify
from services.rag_service import process_rag_query_text, process_rag_query_image
import logging

logger = logging.getLogger(__name__) #instead of printing errors

'''
Define all API calls- runs/set up when server created. Routes defined for:
    - query (post): get user input and respond with RAG enhanced GPT. 
    - genImage (post): create memes based on prompt and return
'''

def setup_routes(app):
    @app.route('/query/text', methods=['POST'])
    def process_query_text():
        data = request.json
        query = data.get('query')

        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        try:
            response = process_rag_query_text(query)
            return jsonify(response), 200
        except Exception as e:
            logger.error(f"Error processing text query: {str(e)}")
            return jsonify("Couldn't process query!"), 401
        
    @app.route('/query/image', methods=['POST'])
    def process_query_image():
        data = request.json
        query = data.get('query')
        red_context = data.get('red_context')
        blue_context = data.get('blue_context')

        if not red_context or not blue_context:
            return jsonify({"error": "No query provided"}), 400
        
        try:
            response = process_rag_query_image(query, red_context, blue_context)
            return jsonify(response), 200
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return jsonify("Couldn't generate meme:("), 401