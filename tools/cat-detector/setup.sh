#!/bin/bash -e

echo "The script contains just bunch of commands, it's not intended to be run as a script."
if true; then
    exit 0
fi

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

cd ~/repositories/black-fat-cat; python3 ./tools/cat-detector/src/gathercats.py

conda activate numpy-dev; cd ~/repositories/black-fat-cat; python3 ./tools/cat-detector/src/gathercats.py
conda activate numpy-dev; cd ~/repositories/black-fat-cat; python3 ./tools/cat-detector/src/main.py
conda activate numpy-dev; cd /home/odroid/repositories/black-fat-cat; python3 ./tools/cat-detector/src/main.py

fswebcam -r 640x480 --jpeg 85 -D 1 web-cam-shot.jpg