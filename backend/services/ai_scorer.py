import json
import re

import httpx

from models import ModelConfig
from services.model_manager import decrypt_api_key

SCORING_PROMPT = """你是一个专业剧本评估师。请严格按照以下框架对剧本进行评分和分析。

---

## 评分规则

对以下五个维度分别打分，每项 **1-100 分**（100 分为满分）。评价分取五个维度的平均分。

### 一、有趣度（1-100 分）

评估剧本是否有趣、抓人眼球。重点考察：
- 故事概念是否新颖、有想象力
- 是否有让人想继续往下看的钩子和悬念
- 煽情、恋爱、悬疑等类型特征是否足够鲜明
- 能否引发观众的情绪共鸣（笑、哭、紧张、感动）

### 二、热门程度（1-100 分）

评估该题材在当前市场是否热门、是否有爆款潜力。重点考察：
- **题材热度**：该题材类型在当前市场是否正处于热潮
- **爆款潜力**：剧本核心卖点是否具备出圈传播的基因
- 目标受众是否明确、受众规模是否足够大
- 是否踩中当下观众的情绪需求和社会话题趋势

### 三、逻辑程度（1-100 分）

评估剧本的逻辑严密性。重点考察：
- **人物设定完整性**：人物背景、性格、动机、成长弧是否交代清楚
- **人物与剧情一致性**：人物行为是否符合其设定，有没有前后矛盾
- **剧情逻辑漏洞**：情节推进是否合理
- **站位逻辑**：角色在场景中的位置、动作、行动路线是否合理
- **空间逻辑**：场景的空间关系是否清晰合理
- **时间逻辑**：时间线是否连贯自洽
- 设定世界观内部自洽（玄幻/科幻/架空题材特别关注此项）

### 四、动作链流畅度（1-100 分）

评估场景之间、事件之间的衔接质量。重点考察：
- 场景转换是否自然，有没有"硬切"或跳跃感
- 一个事件到下一个事件的因果链条是否清晰（A 导致 B，B 导致 C）
- 动作/事件链是否有断裂（上一段还在处理一件事，下一段莫名其妙跳到另一件事）
- 转场方式是否服务于叙事（而非为了转场而转场）

### 五、剧情发展流畅度（1-100 分）

评估整体叙事节奏和结构。重点考察：
- 起承转合是否完整、节奏是否舒服
- 高潮与低谷的分布是否合理，有没有拖沓或过快的问题
- 支线是否干扰主线，多线叙事是否清晰不乱
- 整体观感是否一气呵成

---

## 输出格式

请输出以下两部分，然后输出 JSON。

### 第一部分：评分表

用纯文本表格列出每个维度的分数、给分理由和扣分理由：

```
┌──────────┬────────┬──────────────────────────┬──────────────────────────┐
│ 评分维度 │  分数  │       给分理由           │       扣分理由           │
├──────────┼────────┼──────────────────────────┼──────────────────────────┤
│ 有趣度   │ X/100  │ （一句话）               │ （一句话）               │
│ 热门程度 │ X/100  │ （一句话）               │ （一句话）               │
│ 逻辑程度 │ X/100  │ （一句话）               │ （一句话）               │
│ 动作链流畅度│X/100│ （一句话）               │ （一句话）               │
│ 剧情发展流畅度│X/100│（一句话）              │ （一句话）               │
├──────────┼────────┼──────────────────────────┼──────────────────────────┤
│ 评价分   │ XX/100 │                          │                          │
└──────────┴────────┴──────────────────────────┴──────────────────────────┘
```

### 第二部分：逐维度分析

按五个维度逐一分析。**必须严格使用以下两段式结构**：先用 `【问题】` 标题列出所有维度的问题，再用 `【建议】` 标题列出所有维度的建议。如果某维度无问题/建议，写"无"。

```
【问题】
【有趣度】
开场"发光草"的出现没有前因后果，观众会困惑这是幻觉还是设定。

【热门程度】
奇幻设定仅通过两个隐晦伏笔暗示，首场戏奇幻冲击力不足。

【逻辑程度】
主角接受任务的动机太弱，缺少内心挣扎。

【动作链流畅度】
无

【剧情发展流畅度】
开场信息密度高，留给观众消化时间不足。


【建议】
【有趣度】
增加主角看到发光草后揉眼、自言自语"眼花了"的动作。

【热门程度】
在"意识之间"场景增加发光草药叶片围绕旋转的视觉元素。

【逻辑程度】
在主角同意前插入 2-3 秒的沉默特写。

【动作链流畅度】
无

【剧情发展流畅度】
删减合并部分播报内容，让观众通过角色视角去发现信息。
```

---

## 注意事项

1. **必须读完提供的全部剧本内容后再评分**，不要只看开头就下结论。
2. 分数要有区分度——有明显问题时不要给 70 分以上，各方面都优秀的不要吝啬给 90 分以上。
3. 问题描述要具体到剧本中的位置或情节，不要笼统。
4. 建议要具体可操作，不要只讲空泛的原则。
5. 如果只提供了剧本片段，在最后标注"（基于已提供的内容评估，完整剧本可能有不同结论）"。

---

## 最后，请同时输出以下 JSON（放在你的回复末尾）：

```json
{
  "interestingness": 整数1-100,
  "popularity": 整数1-100,
  "logic": 整数1-100,
  "action_smoothness": 整数1-100,
  "plot_smoothness": 整数1-100,
  "overall": 五维度平均分保留1位小数,
  "analysis": [
    {
      "dimension": "有趣度",
      "pros": "给分理由（一句话）",
      "cons": "扣分理由（一句话）",
      "issues": ["问题描述1", "问题描述2"],
      "suggestions": ["改进建议1", "改进建议2"]
    },
    {
      "dimension": "热门程度",
      "pros": "...",
      "cons": "...",
      "issues": ["..."],
      "suggestions": ["..."]
    },
    {
      "dimension": "逻辑程度",
      "pros": "...",
      "cons": "...",
      "issues": ["..."],
      "suggestions": ["..."]
    },
    {
      "dimension": "动作链流畅度",
      "pros": "...",
      "cons": "...",
      "issues": ["..."],
      "suggestions": ["..."]
    },
    {
      "dimension": "剧情发展流畅度",
      "pros": "...",
      "cons": "...",
      "issues": ["..."],
      "suggestions": ["..."]
    }
  ],
  "score_table": "将第一部分评分表的纯文本表格原样放入此字段"
}
```

> **重要**：每个维度的 `issues` 和 `suggestions` 必须是字符串数组。如果某维度没有问题或建议，使用空数组 `[]`。问题和建议要具体到剧本中的位置或情节，不要空泛。

以下是剧本内容：
---
{script_content}
---"""


def extract_json(text: str) -> dict:
    """从 LLM 返回中提取 JSON，兼容 markdown 代码块包裹"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 尝试匹配 ```json ... ``` 或 ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # 尝试匹配第一个 { ... }
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError("AI 返回格式异常，无法解析评分数据")


def split_analysis(analysis_text: str) -> tuple[str, str]:
    """按【建议】段落标题拆分分析文本"""
    import re
    # 匹配独立成段的【建议】标题（后面没有紧跟文字，或跟换行）
    m = re.search(r'\n【建议】\s*\n', analysis_text)
    if m:
        idx = m.start()
        problems_part = analysis_text[:idx].strip()
        suggestions_part = analysis_text[idx + m.group().__len__():].strip()
        return problems_part, suggestions_part
    # fallback: 旧格式逐行匹配
    problems = []
    suggestions = []
    current_dim = ""
    for line in analysis_text.split('\n'):
        dim_match = re.match(r'【(有趣度|热门程度|逻辑程度|动作链流畅度|剧情发展流畅度)】', line)
        if dim_match:
            current_dim = dim_match.group(1)
            continue
        if '【问题】' in line:
            p = line.split('【问题】', 1)[1].strip()
            if p and p != '无':
                problems.append(f"【{current_dim}】{p}" if current_dim else p)
        if '【建议】' in line:
            s = line.split('【建议】', 1)[1].strip()
            if s and s != '无':
                suggestions.append(f"【{current_dim}】{s}" if current_dim else s)
    return '\n'.join(problems) if problems else '', '\n'.join(suggestions) if suggestions else ''


def validate_scores(data: dict) -> dict:
    """校验评分数据完整性，兼容新旧两种 JSON 格式"""
    fields = ["interestingness", "popularity", "logic", "action_smoothness", "plot_smoothness"]
    for f in fields:
        if f not in data:
            raise ValueError(f"AI返回缺少字段: {f}")
        val = int(data[f])
        if val < 1 or val > 100:
            raise ValueError(f"评分字段 {f} 超出范围: {val}")
        data[f] = val
    data["overall"] = round(float(data.get("overall", sum(data[f] for f in fields) / 5)), 1)

    raw_analysis = data.get("analysis", "")
    score_table = str(data.get("score_table", "")) if isinstance(raw_analysis, list) else ""

    if isinstance(raw_analysis, list):
        # --- 新格式：analysis 是结构化数组 ---
        problems_lines = []
        suggestions_lines = []
        dim_labels = ["有趣度", "热门程度", "逻辑程度", "动作链流畅度", "剧情发展流畅度"]
        for item in raw_analysis:
            dim = str(item.get("dimension", ""))
            pros = str(item.get("pros", ""))
            cons = str(item.get("cons", ""))
            issues = item.get("issues", [])
            suggestions = item.get("suggestions", [])

            if issues:
                problems_lines.append(f"【{dim}】")
                for iss in issues:
                    problems_lines.append(str(iss))
            if suggestions:
                suggestions_lines.append(f"【{dim}】")
                for sug in suggestions:
                    suggestions_lines.append(str(sug))

        # 构建前端展示用的文本
        table = score_table or ""
        problems_text = "\n".join(problems_lines) if problems_lines else "无"
        suggestions_text = "\n".join(suggestions_lines) if suggestions_lines else ""

        if table:
            data["analysis"] = (table + "\n\n【问题分析】\n" + problems_text)[:8000]
        else:
            data["analysis"] = problems_text[:8000] if problems_text != "无" else ""
        data["suggestions"] = suggestions_text[:8000] if suggestions_text else ""
    else:
        # --- 旧格式：analysis 是字符串，用段落标记拆分 ---
        raw_str = str(raw_analysis)[:8000]
        problems_part, suggestions_part = split_analysis(raw_str)
        data["analysis"] = problems_part or raw_str
        data["suggestions"] = suggestions_part[:8000] if suggestions_part else ""

    return data


async def score_script(script_content: str, model_config: ModelConfig, timeout: int = 300, progress_callback=None) -> dict:
    """执行 AI 评分。progress_callback 为可选异步函数，接收进度文本。"""
    api_key = decrypt_api_key(model_config.api_key)
    prompt = SCORING_PROMPT.replace("{script_content}", script_content)

    async def report(msg: str):
        if progress_callback:
            await progress_callback(msg)

    await report("正在调用AI模型进行五维度评分分析（预计2-5分钟）...")

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{model_config.api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_config.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 16384,
            },
        )
        if resp.status_code != 200:
            raise ValueError(f"模型API返回 HTTP {resp.status_code}，请检查模型配置")

        await report("AI模型返回结果，正在解析评分数据...")

        data = resp.json()
        if "choices" not in data or not data["choices"]:
            raise ValueError("模型返回数据格式异常")

        content = data["choices"][0]["message"]["content"]
        try:
            result = extract_json(content)
            validated = validate_scores(result)
            await report("评分完成")
            return validated
        except ValueError:
            raise ValueError("AI 返回了无法解析的评分结果，可能是模型不支持该任务")


async def score_script_stream(script_content: str, model_config: ModelConfig, token_callback=None, timeout: int = 300) -> dict:
    """流式执行 AI 评分。token_callback 为可选异步函数，接收每个生成的文本片段。"""
    api_key = decrypt_api_key(model_config.api_key)
    prompt = SCORING_PROMPT.replace("{script_content}", script_content)

    async def emit(token: str):
        if token_callback:
            await token_callback(token)

    full_response = ""

    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream(
            "POST",
            f"{model_config.api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_config.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 16384,
                "stream": True,
            },
        ) as resp:
            if resp.status_code != 200:
                raise ValueError(f"模型API返回 HTTP {resp.status_code}，请检查模型配置")

            async for line in resp.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        full_response += content
                        await emit(content)
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue

    if not full_response.strip():
        raise ValueError("AI 流式返回为空，可能是模型不支持 stream 模式")

    result = extract_json(full_response)
    validated = validate_scores(result)
    return validated
