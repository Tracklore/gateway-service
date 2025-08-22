# Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy shared libraries
COPY gateway-service/shared-libs /app/shared-libs

ENV PYTHONPATH "${PYTHONPATH}:/app/shared-libs"

# Copy gateway service code
COPY gateway-service /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]