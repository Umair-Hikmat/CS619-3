import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE

def train_and_save_random_forest(data_path, preprocessor_path='preprocessor.pkl'):
    # 1. Load Data
    df = pd.read_csv(data_path)

    # Standardizing column names for the model pipeline
    df.columns = [
        "Age", "Gender", "ChestPainType", "RestingBloodPressure", "Cholesterol",
        "FastingBloodSugar", "RestECG", "MaxHeartRate", "ExerciseInducedAngina",
        "ST_Depression", "ST_Slope", "MajorVessels", "Thalassemia", "Target"
    ]

    X = df.drop('Target', axis=1)
    y = df['Target']

    # 2. Load Preprocessor
    try:
        preprocessor = joblib.load(preprocessor_path)
    except FileNotFoundError:
        print(f"Error: Preprocessor not found at {preprocessor_path}. Please run model_training.py first.")
        return

    # 3. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 4. Preprocess data using the loaded preprocessor
    X_train_proc = preprocessor.transform(X_train)
    X_test_proc = preprocessor.transform(X_test)

    # 5. Handle Imbalance (SMOTE)
    sm = SMOTE(random_state=42)
    X_res, y_res = sm.fit_resample(X_train_proc, y_train)

    # 6. Train Random Forest Classifier Model
    print("\n" + "="*30)
    print("TRAINING RANDOM FOREST CLASSIFIER MODEL")
    print("="*30)

    model_rf = RandomForestClassifier(random_state=42, n_estimators=100)
    model_rf.fit(X_res, y_res)

    # 7. Evaluate Random Forest Classifier
    y_pred_rf = model_rf.predict(X_test_proc)
    print("\n" + "="*30)
    print("RANDOM FOREST CLASSIFIER EVALUATION")
    print("="*30)
    print(classification_report(y_test, y_pred_rf))
    print("Confusion Matrix for Random Forest Classifier:")
    print(confusion_matrix(y_test, y_pred_rf))

    # 8. Save Model
    joblib.dump(model_rf, 'random_forest_model.pkl')
    print("Random Forest Classifier Model Saved: 'random_forest_model.pkl'")
    print("\nProcess Complete: Random Forest Classifier model is ready for use.")

if __name__ == "__main__":
    train_and_save_random_forest('/content/drive/MyDrive/CS619/heart.csv')
