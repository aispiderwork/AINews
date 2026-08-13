"""邮件发送入口：串联 digest 渲染 + sender 发送。

用法：
  python -m mail.send_digest            # 读默认 data/news.json + data/subscribers.json
  NEWS_JSON=... SUBSCRIBER_EMAILS=... python -m mail.send_digest

触发策略：由 crawl-news.yml 的 send-digest job 在早班（UTC 01:00）调用。
"""
import os
import sys
import json

# 允许以脚本方式直接运行（python mail/send_digest.py）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mail.digest import render_digest, format_date  # noqa: E402
from mail.sender import collect_subscribers, send_digest  # noqa: E402


def main():
    news_path = os.environ.get("NEWS_JSON", "data/news.json")
    sub_json = os.environ.get("SUBSCRIBERS_JSON", "data/subscribers.json")

    if not os.path.exists(news_path):
        print(f"[send] 找不到数据文件 {news_path}，退出")
        sys.exit(1)

    html = render_digest(news_path)

    with open(news_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    date_str = format_date(data.get("update_time", ""))
    subject = f"AINews 每日速报 · {date_str}"

    subscribers = collect_subscribers(sub_json)
    if not subscribers:
        print("[send] 无订阅者（Secret SUBSCRIBER_EMAILS 与本地 subscribers.json 均无），跳过")
        return

    print(f"[send] 收件人 {len(subscribers)} 位，主题：{subject}")
    send_digest(html, subject, subscribers)


if __name__ == "__main__":
    main()
