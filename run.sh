#!/bin/bash

# Start Ollama server in the background
echo "Starting Ollama server..."
ollama serve &

# Wait for Ollama to be ready
echo "Waiting for Ollama server to start..."
until curl -s http://localhost:11434 > /dev/null; do
    sleep 1
done
echo "Ollama server is up!"

# Pull the local model
echo "Downloading local model (gemma2:2b)..."
ollama pull gemma2:2b

# Run Streamlit on Hugging Face port 7860
echo "Starting Streamlit app..."
python3 -m streamlit run app.py --server.port 7860 --server.address 0.0.0.0
