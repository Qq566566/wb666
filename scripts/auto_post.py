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

def get_us_formatted_date(date_str):
    """转换 YYYY-MM-DD 为欧美美式风格日期 (例: July 29, 2026)"""
    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%B %d, %Y")

def generate_clean_slug(title_en):
    """将英文标题转化为干净的 URL slug (保留前 6 个核心单词)"""
    # 移除特殊字符，转小写，空格换连字符
    clean_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title_en.lower())
    slug_words = re.sub(r'[\s-]+', '-', clean_title).strip('-').split('-')[:6]
    slug = "-".join(slug_words)
    return slug if slug else "health-research"

def fetch_today_health_trends():
    """多源高可靠抓取：百度热搜官方 -> Bing 医学新闻 -> PubMed 真实权威论文"""
    trending_topics = []

    # 1. 尝试百度官方实时热搜榜
    try:
        url = "https://top.baidu.com/board?tab=realtime"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8')
            raw_titles = re.findall(r'"word":"([^"]+)"', html)
            
            keywords = ["健康", "医", "药", "病", "睡", "食", "老", "身", "心", "血", "脑", "肠", "肝", "癌", "糖", "脂", "维", "素", "菌"]
            for title in raw_titles:
                if any(k in title for k in keywords):
                    trending_topics.append(title)
        if trending_topics:
            print(f"🔥 成功从百度热搜抓取到 {len(trending_topics)} 个健康话题")
    except Exception as e:
        print(f"⚠️ 百度热搜抓取跳过 ({e})")

    # 2. 若百度未搜到，抓取 Bing 最新国内健康新闻
    if not trending_topics:
        try:
            bing_url = "https://cn.bing.com/news/search?q=%e5%81%a5%e5%ba%b7+%e5%8c%bb%e5%ad%a6+%e7%a0%94%e7%a9%b6"
            req = urllib.request.Request(bing_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                html = resp.read().decode('utf-8')
                titles = re.findall(r'class="title"[^>]*>(.*?)</a>', html)
                for t in titles:
                    clean_t = re.sub(r'<[^>]+>', '', t).strip()
                    if clean_t and len(clean_t) > 6:
                        trending_topics.append(clean_t)
            if trending_topics:
                print(f"📰 成功从 Bing 新闻抓取到 {len(trending_topics)} 个医学新闻话题")
        except Exception as e:
            print(f"⚠️ Bing 新闻抓取失败 ({e})")

    # 3. 终极学术兜底：直接向 PubMed 全球医学数据库请求最新权威论文标题
    if not trending_topics:
        try:
            print("🔬 开启 PubMed 权威论文数据库实时检索...")
            search_terms = ["longevity", "mitochondria", "circadian sleep", "gut microbiota", "autophagy", "cellular senescence", "metabolism"]
            chosen_term = random.choice(search_terms)
            
            pm_search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={chosen_term}&retmax=10&sort=pub_date&retmode=json"
            req = urllib.request.Request(pm_search_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                id_list = data.get("esearchresult", {}).get("idlist", [])

            if id_list:
                pm_summary_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(id_list)}&retmode=json"
                req_sum = urllib.request.Request(pm_summary_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req_sum, timeout=5) as resp:
                    sum_data = json.loads(resp.read().decode('utf-8')).get("result", {})
                    for p_id in id_list:
                        paper_title = sum_data.get(p_id, {}).get("title", "")
                        if paper_title:
                            trending_topics.append(paper_title)
            if trending_topics:
                print(f"📖 成功从 PubMed 检索到 {len(trending_topics)} 篇最新发表论文")
        except Exception as e:
            print(f"⚠️ PubMed 检索跳过 ({e})")

    # 4. 罕见失败时的极简降级（基于实时时间戳随机化）
    if not trending_topics:
        trending_topics.append(f"前沿生物医学机制与干预策略研究_{random.randint(1000, 9999)}")

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
                    # 匹配 frontmatter 中的 title
                    match = re.search(r'title:\s*"(.*?)"', content)
                    if match:
                        titles.append(match.group(1))
            except Exception:
                pass
    # 返回最近 20 篇标题用于 AI 参考
    return titles[-20:]

def clean_yaml_frontmatter(title_cn, title_en, desc_cn, desc_en, category, today, slug):
    """
    清洗并生成 Markdown Frontmatter。
    加入了 heroImage 和 image 字段，使用动态 URL 确保配图不重复。
    """
    # 替换引号防 YAML 崩溃
    clean_title = f"{title_cn} | {title_en}".replace('"', "'").strip()
    clean_desc = f"【中文摘要】{desc_cn}【English Summary】{desc_en}".replace('"', "'").replace('\n', ' ').strip()
    
    # 分类清洗
    clean_cat = re.sub(r'[^a-zA-Z]', '', category).lower()
    valid_categories = {"mitochondria", "nutrition", "sleep", "dna", "metabolism", "neuroscience", "longevity", "cellular"}
    if clean_cat not in valid_categories:
        clean_cat = "longevity"
    
    # ----------------【动态独一无二图片链接生成】----------------
    # 结合【今日日期 + 核心单词 Slug + 分类】，生成专属 Seed
    # 这样 Picsum API 会基于这个 Seed 返回一张固定的、但绝对不和别的文章重复的高清图
    img_seed = f"{today}-{slug}-{clean_cat}"
    # 这里同时注入 image 和 heroImage 字段，适配大部分 Astro 模板
    # 修改后的代码（带有科技/实验室蓝绿调风格）
hero_image = f"https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=1200&h=630&fit=crop&q=80"
    
    return f"""---
title: "{clean_title}"
description: "{clean_desc}"
pubDate: {today}
category: "{clean_cat}"
image: "{hero_image}"
heroImage: "{hero_image}"
---"""

def generate_article():
    today = get_beijing_today()
    us_date = get_us_formatted_date(today)
    os.makedirs(BLOG_DIR, exist_ok=True)
    
    # 检查发布配额
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    is_manual = (event_name == "workflow_dispatch")
    
    today_files = [f for f in os.listdir(BLOG_DIR) if f.endswith(f"-{today}.md")]
    current_count = len(today_files)

    if is_manual:
        print("⚡ [手动触发] 绕过限制：手动提交不计入每日上限配额！")
    else:
        print(f"🤖 [定时任务] 今日已发布: {current_count}/{MAX_DAILY_POSTS} 篇")
        if current_count >= MAX_DAILY_POSTS:
            print(f"已达到每日最多定时发布上限 ({MAX_DAILY_POSTS} 篇)，本次跳过。")
            return

    # 获取热点及查重
    trend = fetch_today_health_trends()
    existing_titles = get_existing_titles()
    
    print(f"=== 开始撰写智库级精选博文 (参考热点/论文: {trend}) ===")

    # 提示词：要求地道英文 + 学术中文
    prompt = f"""
You are the Chief Science Officer and Medical Journalist for "VITA Longevity Repository", a world-class health research database.

Write an authoritative, peer-reviewed style research paper based on: 《{trend}》.

【ANTI-DUPLICATION】:
Do not write about these past topics or use similar titles:
{json.dumps(existing_titles, ensure_ascii=False)}

【E-E-A-T & DE-AI WRITING REQUIREMENTS】:
1. STRICT NO AI CLICHÉS: NO "In a world where...", "It's not just A, it's B", "Double-edged sword", "Game-changer", "Revolutionary", "Delve into", "Tapestry".
2. PROFESSIONAL METADATA BLOCK:
   Near the top of the English section, you MUST output a metadata badge quote like this:
   `> 🔬 **Peer-Reviewed & Medically Checked** | **Evidence Level**: Grade A (Clinical & Mechanistic Studies) | **Reading Time**: 6 min`
3. STRUCTURE:
   - `> 💡 **Key Takeaways**`: 3 bullet points summarizing core actionable findings.
   - Core Mechanisms (mentioning Harvard, Stanford, Nature, or Cell studies).
   - Practical Protocol (Checklist / Table).
   - **References Section**: At the bottom, provide 2-3 real, traceable academic references (e.g., *Journal of Clinical Endocrinology*, *Nature Neuroscience*).
   - **Medical Disclaimer**: End with a formal medical disclaimer block.

【REQUIRED OUTPUT FORMAT】:
=== TITLE SECTION ===
CN_TITLE: (专业中文标题)
EN_TITLE: (Native, concise, and academic English title)
CN_DESC: (一句话中文摘要，100字以内)
EN_DESC: (One-sentence clear English summary)
CATEGORY: (Select strictly ONE English word from: [mitochondria, nutrition, sleep, dna, metabolism, neuroscience, longevity, cellular])

=== ENGLISH SECTION ===
(Write pure native English article matching all E-E-A-T requirements above.)

=== CHINESE SECTION ===
(写对应的地道中文版本，包含：元数据标识、核心要点卡片、机制解析、实操指南、参考文献与医学免责声明。)
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    raw_content = response.choices[0].message.content.strip()

    # 1. 解析标题部分
    rand_tag = random.randint(1000, 9999)
    # 使用随机字符串作为兜底，彻底解决默认标题重复
    title_cn, title_en = f"前沿健康科学机制解析 #{rand_tag}", f"Health Science Mechanism Study #{rand_tag}"
    desc_cn, desc_en = "探讨最新健康科学机制与实操策略。", "Exploring health mechanisms and lifestyle strategies."
    category = "longevity"
    
    if "=== TITLE SECTION ===" in raw_content:
        # 提取 === ENGLISH SECTION === 之前的部分
        title_part = raw_content.split("=== ENGLISH SECTION ===")[0]
        m_cn = re.search(r'CN_TITLE:\s*(.*)', title_part)
        m_en = re.search(r'EN_TITLE:\s*(.*)', title_part)
        d_cn = re.search(r'CN_DESC:\s*(.*)', title_part)
        d_en = re.search(r'EN_DESC:\s*(.*)', title_part)
        m_cat = re.search(r'CATEGORY:\s*(.*)', title_part)
        
        # 只有解析成功且不为空时才替换默认值
        if m_cn and m_cn.group(1).strip(): title_cn = m_cn.group(1).strip()
        if m_en and m_en.group(1).strip(): title_en = m_en.group(1).strip()
        if d_cn and d_cn.group(1).strip(): desc_cn = d_cn.group(1).strip()
        if d_en and d_en.group(1).strip(): desc_en = d_en.group(1).strip()
        if m_cat and m_cat.group(1).strip():
            # 提取时先做一次初步清洗，只保留字母
            category = re.sub(r'[^a-zA-Z]', '', m_cat.group(1)).lower()

    # 2. 生成 slug (基于英文标题)
    slug = generate_clean_slug(title_en)
    
    # 3. 清洗并生成 yaml frontmatter (传入 slug 用于生成唯一图片 Seed)
    yaml_header = clean_yaml_frontmatter(title_cn, title_en, desc_cn, desc_en, category, today, slug)

    # 4. 拼接中英文正文
    en_body, cn_body = "", ""
    if "=== CHINESE SECTION ===" in raw_content:
        parts = raw_content.split("=== CHINESE SECTION ===")
        # 移除标识符，提取英文部分
        en_part = parts[0].split("=== ENGLISH SECTION ===")[-1].strip()
        cn_part = parts[1].strip()
        # 注入多语言切换控制的 div (如果前端需要)
        en_body = f'<div class="lang-block lang-en">\n\n{en_part}\n\n</div>'
        cn_body = f'<div class="lang-block lang-cn" style="display: none;">\n\n{cn_part}\n\n</div>'
    else:
        # 如果格式解析失败，默认当作英文正文
        en_body = f'<div class="lang-block lang-en">\n\n{raw_content}\n\n</div>'

    final_content = f"{yaml_header}\n\n{en_body}\n\n{cn_body}"

    # 5. 保存文件 (增加文件名防撞击 Hash)
    filename = f"{slug}-{today}.md"
    file_path = os.path.join(BLOG_DIR, filename)
    
    # 如果遇到同名文件，自动追加随机 Tag，彻底解决文件名覆盖导致重复
    if os.path.exists(file_path):
        filename = f"{slug}-{rand_tag}-{today}.md"
        file_path = os.path.join(BLOG_DIR, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_content)

    print(f"✅ 成功生成智库级权威文章: {file_path}")

if __name__ == "__main__":
    generate_article()
