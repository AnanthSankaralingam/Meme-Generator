from flask import Flask
from flask_cors import CORS
from router import setup_routes

'''
Create and run server on AWS Lambda, since we don't expect much traffic.
logging flask_cors octoai
chromadb==0.4.14 asyncio dotenv
'''

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    setup_routes(app)
    
    return app

app = create_app()

# Uncomment the following if you decide to deploy on AWS Lambda
# def lambda_handler(event, context):
#     return awsgi.response(app, event, context, base64_content_types={"image/png"})

if __name__ == '__main__':
    # Ensure the app listens on all interfaces and port 8080, as required by AWS App Runner
    app.run(host='0.0.0.0', port=8080, debug=True)
