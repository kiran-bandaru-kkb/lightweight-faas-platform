# Use official Python image
FROM python:3.10-slim

# Set workdir
WORKDIR /app

# Install system dependencies (if any, e.g. gcc)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Collect static files if needed (optional)
# RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
