#!/bin/bash
# Usage source activate_env.sh

git pull
git submodule update --remote
cd SliQSim && make && cd ..
source .venv/bin/activate