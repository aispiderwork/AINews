#!/usr/bin/env python3
"""跨平台事件聚类 - 把不同来源报到同一事件的文章归并为一个条目。

设计取舍（对应 docs/项目概要.md 的 P1 内容提质）：
- 用「标题归一化 + 字符 bigram Jaccard 相似度」做启发式归并，零额外成本、零密钥。
- 不引入合成热度分；归并后由 main.py 用「被 N 个来源报道」作为事件重要性的
  真实代理信号来排序（跨源报道越多 = 越值得上头版），比纯时间序更贴近用户价值。
"""

import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

# 相似度阈值：字符 bigram Jaccard >= 该值视为同一事件。
# 0.6 较保守，避免把不同事件错误合并；同一事件被改写标题/换平台报道时通常仍高于此值。
SIMILARITY_THRESHOLD = 0.6

# also_covered_by 仅保留这些字段，避免把整篇大对象塞进聚类条目。
_ALSO_FIELDS = ('platform', 'title', 'url', 'platform_url')


def _normalize_title(title: Optional[str]) -> str:
    """小写、去标点/空白，保留中英文字母数字，用于与语言无关的归一化比对。"""
    if not title:
        return ''
    t = (title or '').lower()
    # 保留 CJK、字母、数字，其余替换为空格
    t = re.sub(r'[^\w\u4e00-\u9fff]+', ' ', t, flags=re.UNICODE)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def _char_bigrams(s: str) -> set:
    if len(s) <= 1:
        return {s}
    padded = ' ' + s + ' '
    return {padded[i:i + 2] for i in range(len(padded) - 1)}


def _title_similarity(a: str, b: str) -> float:
    na, nb = _normalize_title(a), _normalize_title(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ga, gb = _char_bigrams(na), _char_bigrams(nb)
    if not ga or not gb:
        return 0.0
    inter = len(ga & gb)
    union = len(ga | gb)
    return inter / union if union else 0.0


def _to_epoch(publish_time: Optional[str]) -> float:
    """publish_time -> epoch 秒；解析失败返回 0（排最后）。"""
    if not publish_time:
        return 0.0
    try:
        t = publish_time.replace('Z', '+00:00')
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return 0.0


def _pick_primary(articles: List[Dict]) -> Dict:
    """在聚类成员中选最优代表：优先有封面、其次有摘要、最后最新发布。"""
    return sorted(
        articles,
        key=lambda a: (
            0 if a.get('cover_url') else 1,
            0 if a.get('summary') else 1,
            _to_epoch(a.get('publish_time')) or 0,
        ),
        reverse=True,
    )[0]


def cluster_articles(articles: List[Dict]) -> List[Dict]:
    """把不同平台报到同一事件的文章归并。

    Args:
        articles: 全局文章列表（来自各平台合并、去重后的扁平列表）。

    Returns:
        去重后的文章列表；被合并的条目会带上：
          - source_count:     聚类成员数（被多少来源报道）
          - also_covered_by:  其余来源的精简引用列表
        单条不成簇的文章保持原样（不含上面两个字段）。
    """
    if not articles:
        return []

    clusters: List[List[Dict]] = []
    for art in articles:
        placed = False
        for cluster in clusters:
            rep = cluster[0]
            # 仅跨平台合并：同平台条目已在 merge 阶段按 URL/resource_id 去重，
            # 这里再按标题相似度合并同平台条目，易把不同文章误并
            # （如 HuggingFace 两个名称相似的模型）。
            # 同时限制「每平台每簇至多一条」，避免把同一来源的两条相似报道并到一起。
            if rep.get('platform') == art.get('platform'):
                continue
            if any(c.get('platform') == art.get('platform') for c in cluster):
                continue
            if _title_similarity(art.get('title', ''), rep.get('title', '')) >= SIMILARITY_THRESHOLD:
                cluster.append(art)
                placed = True
                break
        if not placed:
            clusters.append([art])

    result: List[Dict] = []
    for cluster in clusters:
        if len(cluster) == 1:
            result.append(cluster[0])
            continue

        primary = _pick_primary(cluster)
        also = [
            {k: a.get(k) for k in _ALSO_FIELDS if a.get(k) is not None}
            for a in cluster
            if a is not primary
        ]

        merged = dict(primary)  # 拷贝，避免污染原始对象
        merged['source_count'] = len(cluster)
        merged['also_covered_by'] = also
        result.append(merged)

    return result
