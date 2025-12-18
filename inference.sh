#!/bin/bash

# Exit on error
set -e

echo "=================================================="
echo "VNPT AI PIPELINE STARTED"
echo "=================================================="

# 1. Processing Data (Ingestion)
echo "[1/2] Processing Data..."
python3 process_data.py

# 2. Inference
echo "[2/2] Running Inference..."
# predict.py has fallback logic to find private_test.json in /code/ or current dir
python3 predict.py

echo "=================================================="
echo "PIPELINE FINISHED"
echo "=================================================="
