# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for psycopg2
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into a temporary directory to leverage Docker cache
COPY requirements.txt /tmp/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy the rest of the application code into the container in a subdirectory
COPY . /app/backend

# Set the working directory to the app root
WORKDIR /app

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
# We use 0.0.0.0 to allow connections from outside the container
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
