#!/bin/bash

arecord -d 10 -f cd output.wav

whisper --model tiny.en --output_format txt output.wav

cat output.wav.txt | tr '\n' ' ' | sed "s/'//g" | xargs -I {} ./gpt.py {}
