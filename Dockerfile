# Use a lightweight Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your entire project into the container
COPY . .

# Hugging Face Spaces require running as a non-root user
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Expose the specific port Hugging Face looks for
EXPOSE 7860

# Start the FastAPI server
# Note: Ensure 'main:app' matches your filename and FastAPI variable
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "7860"]