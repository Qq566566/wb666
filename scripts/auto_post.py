import os
import random
import datetime
from openai import OpenAI

# 获取 API Key
api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("未找到 DEEPSEEK_API_KEY 环境变量，请检查 GitHub Secrets 配置！")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# 专注于大健康、抗衰、睡眠与科学养生的双语 SEO 主题库
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

def generate_article():
    topic_pair = random.choice(TOPICS)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
你是一位顶级的健康医学科普作家与抗衰老研究学者。
请围绕主题《{topic_pair['cn']}》/ "{topic_pair['en']}" 撰写一篇深度、客观且通俗易懂的 Markdown 健康研究博客文章。

要求如下：
1. 顶部必须包含 Front Matter 元数据，标题与摘要需体现中英双语，格式严格如下：
---
title: "{topic_pair['cn']} | {topic_pair['en']}"
description: "【中文摘要】100字左右的深度内容概述。【English Summary】A brief 1-2 sentence overview."
pubDate: "{today}"
---

2. 正文结构要求：
- 使用标准的 Markdown 格式（##, ### 标题，列表，加粗等）
- 内容采用中英对照或段落双语形式（每个小标题和核心观点均有中文与英文对照翻译）
- 结构清晰：引言（科学原理） -> 核心机制分析 -> 可落地的日常实操建议 -> 总结
- 语气严谨、专业、富有启发性，总字数在 1500 - 2000 字之间。
- 切勿出现“AI生成”、“智能体编写”、“大模型”等任何机器生成痕迹，直接返回纯粹的博客文章。
- 不要输出额外的解释性文字，直接返回 Front Matter + Markdown 正文。
"""

    print(f"正在撰写双语健康研究文章: {topic_pair['cn']} ...")
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    
    content = response.choices[0].message.content.strip()
    
    # 清理多余的代码块标记
    if content.startswith("```markdown"):
        content = content[11:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    # 创建保存目录与文件名
    filename = f"{today}-{random.randint(1000, 9999)}.md"
    target_dir = os.path.join("src", "content", "blog")
    os.makedirs(target_dir, exist_ok=True)
    
    file_path = os.path.join(target_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"成功保存文章至: {file_path}")

if __name__ == "__main__":
    generate_article()
