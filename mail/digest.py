"""邮件摘要渲染：读取 news.json -> 生成内联 CSS 的 HTML 邮件正文。

参考 RadarAI 每日速报样式：深色头栏 + 左蓝竖线 + 今日速览列表 + CTA 按钮。
"""
import os
from datetime import datetime, timezone

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")

# 线上站点地址（GitHub Pages）。可经环境变量 SITE_URL 覆盖。
SITE_URL = os.environ.get("SITE_URL", "https://YOUR_GITHUB_USERNAME.github.io/AINews/")

# 头版取前 N 条（参考截图约 8~10 条）
TOP_N = int(os.environ.get("DIGEST_TOP_N", "10"))

# 平台英文 key -> 中文展示名
PLATFORM_LABELS = {
    "qbitai": "量子位",
    "hackernews": "Hacker News",
    "huggingface": "HuggingFace",
    "bestblogs": "BestBlogs",
    "radarai": "RadarAI",
    "unknown": "未知",
}


def _load_template() -> str:
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def format_date(iso_str: str) -> str:
    """'2026-08-13T04:20:17+00:00' -> '2026年08月13日'"""
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return f"{dt.year}年{dt.month:02d}月{dt.day:02d}日"
    except Exception:
        return ""


def _esc(text: str) -> str:
    """HTML 转义（邮件正文必须转义，避免标题里的 & < > 破坏结构）"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_article(a: dict) -> str:
    title = (a.get("title") or "无标题").strip()
    url = a.get("url") or a.get("platform_url") or "#"
    platform = a.get("platform", "unknown")
    label = PLATFORM_LABELS.get(platform, platform)

    # 跨源报道标识（来自 cluster.py 的 source_count）
    extra = ""
    sc = a.get("source_count", 1)
    if sc and sc > 1:
        extra = f' <span style="color:#2563eb;font-size:12px;">· 同时被{sc}个来源报道</span>'

    title_html = _esc(title)
    url_html = _esc(url)

    return (
        '<div style="margin-bottom:14px;padding-left:18px;position:relative;'
        'font-size:15px;line-height:1.6;color:#1f2937;">'
        '<span style="position:absolute;left:2px;color:#2563eb;font-weight:700;">•</span>'
        f'<a href="{url_html}" style="color:#1f2937;text-decoration:none;">{title_html}</a>'
        f'<span style="color:#9ca3af;font-size:12px;"> · {label}</span>{extra}'
        "</div>"
    )


def render_digest(news_json_path: str, top_n: int = TOP_N) -> str:
    import json

    with open(news_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles = (data.get("sorted_all") or [])[:top_n]
    date_str = format_date(data.get("update_time", ""))

    if articles:
        articles_html = "\n".join(render_article(a) for a in articles)
    else:
        articles_html = (
            '<div style="color:#9ca3af;font-size:14px;line-height:1.6;">'
            "今日暂无可汇总的内容，稍后再来看看～</div>"
        )

    unsubscribe_url = os.environ.get("UNSUBSCRIBE_URL", SITE_URL + "#unsubscribe")

    html = (
        _load_template()
        .replace("{{date}}", date_str)
        .replace("{{site_url}}", SITE_URL)
        .replace("{{unsubscribe_url}}", unsubscribe_url)
        .replace("{{articles}}", articles_html)
    )
    return html


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "data/news.json"
    print(render_digest(path))
