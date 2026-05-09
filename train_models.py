import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# Simulate dataset
def create_dataset():
    np.random.seed(42)
    n_samples = 1000

    data = {
        'age': np.random.randint(18, 80, n_samples),
        'gender': np.random.choice(['Male', 'Female'], n_samples),
        'height': np.random.randint(150, 200, n_samples),
        'weight': np.random.randint(50, 120, n_samples),
        'blood_sugar': np.random.uniform(70, 180, n_samples),
        'blood_pressure_sys': np.random.randint(90, 180, n_samples),
        'blood_pressure_dia': np.random.randint(60, 120, n_samples),
        'cholesterol': np.random.uniform(150, 300, n_samples),
        'smoking': np.random.choice([0, 1], n_samples),
        'snoring': np.random.choice([0, 1], n_samples),
        'exercise': np.random.choice([0, 1], n_samples),
        # Disease labels
        'diabetes': np.random.choice([0, 1], n_samples),
        'hypertension': np.random.choice([0, 1], n_samples),
        'cardiovascular': np.random.choice([0, 1], n_samples),
        'ckd': np.random.choice([0, 1], n_samples),
    }

    return pd.DataFrame(data)

# Load or create dataset
df = create_dataset()

# Feature and target preparation
X = df[['age', 'gender', 'height', 'weight', 'blood_sugar', 
        'blood_pressure_sys', 'blood_pressure_dia', 
        'cholesterol', 'smoking', 'snoring', 'exercise']]

y = df[['diabetes', 'hypertension', 'cardiovascular', 'ckd']]

# One-hot encode 'gender'
X = pd.get_dummies(X, columns=['gender'], drop_first=True)

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a RandomForestClassifier for each disease
models = {}
for disease in y.columns:
    model = RandomForestClassifier(random_state=42, n_estimators=100)
    model.fit(X_train, y_train[disease])
    models[disease] = model
    print(f"Trained model for {disease}")

    # Evaluate model
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test[disease], y_pred)
    print(f"Accuracy for {disease}: {accuracy:.2f}")

    # Save the model (changes are required for it ihave removed ml_models)
    joblib.dump(model, f'ml_models/{disease}_model.pkl')
    print(f"Saved {disease} model to ml_models/{disease}_model.pkl")
