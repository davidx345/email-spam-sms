# app.py
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from model import SpamDetector # Assuming SpamDetector is in model.py
import os
import pandas as pd
import tempfile # For handling file uploads securely
import logging

import logging
import time
from datetime import datetime
from functools import wraps
import redis
from prometheus_flask_exporter import PrometheusMetrics
import psutil
from werkzeug.middleware.proxy_fix import ProxyFix

# Ensure logs directory exists before setting up logging
LOG_DIR = 'logs'
LOG_FILE = 'logs/app.log'
try:
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
except Exception as e:
    print(f"Warning: Could not create logs directory: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Handle proxy headers for proper IP detection
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Initialize Prometheus metrics
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

# Redis connection for caching
try:
    redis_client = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    redis_client.ping()
    logger.info("Redis connection established")
except:
    redis_client = None
    logger.warning("Redis not available, caching disabled")

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

# Rate limiting decorator
def rate_limit(max_requests=100, window=60):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if redis_client:
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                key = f"rate_limit:{client_ip}:{f.__name__}"
                
                current = redis_client.get(key)
                if current is None:
                    redis_client.setex(key, window, 1)
                else:
                    if int(current) >= max_requests:
                        return jsonify({'error': 'Rate limit exceeded'}), 429
                    redis_client.incr(key)
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/health')
def health_check():
    """Health check endpoint for load balancers."""
    try:
        # Check model status
        model_status = "healthy" if detector.is_trained else "training_required"
        
        # Check Redis connection
        redis_status = "healthy"
        if redis_client:
            try:
                redis_client.ping()
            except:
                redis_status = "unhealthy"
        else:
            redis_status = "disabled"
        
        # Check system resources
        memory_usage = psutil.virtual_memory().percent
        cpu_usage = psutil.cpu_percent()
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'model_status': model_status,
            'redis_status': redis_status,
            'system': {
                'memory_usage_percent': memory_usage,
                'cpu_usage_percent': cpu_usage
            }
        }
        
        # Return unhealthy status if critical issues
        if memory_usage > 90 or cpu_usage > 90 or model_status != "healthy":
            health_data['status'] = 'unhealthy'
            return jsonify(health_data), 503
            
        return jsonify(health_data), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@app.route('/ready')
def readiness_check():
    """Readiness check for Kubernetes."""
    if detector.is_trained:
        return jsonify({'status': 'ready'}), 200
    else:
        return jsonify({'status': 'not_ready', 'reason': 'model_not_trained'}), 503

@app.route('/predict', methods=['POST'])
@rate_limit(max_requests=50, window=60)
def predict_message():
    start_time = time.time()
    
    try:
        # Validate content type
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
            
        if len(message) > 1000:  # Limit message length
            return jsonify({'error': 'Message too long (max 1000 characters)'}), 400
        
        # Check cache first
        cache_key = f"prediction:{hash(message)}"
        if redis_client:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for message hash: {hash(message)}")
                metrics.counter('cache_hits_total').inc()
                return jsonify(eval(cached_result))
        
        # Make prediction
        result = detector.predict(message)
        
        # Cache result
        if redis_client and result:
            redis_client.setex(cache_key, 300, str(result[0]))  # Cache for 5 minutes
            metrics.counter('cache_misses_total').inc()
        
        # Log prediction
        processing_time = time.time() - start_time
        logger.info(f"Prediction made: {result[0]['prediction']} (confidence: {result[0]['probability']:.2f}) in {processing_time:.3f}s")
        
        # Record metrics
        metrics.histogram('prediction_duration_seconds').observe(processing_time)
        metrics.counter('predictions_total', labels={'prediction': result[0]['prediction']}).inc()
        
        return jsonify({
            'text': message,
            'prediction': result[0]['prediction'],
            'is_spam': result[0]['is_spam'],
            'spam_probability': result[0]['probability'],
            'processing_time': processing_time
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        metrics.counter('prediction_errors_total').inc()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/predict_batch', methods=['POST'])
def predict_batch():
    messages = []  # Initialize messages
    temp_path = None # Initialize temp_path for cleanup
    file_uploaded = False

    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        file_uploaded = True
        app.logger.info(f"File upload attempt: {file.filename}")
        
        try:
            # Use a temporary file to handle uploads securely
            fd, temp_path = tempfile.mkstemp(suffix=os.path.splitext(file.filename)[1])
            os.close(fd)  # Close the raw file descriptor, as save() will reopen
            file.save(temp_path)
            app.logger.info(f"Uploaded file '{file.filename}' saved temporarily to: {temp_path}")

            common_encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']

            if file.filename.endswith('.csv'):
                df = None
                for encoding in common_encodings:
                    try:
                        df = pd.read_csv(temp_path, encoding=encoding)
                        app.logger.info(f"Successfully read CSV '{file.filename}' with encoding: {encoding}")
                        break
                    except UnicodeDecodeError:
                        app.logger.warning(f"Failed to decode CSV '{file.filename}' with {encoding}, trying next.")
                        continue
                    except pd.errors.EmptyDataError:
                        app.logger.warning(f"CSV file '{file.filename}' is empty.")
                        df = pd.DataFrame() # Create empty DataFrame to avoid None error later
                        break # Successfully processed an empty file
                    except Exception as e_read:
                        app.logger.warning(f"Pandas read_csv error for '{file.filename}' with encoding {encoding}: {e_read}")
                        # Don't break here, try other encodings
                
                if df is None: # If all encodings failed for a non-empty file
                    app.logger.error(f"Could not read CSV file '{file.filename}' with any attempted encodings or it's malformed.")
                    return jsonify({'error': f"Could not read CSV file '{file.filename}'. It might be malformed or use an unsupported encoding."}), 500

                if not df.empty:
                    if 'text' in df.columns:
                        messages = df['text'].astype(str).tolist()
                    elif 'message' in df.columns:
                        messages = df['message'].astype(str).tolist()
                    elif 'v2' in df.columns:  # From spam_dataset.csv format
                        messages = df['v2'].astype(str).tolist()
                    else:
                        app.logger.error(f"CSV file '{file.filename}' missing required column.")
                        return jsonify({'error': 'CSV file must contain a "text", "message", or "v2" column'}), 400
                # If df is empty, messages remains [], which is handled later

            elif file.filename.endswith('.txt'):
                read_success = False
                for encoding in common_encodings:
                    try:
                        with open(temp_path, 'r', encoding=encoding) as f_txt:
                            messages = [line.strip() for line in f_txt if line.strip()]
                        app.logger.info(f"Successfully read TXT file '{file.filename}' with encoding: {encoding}")
                        read_success = True
                        break
                    except UnicodeDecodeError:
                        app.logger.warning(f"Failed to decode TXT file '{file.filename}' with {encoding}, trying next.")
                        continue
                if not read_success and not messages: # If all encodings failed and messages is still empty
                    app.logger.error(f"Could not read TXT file '{file.filename}' or it is empty.")
                    return jsonify({'error': f"Could not read TXT file '{file.filename}'. It might be empty or use an unsupported encoding."}), 500
            else:
                app.logger.warning(f"Unsupported file type uploaded: {file.filename}")
                return jsonify({'error': 'Unsupported file type. Please upload .csv or .txt'}), 400
        
        except Exception as e:
            app.logger.error(f"File processing error for '{file.filename if file else 'N/A'}': {e}", exc_info=True)
            return jsonify({'error': f'Error processing file: {str(e)}'}), 500
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    app.logger.info(f"Successfully removed temp file: {temp_path}")
                except Exception as e_remove:
                    app.logger.error(f"Error removing temp file {temp_path}: {e_remove}")
    
    # This branch handles pasted text if no file was uploaded or if file upload was skipped
    if not file_uploaded:
        messages_text = request.form.get('messages_text', '')
        app.logger.info(f"Pasted text received. Length: {len(messages_text)}")
        if not messages_text:
            # This case should ideally be hit only if neither file nor text is provided.
            # If file_uploaded was true but messages list is empty (e.g. empty file), it's handled below.
            app.logger.warning("No file uploaded and no text pasted for batch prediction.")
            return jsonify({'error': 'No file or text provided for batch prediction'}), 400
        messages = [msg.strip() for msg in messages_text.split('\\n') if msg.strip()]

    if not messages:
        app.logger.warning("No messages found after processing input or file (e.g., empty file or only whitespace text).")
        return jsonify({'error': 'No messages found in the input, or the file was empty/malformed.'}), 400
        
    try:
        app.logger.info(f"Predicting for {len(messages)} messages.")
        results = detector.predict(messages) 
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Batch prediction error: {e}", exc_info=True)
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    data = request.get_json()
    if not data:
        app.logger.error("Feedback endpoint received no JSON data.")
        return jsonify({'error': 'No JSON data received'}), 400

    message = data.get('message')
    actual_label = data.get('actual_label')  # Expected: 'spam' or 'ham'
    predicted_label_str = data.get('predicted_label')  # Expected: 'Spam' or 'Not Spam'

    # Log exactly what was received
    app.logger.info(f"Feedback received: message='{message}', actual_label='{actual_label}', predicted_label_str='{predicted_label_str}'")

    if not message or not actual_label or predicted_label_str is None:
        # Log which specific field(s) were considered missing
        missing_fields = []
        if not message:
            missing_fields.append("message (is empty or None)")
        if not actual_label:
            missing_fields.append("actual_label (is empty or None)")
        if predicted_label_str is None: # Check specifically for None for predicted_label_str
            missing_fields.append("predicted_label (is None)")
        
        app.logger.warning(f"Feedback attempt missing data. Problem fields: {', '.join(missing_fields)}. Raw received: data='{data}'")
        return jsonify({'error': 'Missing data for feedback. Required fields: message, actual_label, predicted_label.'}), 400

    # Convert predicted_label_str to 'spam' or 'ham' for storage consistency if needed
    # current logic in script.js already sends actual_label as 'spam' or 'ham'
    # predicted_label_str is 'Spam' or 'Not Spam'

    try:
        feedback_df = pd.DataFrame([[message, predicted_label_str, actual_label]], columns=['message', 'predicted_as', 'user_marked_as_actual'])
        
        # Standardize column names for feedback CSV if they were different before
        # For example, if you want 'v2' and 'v1' like your training data:
        # feedback_to_store_df = pd.DataFrame([[message, actual_label]], columns=['v2', 'v1'])


        if os.path.exists(FEEDBACK_FILE):
            feedback_df.to_csv(FEEDBACK_FILE, mode='a', header=False, index=False, encoding='utf-8')
        else:
            feedback_df.to_csv(FEEDBACK_FILE, mode='w', header=True, index=False, encoding='utf-8')
        
        app.logger.info(f"Feedback stored successfully for message: {message[:50]}...")
        return jsonify({'status': 'success', 'message': 'Feedback received. Thank you!'})
    except Exception as e:
        app.logger.error(f"Feedback storage error: {e}", exc_info=True)
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