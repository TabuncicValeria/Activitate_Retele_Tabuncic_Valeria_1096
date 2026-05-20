# Use a minimal Python base image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy the server script into the container
COPY server.py .

# Expose the communication port
EXPOSE 65432

# Set the entry point to run the server
# Using -u to ensure logs are unbuffered and visible in docker logs
CMD ["python", "-u", "server.py"]
