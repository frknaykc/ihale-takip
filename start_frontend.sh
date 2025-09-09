#!/bin/bash

# Go to frontend directory
cd frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    npm install
fi

# Start the Next.js development server
npm run dev
