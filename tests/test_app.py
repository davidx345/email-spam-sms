import pytest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, initialize_model
from model import SpamDetector

@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def spam_detector():
    """Create a SpamDetector instance for testing."""
    return SpamDetector()

@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return {
        'ham_messages': [
            "Hi, how are you doing today?",
            "Let's meet for coffee tomorrow",
            "Thanks for the help yesterday"
        ],
        'spam_messages': [
            "URGENT! You have won $1000! Click here now!",
            "Free viagra! No prescription needed!",
            "Congratulations! You've won a free iPhone!"
        ]
    }

class TestSpamDetector:
    """Test cases for the SpamDetector class."""
    
    def test_initialization(self, spam_detector):
        """Test SpamDetector initialization."""
        assert spam_detector.vectorizer is not None
        assert spam_detector.model is not None
        assert spam_detector.is_trained is False
    
    def test_predict_without_training(self, spam_detector):
        """Test prediction without training should raise exception."""
        with pytest.raises(Exception) as exc_info:
            spam_detector.predict("Test message")
        
        assert "Model not trained yet" in str(exc_info.value)
    
    def test_train_with_valid_data(self, spam_detector, tmp_path):
        """Test training with valid CSV data."""
        # Create a temporary CSV file
        csv_content = """v1,v2
ham,This is a normal message
spam,WIN FREE MONEY NOW!!!
ham,How are you today?
spam,URGENT: Click here for prize
ham,See you tomorrow
spam,Free pills no prescription"""
        
        csv_file = tmp_path / "test_data.csv"
        csv_file.write_text(csv_content)
        
        accuracy, report = spam_detector.train(str(csv_file))
        
        assert isinstance(accuracy, float)
        assert 0 <= accuracy <= 1
        assert spam_detector.is_trained is True
        assert report is not None
    
    def test_predict_after_training(self, spam_detector, tmp_path, sample_data):
        """Test prediction after proper training."""
        # Create training data
        csv_content = "v1,v2\n"
        for msg in sample_data['ham_messages']:
            csv_content += f"ham,{msg}\n"
        for msg in sample_data['spam_messages']:
            csv_content += f"spam,{msg}\n"
        
        csv_file = tmp_path / "train_data.csv"
        csv_file.write_text(csv_content)
        
        # Train the model
        spam_detector.train(str(csv_file))
        
        # Test prediction
        result = spam_detector.predict("WIN FREE MONEY NOW!")
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert 'prediction' in result[0]
        assert 'probability' in result[0]
    
    def test_save_and_load_model(self, spam_detector, tmp_path):
        """Test model saving and loading functionality."""
        # Create minimal training data
        csv_content = """v1,v2
ham,Normal message
spam,Spam message
ham,Another normal message
spam,Another spam message"""
        
        csv_file = tmp_path / "train_data.csv"
        csv_file.write_text(csv_content)
        
        # Train and save model
        spam_detector.train(str(csv_file))
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        spam_detector.save_model(str(model_dir))
        
        # Create new detector and load model
        new_detector = SpamDetector()
        new_detector.load_model(str(model_dir))
        
        assert new_detector.is_trained is True
        
        # Test that loaded model can make predictions
        result = new_detector.predict("Test message")
        assert isinstance(result, list)

class TestFlaskApp:
    """Test cases for the Flask application."""
    
    def test_index_route(self, client):
        """Test the index route."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    @patch('app.detector')
    def test_predict_api_success(self, mock_detector, client):
        """Test successful prediction API call."""
        # Mock the detector
        mock_detector.predict.return_value = [{
            'prediction': 'Spam',
            'probability': 0.95,
            'is_spam': True
        }]
        mock_detector.is_trained = True
        
        response = client.post('/predict', 
                             json={'message': 'WIN FREE MONEY!'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['prediction'] == 'Spam'
        assert data['is_spam'] is True
        assert 'spam_probability' in data
    
    def test_predict_api_missing_message(self, client):
        """Test prediction API with missing message."""
        response = client.post('/predict', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_predict_api_invalid_json(self, client):
        """Test prediction API with invalid JSON."""
        response = client.post('/predict',
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
    
    @patch('app.detector')
    def test_metrics_endpoint(self, mock_detector, client):
        """Test metrics endpoint for monitoring."""
        response = client.get('/metrics')
        assert response.status_code == 200
        
        # Check if response contains Prometheus-style metrics
        data = response.get_data(as_text=True)
        assert 'spam_detector_' in data or 'flask_' in data

class TestModelPerformance:
    """Performance and load testing for the model."""
    
    @pytest.mark.slow
    def test_prediction_performance(self, spam_detector, tmp_path):
        """Test prediction performance with multiple messages."""
        import time
        
        # Create training data
        csv_content = "v1,v2\n"
        for i in range(100):
            csv_content += f"ham,Normal message {i}\n"
            csv_content += f"spam,Spam message {i} WIN FREE MONEY\n"
        
        csv_file = tmp_path / "perf_data.csv"
        csv_file.write_text(csv_content)
        
        # Train model
        spam_detector.train(str(csv_file))
        
        # Test batch prediction performance
        messages = [f"Test message {i}" for i in range(100)]
        
        start_time = time.time()
        results = spam_detector.predict(messages)
        end_time = time.time()
        
        # Should process 100 messages in less than 1 second
        assert end_time - start_time < 1.0
        assert len(results) == 100
    
    def test_memory_usage(self, spam_detector, tmp_path):
        """Test memory usage doesn't grow excessively."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create and train multiple models
        for i in range(5):
            csv_content = f"v1,v2\nham,Message {i}\nspam,Spam {i}\n"
            csv_file = tmp_path / f"data_{i}.csv"
            csv_file.write_text(csv_content)
            
            detector = SpamDetector()
            detector.train(str(csv_file))
            
            # Make some predictions
            for j in range(10):
                detector.predict(f"Test message {j}")
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB)
        assert memory_growth < 100 * 1024 * 1024

class TestIntegration:
    """Integration tests combining multiple components."""
    
    @patch('app.detector')
    def test_full_workflow(self, mock_detector, client, tmp_path):
        """Test complete workflow from training to prediction."""
        # Mock successful training
        mock_detector.train.return_value = (0.95, "Classification report...")
        mock_detector.is_trained = True
        mock_detector.predict.return_value = [{
            'prediction': 'Ham',
            'probability': 0.85,
            'is_spam': False
        }]
        
        # Test web interface
        response = client.get('/')
        assert response.status_code == 200
        
        # Test API prediction
        response = client.post('/predict', 
                             json={'message': 'Hello friend'})
        assert response.status_code == 200
        
        # Test health check
        response = client.get('/health')
        assert response.status_code == 200

if __name__ == '__main__':
    pytest.main(['-v', '--cov=.', '--cov-report=html'])
