#!/bin/bash

# Create templates directory if it doesn't exist
mkdir -p templates

# Copy API files
cp ../api_script/main.py .
cp ../api_script/facade.py .
cp ../api_script/requirements.txt .
cp ../api_script/templates/upload.html templates/

# Apply kustomization
kubectl apply -k .

# Clean up copied files
rm main.py facade.py requirements.txt
rm -rf templates 