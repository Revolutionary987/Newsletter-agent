FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH

# 1. 🚨 WEASYPRINT DEPENDENCIES: Install system-level Linux libraries as root
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libglib2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# 2. Create the non-root user for Hugging Face security
RUN useradd -m -u 1000 user
WORKDIR $HOME/app

# 3. Copy requirements first to leverage Docker cache
COPY --chown=user:user requirements.txt .

# 4. Switch to the non-root user to install Python packages safely
USER user
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of the application code
COPY --chown=user:user . .

EXPOSE 7860

CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "7860"]