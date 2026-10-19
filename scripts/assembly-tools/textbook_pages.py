# 교재 PDF 원본에서 쪽 이미지를 뽑아 저장소에 올린다 (MCP 의 get_textbook_page 가 꺼내 보는 파일).
#   python textbook_pages.py upload "<PDF 경로>" <권> [첫쪽 끝쪽]      예: python textbook_pages.py upload "C:/.../2020년 큐보 1단계(배포용).pdf" 1 60 75
#   환경변수 IVS_MCP_URL = 발명학교 MCP 주소(키 포함, 예: https://invent-school-sigma.vercel.app/api/mcp?key=...)
# 서버에 올라가 있는 교재 PDF 는 원본의 절반 해상도라 작은 구멍을 세기 어려워서, 원본(쪽 사진 2524×3531)에서 직접 뽑는다.
# 쪽마다 원본 해상도 JPEG(hi)와 가로 절반짜리(small)를 올린다. 이미 올라가 있어도 덮어쓴다.
import sys, os, json, base64, urllib.request
try:
    import pymupdf
except ImportError:
    import fitz as pymupdf  # 예전 이름

TARGET_W = 2524  # 원본 쪽 사진의 가로 픽셀

def render(page, width_px, quality):
    zoom = width_px / page.rect.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
    return pix.tobytes("jpeg", jpg_quality=quality)

def call(url, name, args):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
    raw = urllib.request.urlopen(req, timeout=120).read().decode("utf-8")
    line = [l[6:] for l in raw.splitlines() if l.startswith("data: ")][0]
    r = json.loads(line).get("result", {})
    text = "\n".join(c.get("text", "") for c in r.get("content", []))
    if r.get("isError"):
        raise RuntimeError(text)
    return text

def main():
    if len(sys.argv) < 4 or sys.argv[1] != "upload":
        print(__doc__); sys.exit(1)
    pdf, volume = sys.argv[2], int(sys.argv[3])
    url = os.environ.get("IVS_MCP_URL")
    if not url:
        print("환경변수 IVS_MCP_URL 이 없어요(MCP 주소, 키 포함)."); sys.exit(1)
    doc = pymupdf.open(pdf)
    first = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    last = int(sys.argv[5]) if len(sys.argv) > 5 else len(doc)
    ok = 0
    for n in range(first, last + 1):
        page = doc[n - 1]
        hi = render(page, TARGET_W, 78)
        small = render(page, TARGET_W // 2, 80)
        try:
            call(url, "upload_textbook_page", {"volume": volume, "page": n, "hi": base64.b64encode(hi).decode(), "small": base64.b64encode(small).decode()})
            ok += 1
            print(f"{volume}권 {n}쪽 올림 (hi {len(hi)//1024}KB / small {len(small)//1024}KB)", flush=True)
        except Exception as e:
            print(f"{volume}권 {n}쪽 실패: {e}", flush=True)
    print(f"끝: {ok}/{last - first + 1}쪽")

if __name__ == "__main__":
    main()
