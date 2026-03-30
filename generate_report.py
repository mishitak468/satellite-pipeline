import os
import glob
import pandas as pd
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset


def generate():
    """
    Analyzes data drift between baseline telemetry and recent live data.
    Useful for detecting anomalies like the 'Solar Flare' simulation.
    """
    # Use an environment variable or a relative path for portability
    # This defaults to the Docker path but works locally if the folder exists
    data_path = os.getenv("DATA_LAKE_PATH", "data_lake/telemetry/*.parquet")

    files = sorted(glob.glob(data_path))

    if not files:
        print(f"Error: No data found at {data_path}")
        return

    if len(files) < 20:
        print(
            f"Warning: Only found {len(files)} files. Results may not be statistically significant.")

    # Compare early 'Normal' data against the latest 'Live' data
    # Adjust slicing based on how much data you want to compare
    reference_df = pd.concat([pd.read_parquet(f) for f in files[:50]])
    current_df = pd.concat([pd.read_parquet(f) for f in files[-50:]])

    print(
        f"Analyzing drift for {len(current_df)} recent records against baseline...")

    report = Report(metrics=[
        DataDriftPreset(),
        TargetDriftPreset()
    ])

    report.run(reference_data=reference_df, current_data=current_df)

    output_file = "satellite_drift_report.html"
    report.save_html(output_file)

    print(f"--- SUCCESS! ---")
    print(f"Report saved to: {output_file}")


if __name__ == "__main__":
    generate()
