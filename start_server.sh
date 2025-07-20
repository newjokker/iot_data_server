#!/bin/bash

cd  /root/Code/iot_server

source ~/venv/bin/activate

uvicorn server:app --host 0.0.0.0 --port 12345 --workers 1


