# -------------------
# 1) Base stage
# -------------------
FROM ubuntu:22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    HOME="/home/appuser"

# Install system dependencies
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
        libglib2.0-0 \
        postgresql-client \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN groupadd -r appuser && \
    useradd -m -r -g appuser --uid 1000 appuser && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Install pip (user local)
RUN wget https://bootstrap.pypa.io/get-pip.py && \
    python3 get-pip.py --user && \
    rm get-pip.py

# Create a directory for Certbot (if needed)
RUN mkdir -p /var/www/certbot && \
    chown -R appuser:appuser /var/www/certbot

# -------------------
# 2) Builder stage (Install PyTorch, detectron2, etc.)
# -------------------
FROM base AS builder

WORKDIR /home/appuser
USER appuser

ENV PATH="/home/appuser/.local/bin:${PATH}" \
    HOME="/home/appuser"

# (Optional) upgrade pip
RUN python3 -m pip install --user --upgrade pip

# Install big dependencies that won't change often
RUN python3 -m pip install --user --no-cache-dir \
    tensorboard cmake onnx \
    torch torchvision torchaudio \
    'git+https://github.com/facebookresearch/fvcore'

# Clone and install Detectron2 from source
RUN git clone https://github.com/facebookresearch/detectron2 detectron2_repo && \
    python3 -m pip install --user -e detectron2_repo

# -------------------
# 3) Final stage
# -------------------
FROM base

WORKDIR /home/appuser
USER appuser

# Copy installed libs from builder
COPY --from=builder /home/appuser/.local /home/appuser/.local

ENV PATH="/home/appuser/.local/bin:${PATH}" \
    HOME="/home/appuser" \
    FVCORE_CACHE="/tmp"

# 3.1) Copy requirements.txt first (so if only code changes, cache layer remains)
COPY requirements.txt /home/appuser/requirements.txt

# 3.2) Install Python dependencies from requirements.txt
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# 3.3) Copy the rest of the project
COPY . /home/appuser

# (Optional) Collect static files during build
RUN python3 manage.py collectstatic --no-input

EXPOSE 8000

# 3.4) Run gunicorn
CMD ["gunicorn", "--workers=7", "--timeout=90", "--bind=0.0.0.0:8000", "AI_Dental_Health_APP.wsgi:application"]
