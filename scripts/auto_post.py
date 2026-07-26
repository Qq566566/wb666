import os
import random
import datetime
from openai import OpenAI

# 1. 配置 DeepSeek API 端点
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"  # 指向 DeepSeek 官方接口
)

# 2. 备选 SEO 主题库
TOPICS = [
    "2026年个人博客如何优化SEO并提升 Google 排名",
    "静态网站生成器对比：Astro vs Hugo vs Hexo",
    "为什么全自动 AI 建站是未来的趋势",
    "如何利用 Serverless 架构实现零成本网站托管",
    "新手搭建个人网站需要避开的 5 个坑",
    "DeepSeek 在自动化内容生成中的实战指南"
]

def generate_article():
    topic = random.choice(TOPICS)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    prompt = f"""
你是一位资深的 SEO 内容专家和科技博主。
请围绕主题《{topic}》写一篇深度 Markdown 博客文章。

要求如下：
1. 顶部必须包含 Front Matter 元数据，格式严格如下：
---
title: "文章标题"
description: "150字以内的文章摘要，用于SEO"
pubDate: "{today}"
---

2. 正文要求：
- 使用标准的 Markdown 格式（使用 ##, ### 标题，列表，粗体等）
- 结构清晰，包含背景、核心观点、实操建议、总结
- 内容通顺自然，字数在 1000-1800 字之间。
- 不要输出额外的解释性文字或 ```markdown 包裹符，直接返回 Front Matter + 文章正文。
"""

    print(f"正在使用 DeepSeek 生成主题文章: {topic} ...")
    
    response = client.chat.completions.create(
        model="deepseek-chat",  # 使用 DeepSeek V3 模型，性价比极高
        messages=[
            {"role": "user", "content": prompt}
        ],
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

    # 3. 将文件保存到 Astro 的文章目录下
    filename = f"{today}-{random.randint(1000, 9999)}.md"
    file_path = os.path.join("src", "content", "blog", filename)
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"成功保存文章至: {file_path}")

if __name__ == "__main__":
    generate_article()
