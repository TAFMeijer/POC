FROM python:3.11-slim

# Set up a new user to prevent running as root (Good practice for Hugging Face Spaces)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    # Hugging Face runs natively on port 7860
    PORT=7860 

WORKDIR $HOME/app

# Only copy requirements.txt first to leverage Docker layer caching
COPY --chown=user requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application
COPY --chown=user . .

# Run Gunicorn with 2 workers bound to the port specified by HuggingFace
CMD ["gunicorn", "-b", "0.0.0.0:7860", "-w", "2", "app:server"]
