#!/usr/bin/env python3
"""AI关键词过滤工具"""

from typing import List, Dict

AI_KEYWORDS = [
    'ai', '人工智能', 'llm', 'gpt', 'claude', 'openai', 'anthropic',
    'google ai', 'deepmind', 'machine learning', '机器学习',
    'deep learning', '深度学习', 'neural network', '神经网络',
    'transformer', 'bert', 'llama', 'mistral', 'agent', '智能体',
    'copilot', '大模型', 'foundation model', '基础模型',
    'agi', 'artificial general intelligence',
    'computer vision', '计算机视觉', 'nlp', 'natural language processing',
    '自然语言处理', 'rag', 'retrieval augmented generation',
    'fine-tuning', '微调', 'prompt', '提示词',
    '多模态', 'multimodal', '具身智能', 'embodied ai',
    'robotics', '机器人', '自动驾驶', 'autonomous',
    'gemini', 'palm', 'bard', 'midjourney', 'stable diffusion', 'dall-e',
    'ai安全', 'ai safety', 'ai监管', 'ai regulation',
    'chatbot', 'generative ai', '生成式ai', 'coding', '代码生成',
]


def is_ai_related(title: str, summary: str = '') -> bool:
    """判断是否为AI相关新闻"""
    text = (title + ' ' + summary).lower()
    return any(keyword.lower() in text for keyword in AI_KEYWORDS)


def filter_ai_news(articles: List[Dict]) -> List[Dict]:
    """过滤出AI相关新闻"""
    return [
        article for article in articles
        if is_ai_related(
            article.get('title', ''),
            article.get('summary', '')
        )
    ]
