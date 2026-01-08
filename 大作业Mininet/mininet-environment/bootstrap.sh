#!/bin/bash

set -e

QTR=22sp
MININET_VERSION="stable-2.3.0"
# No upstream tags, so pinning to a specific commit on gar-experimental that
# supports python3 and appears stable since 2020.
POX_VERSION="5f82461e01f8822bd7336603b361bff4ffbd2380"

sudo apt-get update
sudo apt-get install -y python3 unzip net-tools
git clone --depth 1 https://gitlab.cs.washington.edu/561p-course-staff/mininet.git -b stable-2.3.0
(cd mininet && git checkout $MININET_VERSION)
#mininet/util/install.sh -nfvp
#(cd pox && git checkout $POX_VERSION)
git clone https://gitlab.cs.washington.edu/561p-course-staff/project-1-starter project-1
git clone https://gitlab.cs.washington.edu/561p-course-staff/project-2-starter project-2
#ln -s ~/project-1/pox/* ~/pox/pox/misc/
