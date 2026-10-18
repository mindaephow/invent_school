#!/bin/bash
# 사용: ./_variant.sh ARM INNER SGN COL RF  → 빌드 후 겹침 줄 수 출력
cd "$(dirname "$0")"
B32ARM=$1 B32IN=$2 B32SGN=$3 B32COL=$4 B32RF=$5 PYTHONIOENCODING=utf-8 python build.py battlerobot2 --write >/dev/null 2>&1
B32ARM=$1 B32IN=$2 B32SGN=$3 B32COL=$4 B32RF=$5 PYTHONIOENCODING=utf-8 python build.py battlerobot2 2>&1 | grep -E "^  겹침" | cut -c1-70
