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


def _decrypt_email(cipher_b64: str) -> str | None:
    """用 EMAIL_KEY 解密 Worker 写入的 e 字段（AES-256-GCM，base64(iv+ct+tag)）。

    与 worker/worker.js 的加密严格对应：密钥为 32 字节（base64），
    iv 12 字节在前，认证 tag 16 字节在尾部。无 EMAIL_KEY 时返回 None。
    """
    import base64

    key_b64 = os.environ.get("EMAIL_KEY", "").strip()
    if not key_b64 or not cipher_b64:
        return None
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

        key = base64.b64decode(key_b64)
        raw = base64.b64decode(cipher_b64)
        iv = raw[:12]
        tag = raw[-16:]
        ct = raw[12:-16]
        decryptor = Cipher(algorithms.AES(key), modes.GCM(iv, tag)).decryptor()
        return decryptor.update(ct).decode("utf-8").strip()
    except Exception as e:  # 解密失败（密钥不匹配/数据损坏）不应中断整批
        print(f"[sender] 解密订阅邮箱失败：{e}")
        return None


def load_subscribers_from_json(path: str) -> list:
    """从 data/subscribers.json 读取 active 状态的邮箱。

    兼容两种存储：
    - 新格式：e 字段为密文，用 EMAIL_KEY 解密（推荐，公开仓库不暴露明文）
    - 旧格式：email 字段为明文（本地调试 / 历史数据）
    """
    import json

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    result = []
    active_total = 0
    for s in data.get("subscribers", []):
        if s.get("status") != "active":
            continue
        active_total += 1
        email = None
        if s.get("e"):
            email = _decrypt_email(s["e"])
        elif s.get("email"):
            email = s["email"].strip()  # 旧明文格式兼容
        if email:
            result.append(email)
    # 防御性告警：有 active 订阅却全部解密失败 → 多为 EMAIL_KEY 不匹配/缺失，
    # 此时系统会"静默"跳过发送，订阅者永远收不到邮件。显式报警便于在 Actions 日志发现。
    if active_total > 0 and len(result) == 0:
        print(
            "[sender] ⚠️ 严重：subscribers.json 有 %d 个 active 订阅，但解密出 0 个有效邮箱。"
            "通常是 GitHub Actions 的 EMAIL_KEY 与 Cloudflare Worker 的 EMAIL_KEY 不一致或缺失导致。"
            % active_total
        )
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
                    # 关闭打开/点击追踪，避免链接被包成 awstrack.me 重定向（国内网络不可达）
                    # 使用 Resend v2 规范的 track 对象
                    "track": {
                        "opens": False,
                        "links": "none",
                        "messages": False,
                    },
                }
            )
            ok += 1
            print(f"[sender] 已发送 -> {email}")
        except Exception as e:  # Resend 单封失败不应中断整批
            print(f"[sender] 发送失败 {email}: {e}")

    print(f"[sender] 完成：成功 {ok}/{len(subscribers)}")
    return ok > 0
