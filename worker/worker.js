/**
 * AINews 订阅/退订 Worker（Cloudflare Workers）
 *
 * 职责：通过 GitHub Contents API 读写仓库内的 data/subscribers.json，
 *       支持 /subscribe 与 /unsubscribe 两个端点，返回 4 种 case 结果。
 *
 * 配置（部署前设置）：
 *   - wrangler secret put GH_TOKEN        # GitHub PAT，需 public_repo（公开仓库）或 repo 权限
 *   - wrangler.toml 的 [vars] 中设置 REPO / PATH
 *
 * 说明：GitHub Pages 是静态站，无后端；本 Worker 充当轻量 API，
 *       直接读写同一仓库的 subscribers.json（经 API 写入会绕过本地 .gitignore，
 *       文件在仓库中可见——公开仓库下邮箱会公开，详见部署说明的隐私提示）。
 */

// UTF-8 安全的 base64 编解码（Cloudflare Workers 全局有 atob/btoa/TextEncoder/TextDecoder）
function utf8ToBase64(str) {
  const bytes = new TextEncoder().encode(str);
  let bin = "";
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}
function base64ToUtf8(b64) {
  const bin = atob(b64.replace(/\s/g, ""));
  const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

// 允许跨域的来源（GitHub Pages + 本地调试预览）。命中才回具体 Origin，否则拒绝跨域。
const ALLOWED_ORIGINS = new Set([
  "https://aispiderwork.github.io",
  "http://127.0.0.1:5500",
  "http://localhost:5500",
  "http://127.0.0.1:49295",
  "http://localhost:49295",
]);

function corsHeaders(origin) {
  const allow = ALLOWED_ORIGINS.has(origin) ? origin : "null";
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    Vary: "Origin",
  };
}

function json(data, status, origin) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...corsHeaders(origin),
    },
  });
}

function validEmail(e) {
  return typeof e === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e.trim());
}

// 读取 data/subscribers.json（不存在则返回空列表）
async function getSubscribers(env) {
  const url = `https://api.github.com/repos/${env.REPO}/contents/${env.PATH}`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${env.GH_TOKEN}`,
      "User-Agent": "ainews-subscribe-worker",
      Accept: "application/vnd.github+json",
    },
  });
  if (res.status === 404) return { subscribers: [], sha: null };
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`GitHub GET ${res.status}: ${t.slice(0, 200)}`);
  }
  const j = await res.json();
  let subscribers = [];
  try {
    subscribers = JSON.parse(base64ToUtf8(j.content)).subscribers || [];
  } catch {
    subscribers = [];
  }
  return { subscribers, sha: j.sha };
}

// 写回 data/subscribers.json（有 sha 则更新，无则新建）
async function putSubscribers(env, subscribers, sha) {
  const body = {
    message: "chore(subscribe): update subscribers via worker",
    content: utf8ToBase64(
      JSON.stringify({ version: 1, subscribers }, null, 2)
    ),
  };
  if (sha) body.sha = sha;
  const res = await fetch(
    `https://api.github.com/repos/${env.REPO}/contents/${env.PATH}`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${env.GH_TOKEN}`,
        "User-Agent": "ainews-subscribe-worker",
        "Content-Type": "application/json",
        Accept: "application/vnd.github+json",
      },
      body: JSON.stringify(body),
    }
  );
  if (!res.ok) {
    const t = await res.text();
    throw new Error(`GitHub PUT ${res.status}: ${t.slice(0, 200)}`);
  }
  return res.json();
}

// 处理并发写冲突（409）：重新拉取最新 sha 后重试一次
async function withRetry(env, fn) {
  try {
    return await fn();
  } catch (e) {
    if (String(e.message).includes("409")) return await fn();
    throw e;
  }
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }
    if (request.method !== "POST") {
      return json({ ok: false, code: "method_not_allowed", message: "仅支持 POST" }, 405, origin);
    }

    let payload;
    try {
      payload = await request.json();
    } catch {
      return json({ ok: false, code: "invalid_json", message: "请求格式错误" }, 400, origin);
    }
    const email = (payload.email || "").trim().toLowerCase();
    if (!validEmail(email)) {
      return json({ ok: false, code: "invalid", message: "请输入有效的邮箱地址" }, 400, origin);
    }

    const action = new URL(request.url).pathname.replace(/\/+$/, "").split("/").pop();
    if (action !== "subscribe" && action !== "unsubscribe") {
      return json({ ok: false, code: "unknown_action", message: "未知操作" }, 404, origin);
    }

    try {
      const result = await withRetry(env, async () => {
        const { subscribers, sha } = await getSubscribers(env);
        const idx = subscribers.findIndex(
          (s) => (s.email || "").toLowerCase() === email
        );

        if (action === "subscribe") {
          if (idx >= 0 && subscribers[idx].status === "active") {
            return { code: "already_subscribed", message: "该邮箱已订阅，无需重复订阅" };
          }
          if (idx >= 0) {
            subscribers[idx].status = "active";
            subscribers[idx].subscribed_at = new Date().toISOString();
          } else {
            subscribers.push({
              email,
              subscribed_at: new Date().toISOString(),
              status: "active",
            });
          }
          await putSubscribers(env, subscribers, sha);
          return { code: "subscribed", message: `订阅成功！每日早报将发送至 ${email}` };
        }

        // unsubscribe
        if (idx < 0 || subscribers[idx].status !== "active") {
          return { code: "not_subscribed", message: "该邮箱尚未订阅，无需退订" };
        }
        subscribers[idx].status = "unsubscribed";
        subscribers[idx].unsubscribed_at = new Date().toISOString();
        await putSubscribers(env, subscribers, sha);
        return { code: "unsubscribed", message: `已退订，后续将不再向 ${email} 发送邮件` };
      });

      const ok = result.code === "subscribed" || result.code === "unsubscribed";
      return json(
        { ok, code: result.code, message: result.message },
        ok ? 200 : 409,
        origin
      );
    } catch (e) {
      return json(
        { ok: false, code: "error", message: `服务暂时不可用：${e.message}` },
        500,
        origin
      );
    }
  },
};
