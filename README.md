# ONOS+P4 Developer Tools

***

**DEPRECTAED** The content of this repository is deprecated. Starting with ONOS 1.12, official support for P4-enabled devices is available via P4Runtime. For more information please visit: https://wiki.onosproject.org/display/ONOS/P4+brigade#P4brigade-Learnmore

***

This repository maintains a set of tools and scripts to allow ONOS developers try the P4 experimental support.

For more information, visit: https://wiki.onosproject.org/x/lou

## Quickstart

**Important:** the following scripts have been tested on a [Mininet 2.2.1 VM with Ubuntu 14.04 64 bit](https://github.com/mininet/mininet/wiki/Mininet-VM-Images)

1. First of all you need to pull the git submodules for onos-bmv2 (ONOS fork of BMv2) and p4c-bmv2 (P4 compiler for BMv2):

		git submodule update --init --recursive

2. Follow the instructions inside the respective submodules to build and install onos-bmv2 and p4c-bmv2, or use the following command to do it in one shot (it might take a while to build everything):

		./build_all.sh

3. To make your development experience more pleasant, we suggest you to also include the following line in your .bash_profile:

		source /path/to/onos-p4-dev/tools/bash_profile
