import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
import glob
import os


def train():
    # path to your parquet files
    path = '/Users/mishitakaja/satellite-pipeline/data_lake/telemetry'
    all_files = glob.glob(os.path.join(path, "*.parquet"))

    if not all_files:
        print("No data found in Data Lake!")
        return

    # load
    print(f"Loading {len(all_files)} files from Data Lake...")
    df_list = [pd.read_parquet(f) for f in all_files]
    df = pd.concat(df_list, ignore_index=True)

    features = ['altitude', 'velocity', 'battery_temp']
    X = df[features]

    # train
    print("Training Isolation Forest model...")
    model = IsolationForest(contamination=0.1, random_state=42)
    model.fit(X)

    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/anomaly_model.pkl')
    print("Model trained and saved to models/anomaly_model.pkl")


if __name__ == "__main__":
    train()
