import os
import random
import datetime
import sys
import re
import json
import urllib.request
from openai import OpenAI

# 1. 初始化客户端
api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("未找到 DEEPSEEK_API_KEY 环境变量！")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

# 2. 配置参数
MAX_DAILY_POSTS = 5  # 定时发布的每日上限
BLOG_DIR = os.path.join("src", "content", "blog")

def get_beijing_today():
    """获取北京时间 (UTC+8) 日期字符串 YYYY-MM-DD"""
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    beijing_now = utc_now + datetime.timedelta(hours=8)
    return beijing_now.strftime("%Y-%m-%d")

def fetch_today_health_trends():
    """抓取当日健康/医学热点主题"""
    trending_topics = []
    try:
        req = urllib.request.Request(
            "https://tenapi.cn/v2/baiduhot",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("code") == 200:
                for item in data.get("data", []):
                    title = item.get("name", "")
                    if any(k in title for k in ["健康", "医", "药", "病", "睡", "食", "老", "身", "心", "血"]):
                        trending_topics.append(title)
    except Exception as e:
        print(f"⚠️ 热点抓取跳过 ({e})，将切换至备用知识库。")

    if not trending_topics:
        backup_angles = [
            "最新的昼夜节律与睡眠修复研究",
            "肠道菌群与情绪管理的前沿进展",
            "针对慢性炎症的抗炎饮食策略",
            "办公族抗疲劳与线粒体激活",
            "科学补镁与神经系统放松",
            "细胞自噬与延缓衰老的日常实践"
        ]
        trending_topics.append(random.choice(backup_angles))

    return random.choice(trending_topics)

def get_existing_titles():
    """读取历史文章标题，实现智能防重"""
    titles = []
    if not os.path.exists(BLOG_DIR):
        return titles

    for fname in os.listdir(BLOG_DIR):
        if fname.endswith(".md"):
            fpath = os.path.join(BLOG_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read(1000)
                    match = re.search(r'title:\s*"(.*?)"', content)
                    if match:
                        titles.append(match.group(1))
            except Exception:
                pass
    return titles[-20:]

def clean_yaml_frontmatter(title_cn, title_en, desc_cn, desc_en, today):
    clean_title = f"{title_cn} | {title_en}".replace('"', "'").strip()
    clean_desc = f"【中文摘要】{desc_cn}【English Summary】{desc_en}".replace('"', "'").replace('\n', ' ').strip()
    
    # 注意：pubDate 切勿使用引号包裹，保证 YAML 将其识别为原生 Date
    return f"""---
title: "{clean_title}"
description: "{clean_desc}"
pubDate: {today}
---"""

def generate_article():
    today = get_beijing_today()
    os.makedirs(BLOG_DIR, exist_ok=True)
    
    # 区分手动触发与定时触发
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    is_manual = (event_name == "workflow_dispatch")
    
    # 统计今天生成的文章数量
    today_files = [f for f in os.listdir(BLOG_DIR) if f.startswith(today) and f.endswith(".md")]
    current_count = len(today_files)

    if is_manual:
        print("⚡ [手动触发] 绕过限制：手动提交不计入每日上限配额！")
    else:
        print(f"🤖 [定时任务] 今日已发布: {current_count}/{MAX_DAILY_POSTS} 篇")
        if current_count >= MAX_DAILY_POSTS:
            print(f"已达到每日最多定时发布上限 ({MAX_DAILY_POSTS} 篇)，本次跳过。")
            return

    trend = fetch_today_health_trends()
    existing_titles = get_existing_titles()
    
    print(f"=== 开始撰写文章 (参考热点: {trend}) ===")

    prompt = f"""
你是一位顶级的健康医学科普作家与抗衰老研究学者。
请结合今天的健康热点/前沿方向《{trend}》，为你自己的双语健康博客撰写一篇**全新切入点**的深度科普文章。

【防重要求】：
以下是你之前已经撰写过的文章标题，**绝对不要重复**类似的主题或观点：
{json.dumps(existing_titles, ensure_ascii=False)}

【输出要求】：
请严格按照以下格式输出：

=== TITLE SECTION ===
CN_TITLE: (吸引人且专业的中文文章标题)
EN_TITLE: (对应的英文文章标题)
CN_DESC: (一句话中文摘要，100字以内)
EN_DESC: (一句话英文摘要)

=== ENGLISH SECTION ===
(用纯英文撰写完整文章，包括：Introduction, Core Mechanisms, Actionable Recommendations, Conclusion。)

=== CHINESE SECTION ===
(用纯中文撰写完整文章，包括：引言、核心机制、实操建议、总结。)
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.85,
    )

    raw_content = response.choices[0].message.content.strip()

    title_cn, title_en = "最新健康前沿研究", "Latest Health Science Research"
    desc_cn, desc_en = "探讨最新健康科学机制与实操策略。", "Exploring health mechanisms and lifestyle strategies."
    
    if "=== TITLE SECTION ===" in raw_content:
        title_part = raw_content.split("=== ENGLISH SECTION ===")[0]
        m_cn = re.search(r'CN_TITLE:\s*(.*)', title_part)
        m_en = re.search(r'EN_TITLE:\s*(.*)', title_part)
        d_cn = re.search(r'CN_DESC:\s*(.*)', title_part)
        d_en = re.search(r'EN_DESC:\s*(.*)', title_part)
        
        if m_cn: title_cn = m_cn.group(1).strip()
        if m_en: title_en = m_en.group(1).strip()
        if d_cn: desc_cn = d_cn.group(1).strip()
        if d_en: desc_en = d_en.group(1).strip()

    yaml_header = clean_yaml_frontmatter(title_cn, title_en, desc_cn, desc_en, today)

    en_body, cn_body = "", ""
    if "=== CHINESE SECTION ===" in raw_content:
        parts = raw_content.split("=== CHINESE SECTION ===")
        en_part = parts[0].split("=== ENGLISH SECTION ===")[-1].strip()
        cn_part = parts[1].strip()
        en_body = f'<div class="lang-block lang-en">\n\n{en_part}\n\n</div>'
        cn_body = f'<div class="lang-block lang-cn" style="display: none;">\n\n{cn_part}\n\n</div>'
    else:
        en_body = f'<div class="lang-block lang-en">\n\n{raw_content}\n\n</div>'

    final_content = f"{yaml_header}\n\n{en_body}\n\n{cn_body}"

    filename = f"{today}-{random.randint(1000, 9999)}.md"
    file_path = os.path.join(BLOG_DIR, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)

    print(f"✅ 成功生成并保存文章: {file_path}")

if __name__ == "__main__":
    generate_article()
