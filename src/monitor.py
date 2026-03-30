import pandas as pd
from sqlalchemy import create_engine
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
import time

engine = create_engine(
    'postgresql://user:password@localhost:5432/telemetry_db')


def check_drift():
    reference_data = pd.read_csv("models/reference_data.csv")

    while True:
        # Get last 100 records from Postgres
        current_data = pd.read_sql(
            "SELECT altitude, velocity, battery_temp FROM telemetry ORDER BY ingestion_time DESC LIMIT 100", engine)

        if len(current_data) >= 100:
            drift_report = Report(metrics=[DataDriftPreset()])
            drift_report.run(reference_data=reference_data,
                             current_data=current_data)

            # Save report as HTML for your portfolio
            drift_report.save_html("monitoring/drift_report.html")
            print("Drift report updated at monitoring/drift_report.html")

        time.sleep(60)  # Run every minute


if __name__ == "__main__":
    check_drift()
