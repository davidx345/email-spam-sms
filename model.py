# model.py
import pandas as pd
import numpy as np
# from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer # Changed to TF-IDF
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pickle
import os

class SpamDetector:
    def __init__(self):
        # self.vectorizer = CountVectorizer()\r
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2)) # Using TF-IDF with stop words and n-grams
        self.model = MultinomialNB()
        self.is_trained = False
    
    def train(self, data_path):
        # Try different encodings
        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(data_path, encoding=encoding)
                # Add a check for required columns
                if 'v1' not in df.columns or 'v2' not in df.columns:
                    print(f"Encoding {encoding} successful, but missing 'v1' or 'v2' columns.")
                    df = None # Reset df to continue loop
                    continue
                print(f"Successfully read CSV with encoding: {encoding}")
                break  # If successful, exit the loop
            except UnicodeDecodeError:
                print(f"Failed to decode with {encoding}")
                continue
            except Exception as e:
                print(f"An error occurred with encoding {encoding}: {e}")
                continue
        
        if df is None:
            raise ValueError("Could not read the CSV file with any of the attempted encodings or required columns 'v1', 'v2' are missing.")

        # Convert labels to binary (0 for ham, 1 for spam)
        # Ensure 'v1' is treated as string to avoid issues with .map if it contains non-string values
        df['label_num'] = df['v1'].astype(str).map({'ham': 0, 'spam': 1})
        
        # Handle cases where mapping might result in NaN (e.g., unexpected values in 'v1')
        # Option 1: Drop rows with NaN labels
        df.dropna(subset=['label_num'], inplace=True)
        # Option 2: Fill NaN with a default (e.g., 0 for 'ham'), but dropping is safer if labels are unexpected
        # df['label_num'].fillna(0, inplace=True) 

        # Ensure 'v2' (text messages) is treated as string
        df['v2'] = df['v2'].astype(str)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            df['v2'], df['label_num'], test_size=0.2, random_state=42, stratify=df['label_num'] # Added stratify
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
    
    def predict(self, text_input): # Renamed 'text' to 'text_input' for clarity
        if not self.is_trained:
            # Try to load the model if not trained and model files exist
            if os.path.exists(f"model/vectorizer.pkl") and os.path.exists(f"model/model.pkl"):
                print("Model not marked as trained, but files found. Attempting to load.")
                self.load_model()
            else:
                raise Exception("Model not trained yet and no pre-trained model found. Call train() or ensure model files are in 'model/' directory.")
        
        # If input is a single string, convert to list
        if isinstance(text_input, str):
            messages = [text_input]
        elif isinstance(text_input, list):
            messages = text_input
        else:
            raise ValueError("Input must be a string or a list of strings.")

        if not all(isinstance(msg, str) for msg in messages):
            raise ValueError("All items in the input list must be strings.")
            
        # Vectorize the input text
        text_vec = self.vectorizer.transform(messages)
        
        # Predict
        predictions = self.model.predict(text_vec)
        
        # Get probability scores
        probabilities = self.model.predict_proba(text_vec)
        
        # Return result as a list of dicts for each input text
        results = []
        for i, pred_label in enumerate(predictions):
            spam_probability = float(probabilities[i][1]) # Probability of being spam (class 1)
            results.append({
                'text': messages[i],
                'is_spam': bool(pred_label),
                'spam_probability': round(spam_probability * 100, 2), # As percentage
                'ham_probability': round(float(probabilities[i][0]) * 100, 2), # As percentage
                'prediction': 'Spam' if pred_label else 'Not Spam'
            })
        
        return results[0] if isinstance(text_input, str) else results # Return single dict if single string input
    
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
        vectorizer_path = f"{path}/vectorizer.pkl"
        model_path = f"{path}/model.pkl"

        if not os.path.exists(vectorizer_path) or not os.path.exists(model_path):
            raise FileNotFoundError(f"Model files not found in directory '{path}'. Please train the model first or ensure paths are correct.")
            
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
    
    # Create a dummy spam_dataset.csv for testing if it doesn't exist
    if not os.path.exists("spam_dataset.csv"):
        print("Creating a dummy spam_dataset.csv for testing.")
        dummy_data = {
            'v1': ['ham', 'spam', 'ham', 'spam', 'ham', 'spam', 'ham', 'spam', 'ham', 'spam'],
            'v2': [
                'Go until jurong point, crazy.. Available only in bugis n great world la e buffet... Cine there got amore wat...',
                'Free entry in 2 a wkly comp to win FA Cup final tkts 21st May 2005. Text FA to 87121 to receive entry question(std txt rate)T&C\'s apply 08452810075over18\'s',
                'U dun say so early hor... U c already then say...',
                'WINNER!! As a valued network customer you have been selected to receivea £900 prize reward! To claim call 09061701461. Claim code KL341. Valid 12 hours only.',
                'Nah I don\'t think he goes to usf, he lives around here though',
                'Had your mobile 11 months or more? U R entitled to Update to the latest colour mobiles with camera for Free! Call The Mobile Update Co FREE on 08002986030',
                'I\'m gonna be home soon and i don\'t want to talk about this stuff anymore tonight, k? I\'ve cried enough today.',
                'SIX chances to win CASH! From 100 to 20,000 pounds txt> CSH11 and send to 87575. Cost 150p/day, 6days, 16+ TsandCs apply Reply HL 4 info',
                'Eh u remember how 2 spell his name... Yes i did. He v naughty make until i v wet.',
                'URGENT! You have won a 1 week FREE membership in our £100,000 Prize Jackpot! Txt the word: CLAIM to No: 81010 T&C www.dbuk.net LCCLTD POBOX 4403LDNW1A7RW18'
            ]
        }
        pd.DataFrame(dummy_data).to_csv("spam_dataset.csv", index=False, encoding='utf-8')

    print("Training model with spam_dataset.csv...")
    try:
        accuracy, report = detector.train("spam_dataset.csv")
        detector.save_model()
        print(f"Model trained with accuracy: {accuracy}")
        print("Classification Report:")
        print(report)
        print("Model saved successfully in the 'model' directory.")
    except Exception as e:
        print(f"Error during training: {e}")

    # Example prediction
    if detector.is_trained:
        test_messages = [
            "Congratulations! You've won $1000. Reply YES to claim.",
            "Hey, are we still on for dinner tonight?",
            "URGENT! Your account has been compromised. Click here to secure it."
        ]
        results = detector.predict(test_messages)
        print("\\nPredictions:")
        for res in results:
            print(f"Text: {res['text']}")
            print(f"  Prediction: {res['prediction']}, Spam Probability: {res['spam_probability']}%\\n")
        
        single_result = detector.predict("This is a normal message.")
        print(f"Text: {single_result['text']}")
        print(f"  Prediction: {single_result['prediction']}, Spam Probability: {single_result['spam_probability']}%")
    else:
        print("\\nSkipping prediction examples as model training failed or was skipped.")