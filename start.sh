#!/bin/bash

sudo apt-get update && \
sudo apt-get install -y git python-pip python-dev python-virtualenv

git clone https://github.com/harsh376/frontend326.git
git clone https://github.com/harsh376/backend326.git

cd backend326
git pull

cd ../frontend326
rm -rf venv
git pull
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt

screen -d -m python run.py
echo 'App is running'
