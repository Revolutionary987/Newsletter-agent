# Use a lightweight Python image
FROM python:3.11-slim

# Hugging Face Spaces require running as a non-root user
# We must create the user FIRST
RUN useradd -m -u 1000 user

# Set the working directory
WORKDIR /app

# Copy the requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# COPY files and assign ownership to the non-root user instantly
COPY --chown=user:user . .

# Now switch to the user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose the specific port Hugging Face looks for
EXPOSE 7860

# Start the FastAPI server
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "7860"]