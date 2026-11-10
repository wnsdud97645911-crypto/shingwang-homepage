import json
import re
import html
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

RSS_URL = "https://rss.blog.naver.com/shin_gwang_.xml"
IMAGE_DIR = Path("images")
IMAGE_DIR.mkdir(exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}
MAX_IMAGE_SIZE = 8 * 1024 * 1024

def get_image_url(description):
    content = html.unescape(description or "")
    matches = re.findall(
        r'<img\b[^>]*>', content, re.I
    )
    for tag in matches:
        for attr in ("src", "data-src"):
            match = re.search(
                rf'\b{attr}\s*=\s*["\']([^"\']+)["\']',
                tag, re.I
            )
            if match:
                url = html.unescape(match.group(1))
                if url.startswith("//"):
                    url = "https:" + url
                if url.startswith("https://"):
                    return url
    return None

def download_image(url, filename):
    try:
        request = urllib.request.Request(
            url, headers=HEADERS
        )
        with urllib.request.urlopen(
            request, timeout=20
        ) as response:
            content_type = response.headers.get(
                "Content-Type", ""
            ).lower().split(";")[0]
            extensions = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp",
                "image/gif": ".gif"
            }
            ext = extensions.get(content_type)
            if not ext:
                return None

            data = response.read(MAX_IMAGE_SIZE + 1)
            if len(data) > MAX_IMAGE_SIZE:
                return None

        path = IMAGE_DIR / (filename + ext)
        path.write_bytes(data)
        return str(path)
    except Exception as error:
        print("사진 다운로드 실패:", error)
        return None

request = urllib.request.Request(
    RSS_URL, headers=HEADERS
)
with urllib.request.urlopen(
    request, timeout=30
) as response:
    root = ET.fromstring(response.read())

posts = []
for index, item in enumerate(
    root.findall("./channel/item")[:50]
):
    title = item.findtext("title", "").strip()
    link = item.findtext("link", "").strip()
    date = item.findtext("pubDate", "").strip()
    description = item.findtext(
        "description", ""
    )

    if not title or not link.startswith("https://"):
        continue

    image_url = get_image_url(description)
    image_path = None

    if image_url:
        image_path = download_image(
            image_url, f"post_{index + 1}"
        )

    posts.append({
        "title": title,
        "link": link,
        "date": date,
        "image": image_path
    })
# 시공 분야별 최신 블로그 글 자동 분류
categories = {
    "asteiji": ["아스테이지", "아스테이지천막", "투명천막", "투명 천막"],
    "urethane": ["우레탄", "우레탄천막", "우레탄 천막"]
}

latest_by_category = {}

for post in posts:
    title_text = post["title"].replace(" ", "").lower()

    for category, keywords in categories.items():
        if category in latest_by_category:
            continue

        if any(keyword.replace(" ", "").lower() in title_text for keyword in keywords):
            latest_by_category[category] = post["link"]

Path("category_links.json").write_text(
    json.dumps(latest_by_category, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

if not posts:
    raise RuntimeError("RSS 게시글이 없습니다.")

Path("posts.json").write_text(
    json.dumps(posts, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
print(f"게시글 {len(posts)}개 저장 완료")
print(f"사진 {sum(bool(p['image']) for p in posts)}개 저장 완료")
