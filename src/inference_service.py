from fastapi import FastAPI, HTTPException
import joblib
import pandas as pd
from pydantic import BaseModel

app = FastAPI(title="Satellite Anomaly Inference Service")

# Load model once at startup
model = joblib.load("models/anomaly_model.pkl")


class TelemetryData(BaseModel):
    altitude: float
    velocity: float
    battery_temp: float


@app.post("/predict")
async def predict(data: TelemetryData):
    # Convert input to DataFrame for sklearn
    input_df = pd.DataFrame([data.dict()])

    # Predict: 1 = Normal, -1 = Anomaly
    prediction = model.predict(input_df)[0]
    score = model.decision_function(input_df)[0]

    return {
        "is_anomaly": int(prediction == -1),
        "anomaly_score": float(score)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
