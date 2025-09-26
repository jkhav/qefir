#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <number_of_evos>"
    exit 1
fi

for i in $(seq 1 $1); do
    source ../.ddsim/bin/activate && python3 rus.py
done