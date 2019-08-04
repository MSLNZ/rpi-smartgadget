#!/bin/bash

# install the prerequisites
sudo apt install python3-venv libssl-dev libffi-dev build-essential libglib2.0-dev -y

# install the rpi-smartgadget package in a virtual environment named 'shtenv'
# which is located in the home directory. If you change the name of the
# virtual environment then you must also change the value of RPI_EXE_PATH
# in smartgadget/__init__.py
cd ~
python3 -m venv shtenv
source shtenv/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools
pip install https://github.com/MSLNZ/rpi-smartgadget/archive/master.tar.gz
deactivate
