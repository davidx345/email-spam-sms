# model.py
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os

class SpamDetector:
    def __init__(self):
        self.vectorizer = CountVectorizer()
        self.model = MultinomialNB()
        self.is_trained = False
    
    def train(self, data_path):
        # Try different encodings
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(data_path, encoding=encoding)
                break  # If successful, exit the loop
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise ValueError("Could not read the CSV file with any of the attempted encodings")

        # Convert labels to binary (0 for ham, 1 for spam)
        df['label_num'] = df['v1'].map({'ham': 0, 'spam': 1})
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            df['v2'], df['label_num'], test_size=0.2, random_state=42
        )
        
        # Vectorize the text data
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # Train the model
        self.model.fit(X_train_vec, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred)
        
        self.is_trained = True
        
        return accuracy, report
    
    def predict(self, text):
        if not self.is_trained:
            raise Exception("Model not trained yet. Call train() first.")
        
        # If input is a single string, convert to list
        if isinstance(text, str):
            text = [text]
        
        # Vectorize the input text
        text_vec = self.vectorizer.transform(text)
        
        # Predict
        prediction = self.model.predict(text_vec)
        
        # Get probability scores
        prob = self.model.predict_proba(text_vec)
        
        # Return result as a list of dicts for each input text
        results = []
        for i, pred in enumerate(prediction):
            results.append({
                'text': text[i],
                'is_spam': bool(pred),
                'spam_probability': float(prob[i][1]),
                'prediction': 'Spam' if pred else 'Not Spam'
            })
        
        return results[0] if len(results) == 1 else results
    
    def save_model(self, path="model"):
        if not self.is_trained:
            raise Exception("Model not trained yet. Call train() first.")
        
        os.makedirs(path, exist_ok=True)
        
        # Save vectorizer and model
        with open(f"{path}/vectorizer.pkl", 'wb') as f:
            pickle.dump(self.vectorizer, f)
        
        with open(f"{path}/model.pkl", 'wb') as f:
            pickle.dump(self.model, f)
    
    def load_model(self, path="model"):
        # Load vectorizer
        with open(f"{path}/vectorizer.pkl", 'rb') as f:
            self.vectorizer = pickle.load(f)
        
        # Load model
        with open(f"{path}/model.pkl", 'rb') as f:
            self.model = pickle.load(f)
        
        self.is_trained = True

# Example usage
if __name__ == "__main__": 
    detector = SpamDetector()
    # You need a CSV file with 'message' and 'label' columns
    # Example: detector.train("spam_dataset.csv")
    
    # Example prediction
    # result = detector.predict("Congratulations! You've won $1000. Reply YES to claim.")
    # print(result)