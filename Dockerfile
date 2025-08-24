# Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create a non-root user with specific UID and GID
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid 1001 --create-home --shell /bin/bash appuser

# Copy shared libraries
COPY shared-libs /app/shared-libs

# Set proper ownership and permissions
RUN chown -R 1001:1001 /app
ENV PYTHONPATH="/app:/app/shared-libs"

# Copy gateway service code
COPY . /app

# Change ownership of copied files
RUN chown -R 1001:1001 /app

# Install dependencies as root (required for package installation)
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER 1001

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]