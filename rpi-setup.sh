#!/bin/bash

# install the Python prerequisites
sudo apt update
sudo apt install python3-venv libssl-dev -y

# install the rpi-smartgadget package in a virtual environment in the home directory
cd ~
python3 -m venv shtenv
source shtenv/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools
pip install https://github.com/MSLNZ/rpi-smartgadget/archive/master.tar.gz
deactivate
