import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

RSS_URL = "https://rss.blog.naver.com/shin_gwang_.xml"

request = urllib.request.Request(
    RSS_URL,
    headers={"User-Agent": "Mozilla/5.0"}
)

with urllib.request.urlopen(request, timeout=30) as response:
    rss_data = response.read()

root = ET.fromstring(rss_data)
posts = []

for item in root.findall("./channel/item")[:10]:
    title = item.findtext("title", "").strip()
    link = item.findtext("link", "").strip()
    date = item.findtext("pubDate", "").strip()

    if title and link.startswith(("https://", "http://")):
        posts.append({
            "title": title,
            "link": link,
            "date": date
        })

if not posts:
    raise RuntimeError("RSS에서 게시글을 찾지 못했습니다.")

Path("posts.json").write_text(
    json.dumps(posts, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"블로그 게시글 {len(posts)}개 저장 완료!")
