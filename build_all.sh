#!/bin/sh

# Exit on errors
set -e

# Install p4c-bmv2
cd p4c-bmv2
sudo pip install -r requirements.txt
sudo python setup.py install

# Compile all p4 programs in p4src
cd ../p4src/
for f in *.p4; do
    sudo p4c-bmv2 --json build/${f%%.*}.json $f
done

# Build bmv2
cd ../onos-bmv2/
bash install_deps.sh
bash autogen.sh
./configure --enable-debugger
make

cd ../