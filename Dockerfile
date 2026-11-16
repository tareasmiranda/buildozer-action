FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV USER=user
ENV HOME=/home/user

# Install system dependencies required by Buildozer / python-for-android
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    openjdk-17-jdk \
    git zip unzip wget curl \
    autoconf automake libtool pkg-config \
    zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo6 \
    cmake libffi-dev libssl-dev \
    build-essential ccache \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create the 'user' account (the action's entrypoint expects it)
RUN useradd -m -s /bin/bash user && \
    echo "user ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/user

USER user
WORKDIR /home/user

# Install Buildozer (the action will overwrite this with the version you pin)
RUN pip3 install --user --upgrade buildozer

# The action will copy entrypoint.py and requirements.txt later
COPY --chown=user:user requirements.txt entrypoint.py /action/

ENTRYPOINT ["/action/entrypoint.py"]