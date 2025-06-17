import joblib
from sklearn.pipeline import Pipeline

class ComplaintClassifier:
    def __init__(self, model_path='ml_classifier/complaint_classifier_model.pkl'):
        try:
            self.model = joblib.load(model_path)
        except FileNotFoundError:
            raise Exception("Model file not found. Please run train_model.py first.")

    def predict(self, description):
        return self.model.predict([description])[0]
