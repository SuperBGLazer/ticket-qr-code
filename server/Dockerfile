FROM python:3.11-slim

# Set a working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


COPY . .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the Flask app code
# Expose Gunicorn port
EXPOSE 5000

# By default, we'll rely on the docker-compose 'command' to run Gunicorn
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:5000"]
