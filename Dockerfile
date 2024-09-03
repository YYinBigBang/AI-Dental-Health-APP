# Use the official Ubuntu 22.04 image as the base image
FROM ubuntu:22.04 AS base

# Set environment variables to ensure Python runs in a non-interactive mode
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV HOME="/home/appuser"

# Install system dependencies and create a non-root user and group
RUN apt-get update && \
    apt-get install -y \
    ca-certificates \
    git \
    wget \
    sudo \
    python3.10 \
    python3.10-dev \
    build-essential \
    cmake \
    libjpeg-dev \
    libpng-dev \
    libgl1 \
    libglib2.0-0 && \
    ln -sv /usr/bin/python3.10 /usr/bin/python3 && \
    ln -sv /usr/bin/python3.10 /usr/bin/python && \
    wget https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py --user && \
    rm get-pip.py && \
    # Ensure appuser and appuser group are created
    groupadd -r appuser && \
    useradd -m -r -g appuser --uid 1000 appuser && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a directory for Certbot and set permissions
RUN mkdir -p /var/www/certbot && \
    chown -R appuser:appuser /var/www/certbot

# Use a multi-stage build to install PyTorch and other dependencies
FROM base AS builder

# Ensure pip is available in the PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV HOME="/home/appuser"

# Set the working directory inside the container
WORKDIR /home/appuser

# Install PyTorch dependencies
RUN python3 -m pip install --user --upgrade pip && \
    python3 -m pip install --user --no-cache-dir tensorboard cmake onnx && \
    python3 -m pip install --user --no-cache-dir torch torchvision torchaudio && \
    python3 -m pip install --user --no-cache-dir 'git+https://github.com/facebookresearch/fvcore'

# Clone and install Detectron2
RUN git clone https://github.com/facebookresearch/detectron2 detectron2_repo && \
    python3 -m pip install --user -e detectron2_repo

# Create the final stage from the base image
FROM base

# Set the working directory inside the container
WORKDIR /home/appuser

# Copy the installed Python dependencies from the builder stage
COPY --from=builder /home/appuser/.local /home/appuser/.local

# Ensure pip is available in the PATH
ENV PATH="/home/appuser/.local/bin:${PATH}"
ENV HOME="/home/appuser"

# Set a fixed model cache directory
ENV FVCORE_CACHE="/tmp"

# Copy the dependency file to the current directory
COPY requirements.txt .

# Install any additional dependencies listed in the requirements.txt file
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Install detectron2 directly in the final stage to ensure it's available
RUN python3 -m pip install --no-cache-dir 'git+https://github.com/facebookresearch/detectron2'

# Copy the current directory contents into the container at /home/appuser
COPY . .

# Run Django's collectstatic command as part of the build process
RUN python3 manage.py collectstatic --no-input

# Expose port 8000 for internal use
EXPOSE 8000

# Start the Gunicorn server, specifying the number of workers and the WSGI application
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:8000", "AI_Dental_Health_APP.wsgi:application"]