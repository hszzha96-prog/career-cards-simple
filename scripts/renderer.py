"""Build portable, self-contained simple job cards without network access."""
from pathlib import Path
import argparse
import hashlib
import html
import json
import re
import sys
from collections import Counter
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'data/project.json').read_text(encoding='utf-8'))
SNAPSHOT_DATE = CONFIG['snapshot_date']
date.fromisoformat(SNAPSHOT_DATE)
SNAPSHOT_DOTTED = SNAPSHOT_DATE.replace('-', '.')
HUB = CONFIG['hub_url']
CSS = (ROOT / 'templates/simple.css').read_text(encoding='utf-8')
JS = (ROOT / 'templates/checklist.js').read_text(encoding='utf-8')
XIAOMI = (ROOT / 'templates/xiaomi-baseline.html').read_text(encoding='utf-8')
BASELINE = json.loads((ROOT / 'templates/xiaomi-baseline.json').read_text(encoding='utf-8'))
CARDS = json.loads((ROOT / 'data/cards.json').read_text(encoding='utf-8'))
EVIDENCE = json.loads((ROOT / 'data/evidence.json').read_text(encoding='utf-8'))
FULL = {item['page_id']: item for item in EVIDENCE}


def baseline_inventory(cards):
    payload = {'cards': cards, 'evidence': EVIDENCE, 'snapshot_date': SNAPSHOT_DATE, 'hub_url': HUB}
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    return digest == BASELINE['inventory_sha256']


def baseline_matches(card):
    payload = {'card': card, 'evidence': FULL[card['page_id']], 'snapshot_date': SNAPSHOT_DATE, 'hub_url': HUB}
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
    return (card['page_id'] == BASELINE['page_id']
            and digest == BASELINE['input_sha256']
            and hashlib.sha256(CSS.encode('utf-8')).hexdigest() == BASELINE['css_sha256']
            and hashlib.sha256(JS.encode('utf-8')).hexdigest() == BASELINE['js_sha256'])

def e(s): return html.escape(str(s),quote=True)
def plain(s): return re.sub(r'[*`]|[🟦🟧🟪🟥]','',str(s)).strip()
def link(url,label): return f'<a href="{e(url)}"'+(' target="_blank" rel="noopener"' if url.startswith('http') else '')+f'>{e(label)}</a>'
def header(title):
    return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><title>{e(title)}</title><style>{CSS}</style></head><body>'
def top(logo='C',index=False):
    nav=('<a href="#candidate">候选</a><a href="#applied">已投</a><a href="#incomplete">待补证据</a><a href="#archive">归档</a>' if index else '<a href="#eligibility">资格核验</a><a href="#match">能力匹配</a><a href="#evidence">项目证据</a><a href="#prep">准备清单</a><a href="#sources">来源</a>')
    return f'<header class="top"><div class="wrap top-inner"><a class="brand" style="color:inherit" href="index.html"><span class="logo" aria-hidden="true">{e(logo)}</span><span>Career Intelligence / 岗位档案</span></a><nav class="nav" aria-label="页面导航">{nav}</nav><button class="print" onclick="window.print()">打印 / 存 PDF</button></div></header>'
def section_start(id,n,en,title,aside=''):
    return f'<section class="section" id="{id}"><div class="section-head"><div><div class="eyebrow">{n:02d} / {e(en)}</div><h2>{e(title)}</h2></div><span class="aside">{e(aside)}</span></div><div class="grid2">'
def kv(rows):return ''.join(f'<div class="kv"><span>{e(r["label"])}</span><strong>{e(r["value"])}</strong></div>' for r in rows)
def source_rows(sources):
    return ''.join(f'<div class="source"><div><strong>{e(s["label"])}</strong><small>{e(s.get("date",SNAPSHOT_DATE))} · {e(s.get("kind","原始来源"))}</small></div>{link(s["url"],"打开 ↗")}</div>' for s in sources)
def sources_for(full):
    seen=set();out=[]
    for s in full['sources']:
        if not s.get('url','').startswith('http') or s['url'] in seen:continue
        seen.add(s['url']);out.append(s)
    return out
def jd_for(full):
    if full['category']=='incomplete':return None
    ss=sources_for(full)
    for s in ss:
        if re.search(r'官方 JD|雇主 JD|岗位 JD',s['label']) and not any(v in s['url'] for v in ['chatgpt.com','mail.google','dropbox.com']):return s['url']
    for s in ss:
        if re.search(r'JD|招聘|岗位详情',s['label']) and any(v in s['url'] for v in ['jobs','careers','career']):return s['url']
    return None

def render(c):
    f=FULL[c['page_id']];url='https://chatgpt.com/space/'+c['page_id'];jd=jd_for(f)
    key=c.get('storage_key', 'career-simple-'+c['page_id']+'-prep-v1')
    kind=c['question_kind']
    doc=header(c['company']+' | '+c['role'])+top(c['company'][0].upper())+'<main class="wrap main">'
    doc+=f'<section class="hero" aria-label="岗位概览"><div><div class="eyebrow">Opportunity intelligence · {e(c["employment"])}</div><h1>{e(c["company"])}<span>{e(c["role"])}</span></h1><p>{e(c["hero"])}</p><div class="hero-meta"><span>⌖ {e(f.get("location","地点待核"))}</span><span>{e(c["employment"])}</span><span>{e(c["short_id"])}</span></div><div class="hero-actions"><a class="btn" href="{e(jd or url)}" target="_blank" rel="noopener">{ "查看原始 JD" if jd else "原始岗位卡"} ↗</a><a class="btn btn-ghost" href="index.html">返回岗位目录</a></div></div><div class="score-area"><div class="ring" id="heroProgress" role="img" aria-label="{e(kind)}完成0题，共5题"><svg viewBox="0 0 120 120" aria-hidden="true"><circle cx="60" cy="60" r="52" fill="none" stroke="#ffffff26" stroke-width="8"/><circle id="heroArc" cx="60" cy="60" r="52" fill="none" stroke="#91dfb7" stroke-width="8" stroke-linecap="round" stroke-dasharray="0 326.73"/></svg><div><div id="heroCount" class="number mono">0</div><div class="outof">/ 5 · {e(kind)}</div></div></div><span class="status-pill">{e(c["pill"])}</span><div class="desc">{e(c["status_label"])}<br>勾选进度保存在本浏览器</div></div></section>'
    doc+='<div class="kpis">'+''.join(f'<div class="kpi"><div class="kpi-label">{e(k["label"])}</div><div class="kpi-val">{e(k["value"])}</div><small>{e(k["note"])}</small></div>' for k in c['kpis'])+'</div>'
    doc+=section_start('eligibility',1,'Eligibility & verification',c['eligibility_title'],f'核验快照 · {SNAPSHOT_DATE} · 非实时状态')
    doc+=f'<article class="card"><h3>岗位与招聘核验</h3>{kv(c["employer"])}<div class="callout">{e(c["employer_note"])}</div></article><article class="card"><h3>个人资格与档期</h3>{kv(c["personal"])}<div class="callout">{e(c["personal_note"])}</div></article></div></section>'
    doc+=section_start('match',2,'Capability & evidence',c['match_title'],'5 个维度 · 保留证据，不作数值评分')
    doc+=f'<article class="card"><h3>{e(c["match_left_title"])}</h3><div class="skills">'
    for d in c['dimensions']:
        doc+=f'<div class="skill"><div class="skill-top"><span>{e(d["name"])}</span><span class="mono">{e(d["status"])}</span></div><div class="track" aria-hidden="true"><div class="fill" style="width:{100 if d["has_evidence"] else 0}%"></div></div><small>{e(d["note"])}</small></div>'
    legend='绿色：找到相关经历；灰色：证据待补。条形不表示分数。' if c['category']!='incomplete' else '岗位身份尚未确认，本页不作 JD 匹配或能力评分。'
    doc+=f'</div><p style="margin-top:16px" class="muted"><small>{legend}</small></p></article><article class="card"><h3>{e(c["match_right_title"])}</h3><div class="table-wrap"><table><thead><tr><th>核对项</th><th>对应证据</th><th>判断</th></tr></thead><tbody>'
    for r in c['matrix']:doc+=f'<tr><td>{e(r["need"])}</td><td>{e(r["evidence"])}</td><td><span class="tag{ " amber" if re.search("待|缺|未",r["verdict"]) else ""}">{e(r["verdict"])}</span></td></tr>'
    doc+='</tbody></table></div></article></div></section>'
    doc+=section_start('evidence',3,'Portfolio evidence',c['projects_title'],'依据个人材料 · 保留贡献边界')
    for i,p in enumerate(c['projects']):
        doc+=f'<article class="card evidence-card"><div class="evidence-label"><div class="evidence-icon" aria-hidden="true">0{i+1}</div><div><h3>{e(p["name"])}</h3><small>{e(p["subtitle"])}</small></div></div><p>{e(p["intro"])}</p><ul class="bullet">'+''.join(f'<li>{e(b)}</li>' for b in p['bullets'])+f'</ul><div class="callout">{e(p["boundary"])}</div>'
        if p['english']:doc+=f'<details class="note"><summary>展开 · 英文表达参考</summary><p class="copy-text" id="project{i}">{e(p["english"])}</p><button class="quiet-btn copy" data-copy="project{i}">复制英文</button><span class="status-msg" aria-live="polite"></span></details>'
        doc+='</article>'
    doc+='</div></section>'
    doc+=section_start('prep',4,'Action & preparation',c['prep_title'],'勾选不改变申请状态')
    doc+='<article class="card"><h3>'+('归档核对' if c['category'] in ['closed','trash'] else '下一步 · 按顺序推进')+'</h3><div class="steps">'
    for i,s in enumerate(c['steps']):
        step_title=re.sub(r'^\d{1,2}\s+','',s['title'])
        doc+=f'<div class="step"><div class="step-num">{i+1}</div><div><strong>{e(step_title)}</strong><p>{e(s["text"])}</p></div></div>'
    doc+=f'</div><details class="note"><summary>展开 · 关键待核项</summary><ul class="bullet">'+''.join(f'<li>{e(g)}</li>' for g in f['gaps'])+'</ul></details></article>'
    doc+=f'<article class="card"><div class="qhead"><h3>{e(kind)} · 清单</h3><strong id="qcount" class="mono" aria-live="polite">0/5</strong></div><div id="qprogress" class="track" role="progressbar" aria-label="{e(kind)}进度" aria-valuemin="0" aria-valuemax="5" aria-valuenow="0"><div id="qfill" class="fill" style="width:0%;transition:width .2s"></div></div>'
    for i,q in enumerate(c['questions']):doc+=f'<label class="question"><input type="checkbox" data-q="{i}"><div><strong><span class="qnum">Q{i+1}</span>{e(q["en"])}</strong><small>{e(q["zh"])}</small></div></label>'
    doc+=f'<div class="actionbar"><span id="savehint">{e(c["question_note"])}</span><button class="quiet-btn" id="reset" type="button">重置清单</button></div></article></div></section>'
    doc+=section_start('sources',5,'Application log & sources','申请记录与原始出处','一岗一条 · 状态沿用原卡')
    doc+=f'<article class="card"><h3>本岗位记录</h3><div class="source"><div><strong>{e(c["company"])} · {e(c["role"])}</strong><small>{e(c["short_id"])}</small><span class="tag">{e(c["status_label"])}</span></div>{link(url,"原卡 ↗")}</div><p style="margin-top:13px">{e(c["application_note"])}</p><div class="callout">{e(c["cv_note"])}</div><p style="margin-top:13px" class="muted"><small>{e(c["dedup_note"])}</small></p><details class="note"><summary>展开 · 原状态文字</summary><p>{e(plain(f["original_status"]))}</p></details></article>'
    ss=sources_for(f)
    primary=[];secondary=[]
    for s in ss:
        if s['url']==url:continue
        if len(primary)<5:primary.append(s)
        else:secondary.append(s)
    doc+='<article class="card"><h3>资料与核验入口</h3>'+source_rows(primary)
    if secondary:doc+='<details class="note"><summary>展开 · 其他原始来源</summary>'+source_rows(secondary)+'</details>'
    notes=[s for s in ss if s.get('note')]
    if notes:doc+='<details class="note"><summary>展开 · 来源核验说明</summary><ul class="bullet">'+''.join(f'<li><strong>{e(s["label"])}</strong>：{e(s["note"])}</li>' for s in notes)+'</ul></details>'
    doc+=f'<div class="source"><div><strong>岗位目录与调度台</strong><small>本地目录用于打开简洁卡；原调度台保留正式状态。</small></div><span>{link("index.html","目录")} · {link(HUB,"调度台 ↗")}</span></div></article></div></section>'
    doc+=f'<footer class="foot"><span>{e(c["company"].upper())} / CAREER INTELLIGENCE · {SNAPSHOT_DOTTED} 核验快照</span><span>简洁版 HTML · 练习仅本地保存 · 原卡保留正式状态</span></footer></main>'
    script=JS.replace('career-xiaomi-A119959-prep-v1',key).replace('面试预练完成',kind+'完成')
    return doc+'<script>'+script+'</script></body></html>'

def build_index(cards):
    counts=Counter(c['category'] for c in cards)
    count=len(cards)
    doc=header('岗位卡 · 简洁版目录')+top('C',True)+'<main class="wrap main">'
    doc+='<section class="hero"><div><div class="eyebrow">Career cards · simple edition</div><h1>岗位卡，简单看。<span>'+str(count)+' 张现有岗位卡 · 简洁版</span></h1><p>沿用已确认的小米版式。选一个岗位，查看资格、经历、准备清单与原始记录。</p><div class="hero-meta"><span>'+SNAPSHOT_DOTTED+' 资料快照</span><span>每岗独立 HTML</span><span>可离线阅读</span></div><div class="hero-actions"><a class="btn" href="#candidate">打开候选清单</a><a class="btn btn-ghost" href="'+HUB+'" target="_blank" rel="noopener">原岗位调度台 ↗</a></div></div><div class="score-area"><div class="ring"><svg viewBox="0 0 120 120" aria-hidden="true"><circle cx="60" cy="60" r="52" fill="none" stroke="#ffffff26" stroke-width="8"/><circle cx="60" cy="60" r="52" fill="none" stroke="#91dfb7" stroke-width="8" stroke-dasharray="326.73 326.73"/></svg><div><div class="number mono">'+str(count)+'</div><div class="outof">张独立岗位卡</div></div></div><span class="status-pill">原状态保留</span><div class="desc">勾选仅作个人准备记录<br>不自动更新申请状态</div></div></section>'
    doc+='<div class="kpis">'+''.join(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-val">{value}</div><small>{note}</small></div>' for label,value,note in [('CANDIDATES · 候选',f"{counts['candidate']} 张",'保留未投候选状态'),('APPLIED · 已投记录',f"{counts['applied']+counts['incomplete']} 张",f"{counts['applied']} 张岗位明确 · {counts['incomplete']} 张细节待补"),('CLOSED · 已结束',f"{counts['closed']} 张",'仅保留历史记录'),('ARCHIVE · 废纸篓',f"{counts['trash']} 张",'保留暂不投决定')])+'</div>'
    groups=[('candidate','候选岗位','先核门槛与档期，再决定推进'),('applied','已投 · 岗位明确','3 张雇主收件回执 · 小米为平台转交' if baseline_inventory(cards) else '保留原卡申请证据与状态'),('incomplete','已投 · 证据待补','本人已投记录保留，先补确切岗位'),('archive','已结束与废纸篓','独立归档，不重新激活')]
    for n,(cat,title,note) in enumerate(groups,1):
        items=[c for c in cards if c['category']==cat or cat=='archive' and c['category'] in ['closed','trash']]
        doc+=f'<section class="section" id="{cat}"><div class="section-head"><div><div class="eyebrow">{n:02d} / {cat}</div><h2>{title}</h2></div><span class="aside">{note}</span></div><article class="card">'
        for c in items:doc+=f'<div class="source"><div><strong>{e(c["company"])} · {e(c["role"])}</strong><small>{e(c["status_label"])} · {e(c["pill"])}</small></div>{link(c["filename"],"打开 HTML ↗")}</div>'
        doc+='</article></section>'
    doc+='<footer class="foot"><span>解压后打开本目录；每张卡也可单独打开。</span><span>简洁版 · 原页面保留正式状态 · 旧版本保留</span></footer></main></body></html>'
    return doc


def build(output):
    """Render the configured inventory to a caller-chosen output directory."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    cards = CARDS
    byid = {c['page_id']: c for c in cards}
    if len(cards) != len(byid) or len(EVIDENCE) != len(FULL) or set(byid) != set(FULL):
        raise ValueError('cards/evidence must have matching, unique page_id values')
    filenames = [c['filename'] for c in cards]
    if len(filenames) != len(set(filenames)):
        raise ValueError('Each job must have a unique filename')
    keys = [c.get('storage_key', 'career-simple-'+c['page_id']+'-prep-v1') for c in cards]
    if any(not re.fullmatch(r'[A-Za-z0-9_.:-]+', key) for key in keys):
        raise ValueError('storage_key may only contain ASCII letters, numbers, _, ., :, and -')
    if len(keys) != len(set(keys)):
        raise ValueError('Each job must have a unique storage_key')
    for c in cards:
        filename = c['filename']
        if Path(filename).name != filename or not filename.endswith('.html') or filename == 'index.html':
            raise ValueError('Unsafe or reserved card filename: '+filename)
        for field, count in [('kpis',4),('employer',5),('personal',5),('dimensions',5),('projects',2),('steps',4),('questions',5)]:
            if len(c[field]) != count:
                raise ValueError(f"{c['company']}: {field} requires {count} entries")
        if filename != FULL[c['page_id']]['filename'] or c['category'] != FULL[c['page_id']]['category']:
            raise ValueError(f"Identity mismatch in evidence for {c['page_id']}")
        if baseline_matches(c):
            content = XIAOMI.replace('<footer class="foot">', '<footer class="foot"><span><a href="index.html">返回岗位目录</a></span>')
        else:
            if c['page_id'] == BASELINE['page_id']:
                print('Xiaomi inputs changed; rendering from current data while preserving its storage key.', file=sys.stderr)
            content = render(c)
        (output / filename).write_text(content, encoding='utf-8')
    (output / 'index.html').write_text(build_index(cards), encoding='utf-8')
    counts = Counter(c['category'] for c in cards)
    readme = f'''岗位卡 · 简洁版（{SNAPSHOT_DATE}）

使用方法
1. 完整解压压缩包。
2. 双击 index.html 打开目录，再选择岗位。
3. 每张 HTML 都包含自身样式与交互，也可单独打开。

共 {len(cards)} 张：{counts['candidate']} 张候选、{counts['applied']} 张岗位明确的已投、{counts['incomplete']} 张已投证据待补、{counts['closed']} 张已结束、{counts['trash']} 张废纸篓。
本包按已确认的小米简洁版制作。已有旧版文件与原 Pages 保留；各岗位卡的简洁版入口与岗位调度台互相对应，正式申请状态以原卡为准。

勾选仅保存在当前浏览器，按岗位分别记录，不改变申请状态。移动文件、换浏览器或清理浏览数据可能使原进度不可见。未沿用旧版复杂工作台的进度。
核验依据为 {SNAPSHOT_DATE} 已收集材料，招聘与邮件状态不是实时更新。来源链接需要联网且可能需要本人登录。
{counts['incomplete']} 张岗位不明确的卡为证据待补版，不作虚构 JD 匹配；已结束与废纸篓不重新激活。

后续岗位卡约定
默认继续沿用本简洁版；只有另外提出网站或界面设计需求时，再另行设计。
保留每岗一条、原始状态、来源、核验日期和真实个人贡献边界。
'''
    (output / '使用说明.txt').write_text(readme, encoding='utf-8')
    return {'cards': len(cards), 'categories': dict(counts), 'directory': str(output)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='Directory for generated HTML and usage notes')
    args = parser.parse_args()
    print(json.dumps(build(args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()
