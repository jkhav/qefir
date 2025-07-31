#!/bin/bash

git pull
git submodule update --remote
cd SliQSim && make && cd ..
source .venv/bin/activate