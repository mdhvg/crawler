#!/bin/bash

mkdir -p pfp downloads
touch info.json queue.json visited.json tree.json
echo "{}" > info.json
echo "[]" > queue.json
echo "[]" > visited.json
echo "{}" > tree.json

python -m venv .env
source .env/bin/activate
pip install -r requirements.txt

echo "Setup complete ✨"