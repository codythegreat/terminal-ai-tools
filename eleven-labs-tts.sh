#!/bin/bash

curl -X 'POST' \
  "https://api.elevenlabs.io/v1/text-to-speech/$CODY_VOICE_ID" \
  -H 'accept: */*' \
  -H "xi-api-key: $ELEVEN_LABS_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "'"$1"'"
}' \
  -s -o output.mp3
