#!/bin/bash
bash eleven-labs-tts.sh "$1" && mpg123 -q output.mp3 &
wait %1
rm output.mp3
