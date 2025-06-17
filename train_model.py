import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib

def generate_sample_data():
    data = {
        'description': [
            'My laptop won’t turn on', 'Keyboard is not working', 'Monitor screen is blank',
            'Software keeps crashing', 'Application is slow', 'Error in software update',
            'Internet connection is down', 'WiFi not connecting', 'Network speed is slow',
            'Printer not responding', 'Server access issue', 'Account login problem'
        ],
        'category': [
            'hardware', 'hardware', 'hardware',
            'software', 'software', 'software',
            'network', 'network', 'network',
            'technical', 'technical', 'technical'
        ]
    }
    df = pd.DataFrame(data)
    df.to_csv('ml_classifier/training_data.csv', index=False)

def train_model():
    try:
        df = pd.read_csv('ml_classifier/training_data.csv')
    except FileNotFoundError:
        generate_sample_data()
        df = pd.read_csv('ml_classifier/training_data.csv')

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', max_features=1000)),
        ('classifier', LogisticRegression(max_iter=1000))
    ])

    pipeline.fit(df['description'], df['category'])
    joblib.dump(pipeline, 'ml_classifier/complaint_classifier_model.pkl')
    print("Model trained and saved as complaint_classifier_model.pkl")

if __name__ == '__main__':
    train_model()
