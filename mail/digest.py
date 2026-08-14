"""邮件摘要渲染：读取 news.json -> 生成内联 CSS 的 HTML 邮件正文。

配色：白底正文 + 羊皮纸黄(#eae2c8)头栏 + 报纸金(#8B6914)强调；
末尾纯文本链接（无 CTA 按钮）。
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
        extra = f' <span style="color:#8B6914;font-size:12px;font-weight:600;">· 同时被{sc}个来源报道</span>'

    title_html = _esc(title)
    url_html = _esc(url)

    # 用表格布局拉开「•」与文字的间距（约 2 个英文空格宽）
    return (
        '<table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:18px;">'
        '<tr>'
        f'<td width="24" valign="top" style="color:#8B6914;font-size:16px;'
        f'line-height:1.65;font-weight:700;">•</td>'
        '<td valign="top" style="font-size:15px;line-height:1.65;color:#2c2418;">'
        f'<a href="{url_html}" style="color:#2c2418;text-decoration:none;">{title_html}</a>'
        f'<span style="color:#9a8b70;font-size:12px;margin-left:6px;">· {label}</span>{extra}'
        '</td>'
        '</tr>'
        '</table>'
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

    # 来源暂不可用提示：被标记为抓取失败的平台，邮件顶部明确告知，而非静默缺内容
    unavailable = data.get("platform_unavailable") or []
    if unavailable:
        names = [_esc(PLATFORM_LABELS.get(p, p)) for p in unavailable]
        notice_html = (
            '<div style="margin-bottom:18px;padding:12px 16px;'
            'border-left:4px solid #c0392b;background-color:#fdf3f2;'
            'color:#a33;font-size:13px;line-height:1.6;">'
            '⚠️ 本期以下来源抓取失败，暂不可用：' + '、'.join(names) +
            '。邮件未含该来源内容。</div>'
        )
    else:
        notice_html = ""

    html = (
        _load_template()
        .replace("{{date}}", date_str)
        .replace("{{site_url}}", SITE_URL)
        .replace("{{unsubscribe_url}}", unsubscribe_url)
        .replace("{{unavailable_notice}}", notice_html)
        .replace("{{articles}}", articles_html)
    )
    return html


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "data/news.json"
    print(render_digest(path))
