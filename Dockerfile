RUN sudo apt-get update && \
    sudo apt-get install -y software-properties-common && \
    sudo rm -rf /var/lib/apt/lists/*

RUN sudo add-apt-repository ppa:openjdk-r/ppa   # ❌ DELETE THIS LINE
RUN sudo apt update
RUN sudo apt-get -y install openjdk-17-jdk