# BASE IMAGE
# Using NVIDIA CUDA image as required by competition rules
# Even if using CPU-only, this ensures environment compatibility with organizers.
FROM nvidia/cuda:12.2.0-devel-ubuntu20.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# ------------------------------------------------------------
# SYSTEM DEPENDENCIES
# ------------------------------------------------------------
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Link python3 to python make sure scripts work
RUN ln -s /usr/bin/python3 /usr/bin/python

# ------------------------------------------------------------
# PROJECT SETUP
# ------------------------------------------------------------
WORKDIR /code

# Copy specific files first to leverage Docker cache
COPY requirements.txt /code/requirements.txt

# ------------------------------------------------------------
# INSTALL LIBRARIES
# ------------------------------------------------------------
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the source code
COPY . /code

# Grant execution permission to the entrypoint script
RUN chmod +x inference.sh

# ------------------------------------------------------------
# EXECUTION
# ------------------------------------------------------------
CMD ["bash", "inference.sh"]
