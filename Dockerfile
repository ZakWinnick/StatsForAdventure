FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user to run the application
RUN useradd -m appuser
USER appuser

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=run.py

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--worker-class", "socketio.gunicorn.workers.SocketIOWorker", "run:app"]