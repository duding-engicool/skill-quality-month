#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""质量月活动策划报告生成器：读取结构化 JSON，输出 Markdown + 精美网页版 HTML。
章节：总体方案 / 活动排期（时间轴）/ 宣传文案 / 总结评优（评分表）。
所有缺失信息章节标注「供参考·待确认」。"""
import argparse
import json
import sys

# 阶段配色（用于时间轴）
PHASE_COLOR = ["#2980B9", "#27AE60", "#E67E22", "#8E44AD", "#16A085"]


def collect_pending(data):
    """汇总所有「供参考·待确认」项。"""
    pending = []
    if not data.get("budget"):
        pending.append("预算：未提供，方案规模可行性无法评估")
    if not data.get("theme"):
        pending.append("主题：未提供，宣传文案与启动会致辞缺锚点")
    if not data.get("scope"):
        pending.append("参与范围：未提供，组织架构与活动覆盖无法定")
    promo = data.get("promo", {})
    if promo.get("pending"):
        for p in promo["pending"]:
            pending.append(f"宣传文案-{p}")
    se = data.get("summary_eval", {})
    if se.get("pending"):
        for p in se["pending"]:
            pending.append(f"总结评优-{p}")
    for p in data.get("pending", []):
        pending.append(p)
    return pending


def build_md(data):
    org = data.get("org", "未命名组织")
    year = data.get("year", "")
    theme = data.get("theme") or "（待确认）"
    cycle = data.get("cycle", "（待确认）")
    scope = data.get("scope") or "（待确认）"
    budget = data.get("budget") or "（待确认）"
    goals = data.get("goals", [])
    principles = data.get("plan", {}).get("principles", [])
    org_mechanism = data.get("plan", {}).get("org_structure", "")
    background = data.get("plan", {}).get("background", "")
    schedule = data.get("schedule", [])
    promo = data.get("promo", {})
    se = data.get("summary_eval", {})
    pending = collect_pending(data)

    L = []
    L.append(f"# 质量月活动策划报告\n")
    L.append(f"**组织**：{org}　**届次**：{year}")
    L.append(f"**主题**：{theme}")
    L.append(f"**周期**：{cycle}")
    L.append(f"**参与范围**：{scope}")
    L.append(f"**预算**：{budget}")
    L.append("")
    if pending:
        L.append(f"> ⚠️ 共 {len(pending)} 项标注「供参考·待确认」，方案未完全定稿，落地前需补齐。\n")

    # 一、总体方案
    L.append("## 一、活动总体方案\n")
    if background:
        L.append(f"**背景**：{background}\n")
    if goals:
        L.append("**目标**")
        for g in goals:
            L.append(f"- {g}")
        L.append("")
    if principles:
        L.append("**原则**")
        for p in principles:
            L.append(f"- {p}")
        L.append("")
    if org_mechanism:
        L.append(f"**组织机制**：{org_mechanism}\n")

    # 二、排期与清单
    L.append("## 二、活动排期与清单\n")
    if schedule:
        for ph in schedule:
            note = " ⚠待确认" if ph.get("note") else ""
            L.append(f"### {ph.get('phase','')}（{ph.get('date','')}）{note}\n")
            items = ph.get("items", [])
            if items:
                L.append("| 事项 | 责任方 | 产出 |")
                L.append("|------|--------|------|")
                for it in items:
                    L.append(f"| {it.get('name','')} | {it.get('owner','')} | {it.get('output','')} |")
                L.append("")
    else:
        L.append("（排期未提供，标注「供参考·待确认」）\n")

    # 三、宣传文案
    L.append("## 三、宣传文案包\n")
    slogans = promo.get("slogans", [])
    if slogans:
        L.append("**主题口号**")
        for s in slogans:
            L.append(f"- {s}")
        L.append("")
    if promo.get("speech"):
        L.append(f"**启动会致辞（要点/草稿）**\n\n{promo['speech']}\n")
    if promo.get("poster_copy"):
        L.append(f"**海报文案**\n\n{promo['poster_copy']}\n")
    if promo.get("article"):
        L.append(f"**公众号推文（角度/草稿）**\n\n{promo['article']}\n")

    # 四、总结与评优
    L.append("## 四、总结与评优\n")
    if se.get("effect_summary"):
        L.append(f"**成效总结框架**\n\n{se['effect_summary']}\n")
    metrics = se.get("metrics", [])
    if metrics:
        L.append("**关键指标对比**")
        L.append("| 指标 | 目标 | 实际 |")
        L.append("|------|------|------|")
        for m in metrics:
            L.append(f"| {m.get('name','')} | {m.get('target','')} | {m.get('actual','（待填报）')} |")
        L.append("")
    awards = se.get("awards", [])
    if awards:
        for aw in awards:
            L.append(f"**{aw.get('name','')}评选**")
            L.append(f"- 评选标准：{aw.get('criteria','')}")
            st = aw.get("score_table", [])
            if st:
                L.append("- 评分表：")
                L.append("| 维度 | 权重 | 评分要点 |")
                L.append("|------|------|----------|")
                for r in st:
                    L.append(f"| {r.get('dim','')} | {r.get('weight','')} | {r.get('point','')} |")
            L.append("")

    # 五、待确认项
    if pending:
        L.append("## 五、供参考·待确认项\n")
        for p in pending:
            L.append(f"- {p}")
        L.append("")
    return "\n".join(L)


def timeline_svg(schedule):
    if not schedule:
        return ""
    n = len(schedule)
    w, h = 920, 150
    seg = w / n
    bars = []
    for i, ph in enumerate(schedule):
        x = i * seg + 10
        color = PHASE_COLOR[i % len(PHASE_COLOR)]
        bars.append(
            f"<rect x='{x:.0f}' y='40' width='{seg-20:.0f}' height='34' rx='6' fill='{color}' opacity='0.85'/>"
            f"<text x='{x+seg/2-10:.0f}' y='62' font-size='12' fill='#fff' text-anchor='middle'>{ph.get('phase','')[:6]}</text>"
            f"<text x='{x+seg/2-10:.0f}' y='96' font-size='10' fill='#7f8c8d' text-anchor='middle'>{ph.get('date','')[:12]}</text>"
        )
    return (f"<svg width='{w}' height='{h}' viewBox='0 0 {w} {h}'>"
            f"<text x='10' y='24' font-size='13' fill='#2c3e50'>活动阶段时间轴</text>"
            f"{''.join(bars)}</svg>")


def build_html(data):
    org = data.get("org", "未命名组织")
    year = data.get("year", "")
    theme = data.get("theme") or "（待确认）"
    cycle = data.get("cycle", "（待确认）")
    scope = data.get("scope") or "（待确认）"
    budget = data.get("budget") or "（待确认）"
    goals = data.get("goals", [])
    principles = data.get("plan", {}).get("principles", [])
    org_mechanism = data.get("plan", {}).get("org_structure", "")
    background = data.get("plan", {}).get("background", "")
    schedule = data.get("schedule", [])
    promo = data.get("promo", {})
    se = data.get("summary_eval", {})
    pending = collect_pending(data)

    goal_html = "".join(f"<li>{g}</li>" for g in goals) or "<li>（待确认）</li>"
    pri_html = "".join(f"<li>{p}</li>" for p in principles)
    bg_html = f"<p>{background}</p>" if background else "<p class='warn'>（背景未提供，标注待确认）</p>"
    om_html = f"<p>{org_mechanism}</p>" if org_mechanism else "<p class='warn'>（组织机制未提供）</p>"

    # 排期表
    sched_html = ""
    if schedule:
        rows = ""
        for ph in schedule:
            note = " <span class='warn'>⚠待确认</span>" if ph.get("note") else ""
            items = ph.get("items", [])
            its = "".join(
                f"<tr><td>{it.get('name','')}</td><td>{it.get('owner','')}</td><td>{it.get('output','')}</td></tr>"
                for it in items) or "<tr><td colspan='3' class='warn'>（无明细）</td></tr>"
            rows += (f"<tr class='ph'><td colspan='3'>【{ph.get('phase','')}】{ph.get('date','')}{note}</td></tr>{its}")
        sched_html = f"<table><tr><th>事项</th><th>责任方</th><th>产出</th></tr>{rows}</table>"
    else:
        sched_html = "<p class='warn'>排期未提供，标注「供参考·待确认」</p>"

    # 宣传文案
    slogans = promo.get("slogans", [])
    slogan_html = "".join(f"<li>{s}</li>" for s in slogans) or "<li class='warn'>（待确认）</li>"
    speech = promo.get("speech", "")
    poster = promo.get("poster_copy", "")
    article = promo.get("article", "")

    # 总结评优
    effect = se.get("effect_summary", "")
    metrics = se.get("metrics", [])
    metric_html = ""
    if metrics:
        mrows = "".join(
            f"<tr><td>{m.get('name','')}</td><td>{m.get('target','')}</td><td>{m.get('actual','（待填报）')}</td></tr>"
            for m in metrics)
        metric_html = f"<table><tr><th>指标</th><th>目标</th><th>实际</th></tr>{mrows}</table>"
    awards = se.get("awards", [])
    award_html = ""
    for aw in awards:
        st = aw.get("score_table", [])
        str_html = ""
        if st:
            srows = "".join(f"<tr><td>{r.get('dim','')}</td><td>{r.get('weight','')}</td><td>{r.get('point','')}</td></tr>" for r in st)
            str_html = f"<table><tr><th>维度</th><th>权重</th><th>评分要点</th></tr>{srows}</table>"
        award_html += (f"<h3>{aw.get('name','')}评选</h3><p>标准：{aw.get('criteria','')}</p>{str_html}")

    pending_html = "".join(f"<li>{p}</li>" for p in pending)
    pending_box = f"<div class='sec'><h2>五、供参考·待确认项（{len(pending)}）</h2><ul>{pending_html}</ul></div>" if pending else ""

    svg = timeline_svg(schedule)

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>质量月活动策划报告 - {org}</title>
<style>
 *{{box-sizing:border-box;font-family:-apple-system,"Microsoft YaHei",sans-serif;color:#2c3e50;}}
 body{{margin:0;background:#f4f6f8;padding:32px;}}
 .wrap{{max-width:980px;margin:0 auto;background:#fff;border-radius:12px;padding:36px;box-shadow:0 4px 20px rgba(0,0,0,.08);}}
 h1{{color:#1a252f;margin-top:0;border-bottom:3px solid #C8102E;padding-bottom:10px;}}
 h2{{color:#C8102E;margin-top:28px;}}
 h3{{color:#1a252f;}}
 .meta{{color:#7f8c8d;font-size:14px;margin:4px 0;}}
 .warn{{color:#e67e22;}}
 .sec{{margin-top:20px;}}
 table{{width:100%;border-collapse:collapse;margin-top:10px;}}
 th,td{{border:1px solid #ecf0f1;padding:8px 10px;font-size:13px;text-align:left;vertical-align:top;}}
 th{{background:#f8f9fa;}}
 tr.ph{{background:#fdf2f2;font-weight:bold;}}
 ul{{line-height:1.9;}}
 .card{{background:#f8f9fa;border-left:4px solid #C8102E;padding:10px 14px;border-radius:6px;margin:8px 0;}}
</style></head><body><div class="wrap">
<h1>质量月活动策划报告</h1>
<div class="meta">组织：{org}　|　届次：{year}</div>
<div class="meta">主题：{theme}</div>
<div class="meta">周期：{cycle}　|　参与范围：{scope}　|　预算：{budget}</div>
{'<div class="card warn">⚠️ 共 %d 项标注「供参考·待确认」，方案未完全定稿，落地前需补齐。</div>' % len(pending) if pending else ''}

<div class="sec"><h2>一、活动总体方案</h2>
{bg_html}
<p><b>目标</b></p><ul>{goal_html}</ul>
{('<p><b>原则</b></p><ul>%s</ul>' % pri_html) if pri_html else ''}
{om_html}
</div>

<div class="sec"><h2>二、活动排期与清单</h2>
{svg}
{sched_html}
</div>

<div class="sec"><h2>三、宣传文案包</h2>
<p><b>主题口号</b></p><ul>{slogan_html}</ul>
{('<div class="card"><b>启动会致辞</b><br>%s</div>' % speech) if speech else '<p class="warn">启动会致辞待确认</p>'}
{('<div class="card"><b>海报文案</b><br>%s</div>' % poster) if poster else ''}
{('<div class="card"><b>公众号推文</b><br>%s</div>' % article) if article else ''}
</div>

<div class="sec"><h2>四、总结与评优</h2>
{('<p>%s</p>' % effect) if effect else '<p class="warn">成效总结待确认</p>'}
{metric_html}
{award_html}
</div>

{pending_box}
</div></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--md-out")
    ap.add_argument("--html-out")
    a = ap.parse_args()
    try:
        data = json.load(open(a.input, encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        sys.exit(1)
    md = build_md(data)
    html = build_html(data)
    if a.md_out:
        open(a.md_out, "w", encoding="utf-8").write(md)
    if a.html_out:
        open(a.html_out, "w", encoding="utf-8").write(html)
    if not a.md_out and not a.html_out:
        print(md)
    else:
        print(json.dumps({"status": "success", "md": a.md_out, "html": a.html_out}, ensure_ascii=False))


if __name__ == "__main__":
    main()
