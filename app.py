import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
import os


class HeartRiskPredictor:
    def __init__(
        self,
        model_path='heart_model.h5',
        preprocessor_path='preprocessor.pkl'
    ):
        self.MODEL_PATH = model_path
        self.PREPROCESSOR_PATH = preprocessor_path
        self._model = None
        self._preprocessor = None

    def _load_assets(self):
        """
        Loads the Keras model and scikit-learn preprocessor
        if not already loaded.
        """

        # Load Deep Learning Model
        if self._model is None and os.path.exists(self.MODEL_PATH):
            self._model = tf.keras.models.load_model(
                self.MODEL_PATH,
                compile=False
            )

        # Load Preprocessor
        if self._preprocessor is None and os.path.exists(self.PREPROCESSOR_PATH):
            self._preprocessor = joblib.load(self.PREPROCESSOR_PATH)

    def predict_heart_risk(self, input_data, threshold=0.45):
        """
        Predicts heart disease risk and returns:
        - target
        - probability percentage
        - risk category
        - status message
        """

        # Ensure model and preprocessor are loaded
        self._load_assets()

        # Check if assets loaded successfully
        if self._model is None:
            return None, 0.0, "Error", "Model file not found."

        if self._preprocessor is None:
            return None, 0.0, "Error", "Preprocessor file not found."

        try:
            # Convert input into DataFrame
            # Convert input into DataFrame (SAFE FIX)
            clean_input = {
                k: (v.item() if hasattr(v, "item") else v)
                for k, v in input_data.items()
            }

            df_input = pd.DataFrame([clean_input])

            # Preprocess input data
            processed_data = self._preprocessor.transform(df_input)
            
            # Ensure data is float32 for TensorFlow model prediction
            processed_data = processed_data.astype(np.float32)

            # Generate prediction probability
            probability = float(
                self._model.predict(
                    processed_data,
                    verbose=0
                )[0][0]
            )

            # Convert to percentage
            percentage = round(probability, 4)

            # Apply threshold
            target = 1 if probability >= threshold else 0

            # Risk Classification
            if probability < 0.30:
                category = "Low Risk"

            elif probability < threshold:
                category = "Borderline / Moderate Risk"

            elif probability < 0.75:
                category = "High Risk"

            else:
                category = "Critical Risk"

            return target, percentage, category, "Success"

        except Exception as e:
            return None, 0.0, "Error", str(e) reshare code fix indention
