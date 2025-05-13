# train_model.py
from model import SpamDetector

def train_model():
    detector = SpamDetector()
    
    print("Starting model training...")
    accuracy, report = detector.train("spam_dataset.csv")
    detector.save_model()
    
    print(f"Model trained with accuracy: {accuracy}")
    print("Classification Report:")
    print(report)
    
    print("Model saved successfully in the 'model' directory.")

if __name__ == "__main__":
    train_model()