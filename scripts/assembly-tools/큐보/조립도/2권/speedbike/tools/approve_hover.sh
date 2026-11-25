# NOTE: the screenshots (jpg files below) are per-PC local files from a Claude session's tool-results
# folder; they do not exist on other PCs. Retake them and set T to the folder holding them before re-running.
cd "$(dirname "$0")/../../../../.."   # -> scripts/assembly-tools
T="${T:-$HOME/screenshots}"
export PYTHONIOENCODING=utf-8
ap() { echo "=== $1"; python supervise.py approve speedbike "$1" "$T/$2" "$3" 2>&1 | tail -4; }
ap 5 mcp-Claude_Browser-blob-1795572763872-rnr8mc.jpg "책 5와 같음: 축 2개가 아래(카메라 쪽)에서 215프레임 칸9·칸2로 올라오고, 빨간 부시 2개가 반대쪽 프레임 바로 위(부시 높이 정도)에 떠 있음. 띄움 160→25.5"
ap 6 mcp-Claude_Browser-blob-1795572775251-muxdfs.jpg "책 6과 같음: 스프라켓 2개가 두 축 끝 바로 앞에 떠 있고 화살표가 축 끝으로 들어감, 넓은 톱니 쪽 바깥. 띄움 158→74.5"
ap 7 mcp-Claude_Browser-blob-1795572781041-d0mlpo.jpg "책 7과 같음: 흰 19프레임이 스프라켓 앞 축 끝에 떠 있고 빨간 부시 2개가 그 바깥에 떠 있음(축→19프레임→부시 순서). 19프레임 76→47.5, 부시 91→62.5"
ap 28 mcp-Claude_Browser-blob-1795572787889-fc5q0n.jpg "책 28과 같음(리벳 규칙 적용): 2벌 모두 리벳이 2열브라켓 벽 아래 구멍과 1열브라켓 사이에 따로 떠 있음(결합 전), 8볼트는 벽 안쪽, 너트는 1열브라켓 바깥"
ap 35 mcp-Claude_Browser-blob-1795572795224-6pf35y.jpg "책 35와 같음: 가까운 쪽 모터 축 끝 바로 앞에 중간바퀴(무늬 면 바깥) 1개, 그 바깥에 빨간 부시 1개, 화살표가 축 끝으로. 바퀴 107→57.5, 부시 149→99.5"
ap 37 mcp-Claude_Browser-blob-1795572809588-xvnltj.jpg "책 37과 같음: 반대쪽 모터 축 끝 바로 앞에 중간바퀴 1개, 그 바깥에 빨간 부시 1개. 축 4/4, 부시 10/10. 바퀴 107→57.5, 부시 149→99.5"
echo "=== rulecheck"; python rulecheck.py speedbike 2>&1 | grep -E "합계|❌" | head -12
