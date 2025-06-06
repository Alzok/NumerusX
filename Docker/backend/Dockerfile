# Docker/backend/Dockerfile

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install build essentials, including gcc, and other dependencies for TA-Lib
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    pkg-config \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    libblas-dev \
    libffi-dev \
    # Add any other system-level dependencies your Python packages might need
    && rm -rf /var/lib/apt/lists/*

# Download and install TA-Lib from source
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Set the working directory in the container
WORKDIR /code

# Copy requirements.txt from the project root
COPY requirements.txt /code/

# Install build dependencies first with specific compatible versions
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install numpy and cython first, as they are often build dependencies for other packages
RUN pip install --no-cache-dir "numpy>=1.24.0,<2.0.0" "cython>=0.29.0"

# Install CPU-only PyTorch first to avoid CUDA downloads that cause timeouts
RUN pip install --no-cache-dir torch==2.1.2+cpu --index-url https://download.pytorch.org/whl/cpu

# Install Python dependencies from requirements.txt (torch will be ignored since already installed)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application code
COPY app /code/app

# Copy .env.example and entrypoint script
COPY .env.example /code/
COPY Docker/backend/entrypoint.sh /code/

# Make entrypoint script executable
RUN chmod +x /code/entrypoint.sh

# Set the working directory to where your main application file is
WORKDIR /code

# Add /code to Python path so imports work correctly
ENV PYTHONPATH=/code

# Expose the port the app runs on
EXPOSE 8000

# Use entrypoint script
ENTRYPOINT ["/code/entrypoint.sh"]

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 