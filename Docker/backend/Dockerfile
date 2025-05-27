# Docker/backend/Dockerfile

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install build essentials, including gcc, and other dependencies for TA-Lib
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    pkg-config \
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

# Install numpy and cython first, as they are often build dependencies for other packages
RUN pip install --no-cache-dir numpy==1.24.3 cython

# Install Python dependencies from requirements.txt
# TA-Lib should now find the system library installed above
# scikit-learn will build using the pre-installed numpy and cython
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application code
COPY app /code/app

# Set the working directory to where your main application file is
WORKDIR /code/app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 