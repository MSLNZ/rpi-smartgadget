#!/bin/bash

# install the prerequisites
sudo apt-get install -y python3-dev python3-venv libssl-dev libffi-dev build-essential libglib2.0-dev

# install the rpi-smartgadget package in a virtual environment named 'shtenv'
# which is located in the home directory. If you change the name of the
# virtual environment then you must also change the value of RPI_EXE_PATH
# in smartgadget/__init__.py
cd ~
python3 -m venv shtenv
source shtenv/bin/activate
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel
cd rpi-smartgadget
python -m pip install .
chmod +x examples/*.py
deactivate
