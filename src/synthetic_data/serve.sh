#!/bin/bash

CUDA_VISIBLE_DEVICES=5 lmdeploy serve api_server \
  /home/storage/huggingface/hub/models--Qwen--Qwen3-4B-Instruct-2507/snapshots/cdbee75f17c01a7cc42f958dc650907174af0554 \
  --server-name 127.0.0.1 \
  --server-port 8530 \
  --cache-block-seq-len 32 \
  --max-batch-size 16 \
  --cache-max-entry-count 0.3 \
  --backend "turbomind" \

