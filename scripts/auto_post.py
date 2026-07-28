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

# 2. 基础配置
MAX_DAILY_POSTS = 5  # 每日最多发布篇数
BLOG_DIR = os.path.join("src", "content", "blog")

def get_beijing_today():
    """获取北京时间 (UTC+8) 的今日日期字符串"""
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    beijing_now = utc_now + datetime.timedelta(hours=8)
    return beijing_now.strftime("%Y-%m-%d")

def fetch_today_health_trends():
    """抓取当日热点资讯/健康话题，作为 AI 选题依据"""
    trending_topics = []
    try:
        # 尝试抓取实时热门榜单 (以公开热搜/新闻接口为例)
        req = urllib.request.Request(
            "https://tenapi.cn/v2/baiduhot",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("code") == 200:
                for item in data.get("data", []):
                    title = item.get("name", "")
                    # 过滤与健康、生活、养生、医疗、生物相关的词汇
                    if any(k in title for k in ["健康", "医", "药", "病", "睡", "食", "老", "发", "身", "心", "血", "癌"]):
                        trending_topics.append(title)
    except Exception as e:
        print(f"⚠️ 热点抓取跳过或失败 ({e})，将使用备用前沿主题库。")

    # 如果没抓到特定健康热点，使用前沿方向做随机组合
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
    """读取已生成的博客文章标题，防止 AI 重复写同一个题材"""
    titles = []
    if not os.path.exists(BLOG_DIR):
        return titles

    for fname in os.listdir(BLOG_DIR):
        if fname.endswith(".md"):
            fpath = os.path.join(BLOG_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read(1000) # 读取文件头部 Front Matter
                    match = re.search(r'title:\s*"(.*?)"', content)
                    if match:
                        titles.append(match.group(1))
            except Exception:
                pass
    return titles[-20:] # 只取最近 20 篇作为防重参考

def clean_yaml_frontmatter(title_cn, title_en, desc_cn, desc_en, today):
    """构建安全的 Astro Markdown 头部信息"""
    clean_title = f"{title_cn} | {title_en}".replace('"', "'").strip()
    clean_desc = f"【中文摘要】{desc_cn}【English Summary】{desc_en}".replace('"', "'").replace('\n', ' ').strip()
    
    yaml_header = f"""---
title: "{clean_title}"
description: "{clean_desc}"
pubDate: "{today}"
---"""
    return yaml_header

def generate_article():
    today = get_beijing_today()
    os.makedirs(BLOG_DIR, exist_ok=True)
    
    # 检查今天已经发了多少篇
    today_files = [f for f in os.listdir(BLOG_DIR) if f.startswith(today) and f.endswith(".md")]
    current_count = len(today_files)
    
    is_manual = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
    
    if not is_manual:
        print(f"🤖 [定时任务] 今日已发布: {current_count}/{MAX_DAILY_POSTS} 篇")
        if current_count >= MAX_DAILY_POSTS:
            print(f"已达到每日最多发布上限 ({MAX_DAILY_POSTS} 篇)，本次任务结束。")
            return
    else:
        print("⚡ [手动触发] 忽略每日额度限制，强制生成 1 篇新文章！")

    # 获取热点和历史已写标题
    trend = fetch_today_health_trends()
    existing_titles = get_existing_titles()
    
    print(f"=== 开始撰写文章 (参考热点/方向: {trend}) ===")

    prompt = f"""
你是一位顶级的健康医学科普作家与抗衰老研究学者。
请结合今天的健康热点/前沿方向《{trend}》，为你自己的双语健康博客撰写一篇**全新切入点**的深度科普文章。

【防重要求】：
以下是你之前已经撰写过的文章标题，**绝对不要重复**类似的主题或观点：
{json.dumps(existing_titles, ensure_ascii=False)}

【输出要求】：
请严格按照以下格式输出（切勿混杂，必须包含明确的分隔标记线）：

=== TITLE SECTION ===
CN_TITLE: (这里写一个吸引人且专业的中文文章标题)
EN_TITLE: (这里写对应的英文文章标题)
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
        temperature=0.85, # 调高随机性度数，确保创意性
    )

    raw_content = response.choices[0].message.content.strip()

    # 解析标题和摘要
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

    # 解析正文（双语分块）
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

    # 生成随机序号文件名
    filename = f"{today}-{random.randint(1000, 9999)}.md"
    file_path = os.path.join(BLOG_DIR, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)

    print(f"✅ 成功生成并保存文章: {file_path}")
    print(f"📌 最终标题: {title_cn}")

if __name__ == "__main__":
    generate_article()
