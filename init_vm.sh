#!/bin/bash
GIT_REPO=https://github.com/minkj1992/jarvis.git
DIR_NAME=jarvis

# Uninstall old versions
sudo yum remove docker \
                  docker-client \
                  docker-client-latest \
                  docker-common \
                  docker-latest \
                  docker-latest-logrotate \
                  docker-logrotate \
                  docker-engine

# Install docker using the rpm repository
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl start docker
sudo usermod -aG docker ${USER}
sudo systemctl restart docker

# gcc make gcc-c++
sudo yum install gcc make gcc-c++ git -y

# Initialize git
git config --global user.name 'minkj1992'
git config --global user.email minkj1992@gmail.com

# Clone git repository
git clone $GIT_REPO
cd $DIR_NAME

echo 'Before run lets-encrypt set domain to ip and domain server name'
chmod +x ./init-letsencrypt.sh
