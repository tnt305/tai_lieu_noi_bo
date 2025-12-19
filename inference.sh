#!/bin/bash

set -e

echo "=================================================="
echo "1 2 3 VNPTAI XINCHAO"
echo "=================================================="

# # 1. Processing Data (Ingestion)
echo "[1/2] Processing Data..."
python3 process_data.py

# 2. Inference
echo "[2/2] Running Inference..."
python3 predict.py

echo "=================================================="
echo "PIPELINE FINISHED"
echo "=================================================="
