#!/bin/bash
# usage: shot.sh out.png "query" [w h]
W=${3:-800}; H=${4:-600}
"/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --use-angle=swiftshader --enable-unsafe-swiftshader --hide-scrollbars --window-size=$W,$H --virtual-time-budget=6000 --screenshot="$1" "http://localhost:8765/index.html?$2" >/dev/null 2>&1
