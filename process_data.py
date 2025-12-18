import sys
import os

sys.path.append(os.getcwd())

from src.etl.ingest import run_ingestion

if __name__ == "__main__":
    print("--- STARTING DATA PROCESSING (Ingestion) ---")
    try:
        # Run ingestion with default parameters
        # Adjust batch_size if running on limited memory environment
        run_ingestion(batch_size=10, upload_batch_size=50)
        print("--- DATA PROCESSING COMPLETE ---")
    except Exception as e:
        print(f"## Data Processing Failed: {e}")
        sys.exit(1)
