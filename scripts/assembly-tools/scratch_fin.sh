#!/bin/bash
# usage: scratch_fin.sh N screenshot_file "비교 문구" "다음 번호 비교 문구"
cd /c/Users/user/Downloads/invent_school/scripts/assembly-tools; export PYTHONIOENCODING=utf-8
T="C:/Users/user/.claude/projects/C--Users-user-Downloads/eeb975a4-7471-4c93-899b-052704acd340/tool-results"
python record_check.py bowling $1 "$T/$2" "$3" 2>&1 | tail -2
python verify_step.py bowling $1 2>&1 | grep "✅\|⚠\|❌" | cut -c1-160
python rulecheck.py bowling $1 2>&1 | tail -2
python track.py bowling $1 --views 앞,뒤,좌,우,위,아래 --next "$4" 2>&1 | tail -1
git checkout -- trailer_links.json 2>/dev/null
