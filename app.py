# app.py
from flask import Flask, request, jsonify, render_template
from model import SpamDetector
import os

app = Flask(__name__)
detector = SpamDetector()

# Path to pre-trained model
MODEL_PATH = "model"

# Check if model exists, otherwise we'll need to train it
if os.path.exists(f"{MODEL_PATH}/model.pkl"):
    detector.load_model(MODEL_PATH)
else:
    # You'll need to provide a dataset and train the model
    # This is just a placeholder - you'll need to implement this
    print("Model not found. You need to train the model first.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    # Get the message from the request
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        # Make prediction
        result = detector.predict(message)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_and_train():
    # This endpoint would handle training with a new dataset
    # This is a placeholder - you'll need to implement file upload
    # and training logic
    return jsonify({'message': 'Training endpoint. Not implemented yet.'})

if __name__ == '__main__':
    app.run(debug=True)