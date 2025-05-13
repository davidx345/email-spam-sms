# SMS Spam Detector

A machine learning-based SMS spam detection system built with Flask, scikit-learn, and Python.

## Overview

This project uses Natural Language Processing (NLP) and Machine Learning techniques to classify SMS messages as either spam or legitimate (ham). It provides a web interface for real-time classification of messages.

## Features

- Real-time SMS message classification
- Web interface for easy interaction
- RESTful API for integration with other applications
- High accuracy Naive Bayes classifier
- Automatic model retraining capabilities

## Tech Stack

- Python 3.x
- Flask (Web Framework)
- scikit-learn (Machine Learning)
- Pandas (Data Processing)
- NumPy (Numerical Operations)
- HTML/CSS/JavaScript (Frontend)

## Project Structure

```
.
├── app.py                  # Flask application
├── model.py                # Spam detector class
├── train_model.py          # Script to train the model
├── requirements.txt        # Project dependencies
├── spam_dataset.csv        # Training dataset
├── model/                  # Saved model files
│   ├── model.pkl           # Trained model
│   └── vectorizer.pkl      # Text vectorizer
├── static/                 # Static files
│   ├── css/
│   └── js/
└── templates/              # HTML templates
    └── index.html          # Main interface
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/davidx345/email-spam-sms.git
cd email-spam-sms
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Unix/MacOS
source venv/bin/activate
```

3. Install the requirements:
```bash
pip install -r requirements.txt
```

4. Train the model:
```bash
python train_model.py
```

5. Run the application:
```bash
python app.py
```

6. Open your browser and navigate to `http://127.0.0.1:5000`

## API Usage

The application provides a simple REST API:

- **Endpoint**: `/predict`
- **Method**: POST
- **Content-Type**: application/json
- **Request Body**:
```json
{
    "message": "Your SMS message here"
}
```
- **Response**:
```json
{
    "text": "Your SMS message here",
    "is_spam": true,
    "spam_probability": 0.92,
    "prediction": "Spam"
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The SMS Spam Collection dataset
- scikit-learn documentation and community
- Flask framework

## Contact

David - [GitHub](https://github.com/davidx345)
