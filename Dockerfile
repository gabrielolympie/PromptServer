# Use an official Python runtime as a parent image
FROM python:3.11-slim-buster

# Set the working directory in the container to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Display the content of the .env file
# RUN cat .env

RUN pip install --no-cache-dir -r requirements.txt

# Read port from .env file during build time
RUN export PORT=8080

# Make the specified port available to the world outside the container
EXPOSE $PORT

## Seting modal token
CMD uvicorn app:app --host 0.0.0.0 --port 8080
