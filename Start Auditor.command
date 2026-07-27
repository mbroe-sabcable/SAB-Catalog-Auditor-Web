#!/bin/bash

cd "/Users/maureenbroe/Desktop/SAB-Catalog-Auditor-Web"

source .venv/bin/activate

uvicorn main:app --reload &
SERVER_PID=$!

sleep 3

open http://127.0.0.1:8000

wait $SERVER_PID