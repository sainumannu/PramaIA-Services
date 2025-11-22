#!/bin/bash
# Script di avvio rapido per Mac/Linux
cd "$(dirname "$0")"
pip3 install -r requirements.txt
python3 src/main.py
