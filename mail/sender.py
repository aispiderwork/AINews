"""邮件发送：通过 Resend API 批量发送摘要邮件。

设计约束：
- 零成本：使用 Resend 免费计划（3000 封/月）。
- 安全退出：本地未安装 resend / 未配置 API Key 时，打印提示并跳过，不报错中断 CI。
- 发件人：默认 Resend 试用域名 onboarding@resend.dev，配正式域名后改 RESEND_FROM。
"""
import os


def _get_resend():
    """惰性导入 resend，避免本地未安装时阻塞导入。"""
    try:
        import resend

        return resend
    except ImportError:
        return None


def load_subscribers_from_env() -> list:
    """从 Secret SUBSCRIBER_EMAILS（逗号分隔）读取收件人列表。"""
    raw = os.environ.get("SUBSCRIBER_EMAILS", "").strip()
    if not raw:
        return []
    return [e.strip() for e in raw.split(",") if e.strip()]


def load_subscribers_from_json(path: str) -> list:
    """从本地 data/subscribers.json 读取 active 状态的邮箱（本地调试用）。"""
    import json

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    result = []
    for s in data.get("subscribers", []):
        if s.get("status") == "active" and s.get("email"):
            result.append(s["email"].strip())
    return result


def collect_subscribers(json_path: str = "data/subscribers.json") -> list:
    """合并 Secret 与本地 JSON 的收件人，去重。Secret 优先。"""
    emails = load_subscribers_from_env()
    emails += load_subscribers_from_json(json_path)
    # 去重保序
    seen = set()
    unique = []
    for e in emails:
        if e.lower() not in seen:
            seen.add(e.lower())
            unique.append(e)
    return unique


def send_digest(html: str, subject: str, subscribers: list) -> bool:
    """发送邮件。返回是否成功发送至少一封。"""
    resend = _get_resend()
    if resend is None:
        print("[sender] 未安装 resend SDK，跳过发送（本地调试可 pip install resend）")
        return False

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("[sender] 缺少 RESEND_API_KEY，跳过发送")
        return False

    if not subscribers:
        print("[sender] 无有效订阅者，跳过发送")
        return False

    resend.api_key = api_key
    from_addr = os.environ.get("RESEND_FROM", "AINews <onboarding@resend.dev>")

    ok = 0
    for email in subscribers:
        try:
            resend.Emails.send(
                {
                    "from": from_addr,
                    "to": [email],
                    "subject": subject,
                    "html": html,
                }
            )
            ok += 1
            print(f"[sender] 已发送 -> {email}")
        except Exception as e:  # Resend 单封失败不应中断整批
            print(f"[sender] 发送失败 {email}: {e}")

    print(f"[sender] 完成：成功 {ok}/{len(subscribers)}")
    return ok > 0
