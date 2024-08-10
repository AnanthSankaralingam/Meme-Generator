from flask import Flask
from flask_cors import CORS
from router import setup_routes
import awsgi

'''
Create and run server on aws lambda, since we dont expect much traffic.
logging flask_cors octoai
chromadb==0.4.14  asyncio dotenv
'''

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    setup_routes(app)
    
    return app

app = create_app()

def lambda_handler(event, context):
    return awsgi.response(app, event, context, base64_content_types={"image/png"})

if __name__ == '__main__':
    app.run(debug=True)