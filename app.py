# app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from model import SpamDetector # Assuming SpamDetector is in model.py
import os
import pandas as pd
import tempfile # For handling file uploads securely

app = Flask(__name__)
app.secret_key = os.urandom(24) # Needed for flash messages

detector = SpamDetector()

# Path to pre-trained model and feedback file
MODEL_PATH = "model"
FEEDBACK_FILE = "feedback_data.csv" # For storing user feedback

# Initialize or load model
def initialize_model():
    global detector
    try:
        if os.path.exists(f"{MODEL_PATH}/model.pkl") and os.path.exists(f"{MODEL_PATH}/vectorizer.pkl"):
            detector.load_model(MODEL_PATH)
            print("Pre-trained model loaded successfully.")
        else:
            print("Model files not found. Training a new model...")
            # Create a dummy spam_dataset.csv if it doesn't exist for initial training
            if not os.path.exists("spam_dataset.csv"):
                print("spam_dataset.csv not found. Creating a dummy dataset.")
                dummy_data = {
                    'v1': ['ham', 'spam'] * 50, # Ensure enough samples for stratification
                    'v2': ['This is a ham message.', 'This is a spam message. Click here!'] * 50
                }
                pd.DataFrame(dummy_data).to_csv("spam_dataset.csv", index=False, encoding='utf-8')
                print("Dummy spam_dataset.csv created.")
            
            accuracy, report = detector.train("spam_dataset.csv")
            detector.save_model(MODEL_PATH)
            print(f"New model trained with accuracy: {accuracy}")
            print("Classification Report:\\n", report)
    except Exception as e:
        print(f"Error during model initialization or training: {e}")
        # Fallback: re-initialize detector to prevent app crash if training fails
        detector = SpamDetector() 
        print("Fell back to an untrained SpamDetector instance due to error.")

initialize_model() # Load or train the model when the app starts

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict_message():
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    try:
        result = detector.predict(message) # predict now returns a dict for single message
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/predict_batch', methods=['POST'])
def predict_batch():
    if 'file' not in request.files:
        messages_text = request.form.get('messages_text', '')
        if not messages_text:
            return jsonify({'error': 'No file or text provided for batch prediction'}), 400
        messages = [msg.strip() for msg in messages_text.split('\\n') if msg.strip()]
    else:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file for batch prediction'}), 400
        
        try:
            # Use a temporary file to handle uploads securely
            _, temp_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
            file.save(temp_path)

            if file.filename.endswith('.csv'):
                df = pd.read_csv(temp_path)
                # Assuming the CSV has a column named 'text' or 'message' for messages
                if 'text' in df.columns:
                    messages = df['text'].astype(str).tolist()
                elif 'message' in df.columns:
                    messages = df['message'].astype(str).tolist()
                elif 'v2' in df.columns: # From spam_dataset.csv format
                    messages = df['v2'].astype(str).tolist()
                else:
                    os.remove(temp_path)
                    return jsonify({'error': 'CSV file must contain a "text", "message", or "v2" column'}), 400
            elif file.filename.endswith('.txt'):
                with open(temp_path, 'r', encoding='utf-8') as f:
                    messages = [line.strip() for line in f if line.strip()]
            else:
                os.remove(temp_path)
                return jsonify({'error': 'Unsupported file type. Please upload .csv or .txt'}), 400
            
            os.remove(temp_path) # Clean up temp file

        except Exception as e:
            app.logger.error(f"File processing error: {e}")
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500

    if not messages:
        return jsonify({'error': 'No messages found in the input'}), 400
        
    try:
        results = detector.predict(messages) # predict can handle a list of messages
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Batch prediction error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    data = request.get_json()
    message = data.get('message')
    actual_label = data.get('actual_label') # 'spam' or 'ham'
    predicted_label_str = data.get('predicted_label') # 'Spam' or 'Not Spam'

    if not message or not actual_label or predicted_label_str is None:
        return jsonify({'error': 'Missing data for feedback'}), 400

    # Convert predicted_label_str to 'spam' or 'ham'
    predicted_label = 'spam' if predicted_label_str == 'Spam' else 'ham'

    try:
        feedback_df = pd.DataFrame([[message, predicted_label, actual_label]], columns=['message', 'predicted', 'actual'])
        if os.path.exists(FEEDBACK_FILE):
            feedback_df.to_csv(FEEDBACK_FILE, mode='a', header=False, index=False)
        else:
            feedback_df.to_csv(FEEDBACK_FILE, mode='w', header=True, index=False)
        
        # Optional: Trigger retraining if enough new feedback is collected
        # For now, just acknowledge feedback
        # Consider adding a check here: if len(pd.read_csv(FEEDBACK_FILE)) % N == 0: call retrain_model_with_feedback()

        return jsonify({'status': 'success', 'message': 'Feedback received. Thank you!'})
    except Exception as e:
        app.logger.error(f"Feedback storage error: {e}")
        return jsonify({'error': f'Could not store feedback: {str(e)}'}), 500

# Placeholder for retraining logic using feedback. Could be a separate script or admin endpoint.
# def retrain_model_with_feedback():
#     global detector
#     try:
#         print("Retraining model with feedback data...")
#         # 1. Load original dataset
#         original_df = pd.read_csv("spam_dataset.csv") # Or your primary dataset
#         # 2. Load feedback data
#         feedback_df = pd.read_csv(FEEDBACK_FILE)
#         # 3. Combine: feedback 'message' -> 'v2', 'actual' -> 'v1'
#         feedback_formatted_df = pd.DataFrame({
#             'v1': feedback_df['actual'],
#             'v2': feedback_df['message']
#         })
#         combined_df = pd.concat([original_df, feedback_formatted_df], ignore_index=True)
#         # 4. Save combined data (optional, or use in-memory)
#         combined_df.to_csv("spam_dataset_augmented.csv", index=False)
#         # 5. Retrain
#         detector = SpamDetector() # Re-initialize
#         accuracy, report = detector.train("spam_dataset_augmented.csv")
#         detector.save_model(MODEL_PATH)
#         print(f"Model retrained with feedback. New accuracy: {accuracy}")
#     except Exception as e:
#         print(f"Error during retraining with feedback: {e}")


# API Endpoint for prediction
@app.route('/api/predict', methods=['POST'])
def api_predict():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided in JSON payload'}), 400
    
    message = data['message']
    
    try:
        # detector.predict returns a dict for single message, or list for multiple
        # For API, we expect single message prediction
        if isinstance(message, list): # If user sends a list, predict first or error
            if not message:
                 return jsonify({'error': 'Empty list of messages provided'}), 400
            # result = detector.predict(message) # Or handle as batch if API spec allows
            result = detector.predict(message[0]) # Predict first message if list
            result['note'] = "API processed the first message from the list."
        elif isinstance(message, str):
            result = detector.predict(message)
        else:
            return jsonify({'error': 'Message must be a string or a list of strings.'}), 400
            
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"API Prediction error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Ensure the 'model' directory exists
    os.makedirs(MODEL_PATH, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)