from flask import Flask
from flask_cors import CORS
from router import setup_routes

'''
Create and run server
'''

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    setup_routes(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)