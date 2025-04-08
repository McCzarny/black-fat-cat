#!/bin/bash -e

apt-get update

apt-get install -y git wget curl unzip tmux ninja-build vim

apt install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y python3.12 python3.12-venv
apt-get install -y python3-setuptools python3-dev build-essential
pip3 install --upgrade pip setuptools


curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
chmod +x Miniforge3-$(uname)-$(uname -m).sh
bash Miniforge3-$(uname)-$(uname -m).sh -b -p ~/miniforge3
micromamba activate ~/miniforge3