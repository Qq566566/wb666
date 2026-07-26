import os
import random
import datetime
import re
from openai import OpenAI

api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("未找到 DEEPSEEK_API_KEY 环境变量！")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

TOPICS = [
    {
        "cn": "昼夜节律与深度睡眠：如何通过光照调节提升身体自我修复力",
        "en": "Circadian Rhythms & Deep Sleep: How Light Exposure Boosts Cellular Repair"
    },
    {
        "cn": "抗炎饮食指南：降低体内慢性炎症的 7 种核心食物策略",
        "en": "Anti-Inflammatory Nutrition: 7 Core Food Strategies to Reduce Systemic Inflammation"
    },
    {
        "cn": "间歇性断食与细胞自噬：延缓衰老与改善代谢的科学真相",
        "en": "Intermittent Fasting & Autophagy: The Science Behind Anti-Aging and Metabolic Health"
    },
    {
        "cn": "办公族隐性疲劳解法：如何通过微运动快速恢复大脑精力",
        "en": "Combating Brain Fog: Micro-Movement Strategies for Office Professionals"
    },
    {
        "cn": "肠道微生态与情绪管理：肠脑轴如何影响日常焦虑",
        "en": "The Gut-Brain Axis: How Microbiome Health Influences Daily Anxiety & Mood"
    },
    {
        "cn": "现代人如何科学补镁：改善睡眠与缓解肌肉紧张的完整指南",
        "en": "Magnesium Supplementation Guide: Improving Sleep Quality & Muscle Recovery"
    }
]

def clean_yaml_frontmatter(title_cn, title_en, desc_cn, desc_en, today):
    """强制生成绝对符合规范的 YAML Front Matter，防止语法报错"""
    # 清理双引号与多余空格
    clean_title = f"{title_cn} | {title_en}".replace('"', "'").strip()
    clean_desc = f"【中文摘要】{desc_cn}【English Summary】{desc_en}".replace('"', "'").replace('\n', ' ').strip()
    
    yaml_header = f"""---
title: "{clean_title}"
description: "{clean_desc}"
pubDate: "{today}"
---"""
    return yaml_header

def generate_article():
    topic_pair = random.choice(TOPICS)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
你是一位顶级的健康医学科普作家与抗衰老研究学者。
请围绕主题《{topic_pair['cn']}》/ "{topic_pair['en']}" 撰写一篇深度、客观且通俗易懂的 Markdown 健康研究博客文章。

正文结构要求：
1. 请勿输出 Front Matter (---)，直接从正文一级标题开始写。
2. 使用标准的 Markdown 格式（##, ### 标题，列表，加粗等）
3. 内容采用中英对照或段落双语形式（每个小标题和核心观点均有中文与英文对照翻译）
4. 结构清晰：引言 -> 核心机制分析 -> 可落地的日常实操建议 -> 总结
5. 语气严谨专业，总字数在 1500 - 2000 字之间，切勿出现“AI生成”、“智能体”等痕迹。
"""

    print(f"正在撰写双语健康研究文章: {topic_pair['cn']} ...")
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    
    body_content = response.choices[0].message.content.strip()
    
    # 清理代码块标记
    if body_content.startswith("```markdown"):
        body_content = body_content[11:]
    if body_content.startswith("```"):
        body_content = body_content[3:]
    if body_content.endswith("```"):
        body_content = body_content[:-3]
    body_content = body_content.strip()

    # 简易摘要生成
    desc_cn = "深入剖析健康机制与前沿科学，提供切实可行的日常改善策略。"
    desc_en = "Exploring health mechanics and cutting-edge science, providing actionable lifestyle strategies."

    # 拼装安全的 YAML 头
    yaml_header = clean_yaml_frontmatter(topic_pair['cn'], topic_pair['en'], desc_cn, desc_en, today)
    final_content = f"{yaml_header}\n\n{body_content}"

    # 保存文件
    filename = f"{today}-{random.randint(1000, 9999)}.md"
    target_dir = os.path.join("src", "content", "blog")
    os.makedirs(target_dir, exist_ok=True)
    
    file_path = os.path.join(target_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    print(f"成功保存文章至: {file_path}")

if __name__ == "__main__":
    generate_article()
