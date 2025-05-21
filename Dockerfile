# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY main.py .
COPY blacklist.txt .
# COPY .env . # Optional: if .env file is used and needs to be in the container

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable for the Uvicorn server (optional, can be overridden)
ENV MODULE_NAME="main:app"
ENV VARIABLE_NAME="app" # Should be 'app' as per main.py

# Run main.py when the container launches
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
