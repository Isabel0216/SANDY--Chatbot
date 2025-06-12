from flask import Flask, request, jsonify, send_file, send_from_directory
from main import chat_with_bot, speak
from flask_cors import CORS
from dotenv import load_dotenv
import io
import os
import sys
import traceback

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)

@app.route('/chat_with_bot', methods=['POST'])
def handle_chat():
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        response = chat_with_bot(data['message'])
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/speak', methods=['POST'])
def handle_speak():
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        audio_bytes = speak(data['text'], return_bytes=True)
        if audio_bytes:
            return send_file(
                io.BytesIO(audio_bytes),
                mimetype='audio/wav'
            )
        return jsonify({'error': 'Could not generate speech'}), 500
    except Exception as e:
        print(f"Error in speak endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/')
def serve_frontend():
    try:
        return send_from_directory('static', 'index.html')
    except Exception as e:
        print(f"Error serving frontend: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Add health check endpoint for Vercel
@app.route('/health')
def health_check():
    try:
        # Check if static directory exists
        if not os.path.exists('static'):
            return jsonify({'error': 'Static directory not found'}), 500
        
        # Check if letters directory exists
        if not os.path.exists('letters'):
            return jsonify({'error': 'Letters directory not found'}), 500
            
        # Check if key files exist
        required_files = [
            'static/index.html',
            'static/TALKING_SANDY.gif',
            'static/WAITING_SANDY.gif',
            'static/Question_SANDY.gif'
        ]
        
        missing_files = [f for f in required_files if not os.path.exists(f)]
        if missing_files:
            return jsonify({'error': f'Missing files: {missing_files}'}), 500

        # Check OpenAI API key
        if not os.getenv('OPENAI_API_KEY'):
            return jsonify({'error': 'OpenAI API key not found'}), 500

        return jsonify({
            'status': 'healthy',
            'static_dir': os.listdir('static'),
            'letters_dir': os.listdir('letters')
        }), 200
    except Exception as e:
        print(f"Error in health check: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 