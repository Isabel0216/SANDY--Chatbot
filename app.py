from flask import Flask, request, jsonify, send_file, send_from_directory
from main import chat_with_bot, speak
from flask_cors import CORS
import io

import os
print("FFmpeg system call:", os.system("ffmpeg -version"))
from pydub.utils import which
print("FFmpeg path (pydub):", which("ffmpeg"))

app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)

@app.route('/chat_with_bot', methods=['POST'])
def handle_chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    response = chat_with_bot(data['message'])
    return jsonify({'response': response})

@app.route('/speak', methods=['POST'])
def handle_speak():
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

@app.route('/')
def serve_frontend():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    app.run(port=5000) 
