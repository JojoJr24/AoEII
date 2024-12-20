#!/bin/bash

# Start Ollama server
ollama serve &

# Start the backend server
uvicorn backend.main:app --reload
