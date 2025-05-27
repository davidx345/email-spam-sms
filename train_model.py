# train_model.py
from model import SpamDetector
import os
import pandas as pd

def train_model():
    detector = SpamDetector()
    
    dataset_path = "spam_dataset.csv"

    # Create a dummy spam_dataset.csv for testing if it doesn't exist
    if not os.path.exists(dataset_path):
        print(f"Dataset '{dataset_path}' not found. Creating a dummy dataset for training.")
        dummy_data = {
            'v1': ['ham', 'spam', 'ham', 'spam', 'ham', 'spam', 'ham', 'spam', 'ham', 'spam',
                   'ham', 'spam', 'ham', 'spam', 'ham', 'spam', 'ham', 'spam', 'ham', 'spam'],
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
                'URGENT! You have won a 1 week FREE membership in our £100,000 Prize Jackpot! Txt the word: CLAIM to No: 81010 T&C www.dbuk.net LCCLTD POBOX 4403LDNW1A7RW18',
                'Ok lar... Joking wif u oni...',
                'FreeMsg Hey there darling it\'s been 3 week\'s now and no word back! I\'d like some fun you up for it still? Tb ok! XxX std chgs to send, £1.50 to rcv',
                'Even my brother is not like to speak with me. They treat me like aids patent.',
                'REMINDER FROM O2: To get 2.50 pounds free call credit and details of great offers pls reply 2 this text with YES. Offer ends 14th July. Subs six pounds per month.',
                'I HAVE A DATE ON SUNDAY WITH WILL!!',
                'XXXMobileMovieClub: To use your credit, click the WAP link in the next txt message or click here>> http://wap. xxxmobilemovieclub.com?n=QJKGIGHJJGCBL',
                'As per your request \'Melle Melle (Oru Minnaminunginte Nurungu Vettam)\' has been set as your callertune for all Callers. Press *9 to copy your friends Callertune',
                'England v Macedonia - dont miss the goals/team news. Txt ur national team to 87077 eg ENGLAND to 87077 Try:WALES, SCOTLAND 4txt/ú1.20 POBOXox36504W45WQ 16+',
                'Is that seriously how you spell his name?',
                'Congratulations! You have won a NINTENDO DS Lite Console! To claim call 09061701497. Code 6969. Valid 12hrs. 150ppm. T&Cs apply 18+'
            ]
        }
        pd.DataFrame(dummy_data).to_csv(dataset_path, index=False, encoding='utf-8')
        print(f"Dummy dataset '{dataset_path}' created.")

    print("Starting model training...")
    try:
        accuracy, report = detector.train(dataset_path) # Use the variable
        detector.save_model() # Saves to "model/model.pkl" and "model/vectorizer.pkl"
        
        print(f"Model trained with accuracy: {accuracy}")
        print("Classification Report:")
        print(report)
        print("Model saved successfully in the 'model' directory.")
    except FileNotFoundError as e:
        print(f"Error: {e}. Please ensure '{dataset_path}' exists or the path is correct.")
    except ValueError as e:
        print(f"ValueError during training: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during training: {e}")

if __name__ == "__main__":
    train_model()