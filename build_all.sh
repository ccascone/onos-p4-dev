#!/bin/sh
set -e
cd p4c-bmv2
sudo pip install -r requirements.txt
sudo python setup.py install
cd ../onos-bmv2/
bash install_deps.sh
bash autogen.sh
./configure --enable-debugger
make
cd ../