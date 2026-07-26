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
    clean_title = f"{title_cn} | {title_en}".replace('"', "'").strip()
    clean_desc = f"【中文摘要】{desc_cn}【English Summary】{desc_en}".replace('"', "'").replace('\n', ' ').strip()
    
    yaml_header = f"""---
title: "{clean_title}"
description: "{clean_desc}"
pubDate: "{today}"
---"""
    return yaml_header

def get_today_target_and_count(target_dir):
    """
    1. 根据今天日期确定今天随机生成的目标总篇数 (1 ~ 5 篇)
    2. 统计今天已经生成的文章数量
    """
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 用当天日期做随机种子，保证“今天”的目标篇数固定（到了“明天”会自动重新随机 1~5 篇）
    seed_value = int(today_str.replace("-", ""))
    random.seed(seed_value)
    daily_target = random.randint(1, 5) # 随机 1 到 5 篇
    
    # 恢复系统的真随机
    random.seed()

    if not os.path.exists(target_dir):
        return daily_target, 0
    
    today_files = [f for f in os.listdir(target_dir) if f.startswith(today_str) and f.endswith(".md")]
    return daily_target, len(today_files)

def generate_article():
    target_dir = os.path.join("src", "content", "blog")
    
    # 1. 获取今天的目标总数和已生成数量
    daily_target, current_count = get_today_target_and_count(target_dir)
    print(f"今日随机分配配额: {daily_target} 篇 | 当前已发布: {current_count} 篇")

    # 2. 如果已经达到今天的随机上限，直接退出
    if current_count >= daily_target:
        print(f"已达到今日随机发布上限 ({daily_target} 篇)，本次运行跳过。")
        return

    # 3. 增加随机概率波动（例如 60% 概率生成），让发布时间点更加分散自然
    if random.random() > 0.6:
        print("随机抽查未命中（本次概率跳过），等待下一次触发。")
        return

    print("=== 开始通过 DeepSeek 撰写双语分离精品质感健康文章 ===")

    topic_pair = random.choice(TOPICS)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
你是一位顶级的健康医学科普作家与抗衰老研究学者。
请围绕主题《{topic_pair['cn']}》/ "{topic_pair['en']}" 撰写一篇深度博客文章。

请严格按照以下格式输出（切勿混杂，必须包含两个明确的分隔标记线）：

=== ENGLISH SECTION ===
(这里只用纯英文撰写完整的文章，从一级/二级标题开始，包括：Introduction, Core Mechanisms, Actionable Recommendations, Conclusion。全程不出现任何中文汉字。)

=== CHINESE SECTION ===
(这里只用纯中文撰写完整的文章，从一级/二级标题开始，包括：引言、核心机制、实操建议、总结。全程不出现任何英文字段，排版清晰。)
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    
    raw_content = response.choices[0].message.content.strip()

    # 摘要生成
    desc_cn = "深入剖析健康机制与前沿科学，提供切实可行的日常改善策略。"
    desc_en = "Exploring health mechanics and cutting-edge science, providing actionable lifestyle strategies."

    yaml_header = clean_yaml_frontmatter(topic_pair['cn'], topic_pair['en'], desc_cn, desc_en, today)
    
    # 解析并用 HTML div 包裹英文区与中文区，彻底实现结构分离
    en_body = ""
    cn_body = ""
    
    if "=== CHINESE SECTION ===" in raw_content:
        parts = raw_content.split("=== CHINESE SECTION ===")
        en_part = parts[0].replace("=== ENGLISH SECTION ===", "").strip()
        cn_part = parts[1].strip()
        
        en_body = f'<div class="lang-block lang-en">\n\n{en_part}\n\n</div>'
        cn_body = f'<div class="lang-block lang-cn" style="display: none;">\n\n{cn_part}\n\n</div>'
    else:
        en_body = f'<div class="lang-block lang-en">\n\n{raw_content}\n\n</div>'

    final_content = f"{yaml_header}\n\n{en_body}\n\n{cn_body}"

    # 保存文件
    filename = f"{today}-{random.randint(1000, 9999)}.md"
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, filename)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)
        
    print(f"成功保存文章至: {file_path}")

if __name__ == "__main__":
    generate_article()
