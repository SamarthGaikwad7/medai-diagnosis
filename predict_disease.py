import joblib

# Load models
diabetes_model = joblib.load('diabetes_model.pkl')
hypertension_model = joblib.load('hypertension_model.pkl')
cardiovascular_model = joblib.load('cardiovascular_model.pkl')
ckd_model = joblib.load('ckd_model.pkl')

def predict_disease(input_data):
    """
    Predict diseases based on user inputs.

    Args:
    - input_data: List of inputs in the order [age, height, weight, blood_sugar, 
      blood_pressure_sys, blood_pressure_dia, cholesterol, smoking, snoring, exercise, gender_encoded]

    Returns:
    - dict: Predictions for each disease.
    """
    predictions = {
        'diabetes': diabetes_model.predict([input_data])[0],
        'hypertension': hypertension_model.predict([input_data])[0],
        'cardiovascular Risk': cardiovascular_model.predict([input_data])[0],
        'Chronic Kidney Disease': ckd_model.predict([input_data])[0],
    }
    return predictions

# Example input
example_input = [45, 175, 70, 120, 140, 80, 250, 0, 1, 1, 1]  # Example values with Male encoded as 1
predictions = predict_disease(example_input)
print(predictions)
