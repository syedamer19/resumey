FROM ollama/ollama:latest

# Install Python, pip, and curl as root
RUN apt-get update && apt-get install -y python3 python3-pip curl && rm -rf /var/lib/apt/lists/*

# Create a non-root user (matching Hugging Face user UID 1000)
RUN useradd -m -u 1000 user

# Set up working directory and change ownership
WORKDIR /home/user/app
RUN chown -R user:user /home/user

# Switch to the non-root user
USER user

# Set environment variables for Ollama to write models in user's home directory
ENV HOME=/home/user
ENV PATH="/home/user/.local/bin:${PATH}"
ENV OLLAMA_MODELS=/home/user/.ollama/models

# Copy requirements and install
COPY --chown=user:user requirements.txt .
RUN pip3 install --no-cache-dir --user -r requirements.txt

# Copy the rest of the application files
COPY --chown=user:user . .

# Fix Windows line endings and ensure run.sh is executable
RUN sed -i -e 's/\r$//' run.sh && chmod +x run.sh

# Set environment variables for the application default configuration
ENV API_PROVIDER="ollama-local"
ENV OLLAMA_HOST="http://localhost:11434"
ENV OLLAMA_MODEL="gemma2:2b"

EXPOSE 7860

CMD ["./run.sh"]
