# -*- coding: utf-8 -*-
"""리포트 HTML 템플릿. build_report.py가 만든 data dict를 받아 HTML 문자열을 돌려준다."""
import html

def f2(x): return f"{x:.2f}"
esc = html.escape
PUSH_BADGE = '<span class="push">▲ 적극 추진</span>'
WATCH_BADGE = '<span class="watch">△ 추진 검토</span>'
def badge(push, watch):
    return PUSH_BADGE if push else (WATCH_BADGE if watch else '')

def render_rec(rec):
    if not rec: return ""
    cats = rec.get("categories", [])
    sims = rec.get("similar", [])
    grps = rec.get("groups", [])

    # (1) 카테고리 추천 — 행 클릭 시 해당 카테고리 상품이 표 컬럼에 맞춰 펼쳐짐
    cat_rows = ""
    for gi, c in enumerate(cats):
        cat_rows += (f'<tr class="catrow" onclick="onCatRow(this)" data-grp="{gi}"><td>{esc(c["cat"])}</td>'
                     f'<td class="num">{c["n_products"]:,}</td>'
                     f'<td class="num">{c["n_reviews"]:,}</td><td class="num pos">{f2(c["pos_ratio"])}%</td>'
                     f'<td class="num">★{f2(c["avg"])}</td></tr>')
        for pr in c.get("products", []):
            cat_rows += (f'<tr class="prow prow-{gi}"><td colspan="2" class="pname">{esc(pr["name"])}</td>'
                         f'<td class="num">{pr["n"]:,}</td><td class="num pos">{f2(pr["pos_ratio"])}%</td>'
                         f'<td class="num">★{f2(pr["avg"])}</td></tr>')

    # (2) 유사 상품 추천
    sim_html = ""
    for s in sims:
        items = ""
        for it in s["items"]:
            shared = " · ".join(esc(w) for w in it["shared"])
            items += (f'<li><b>{esc(it["name"])}</b> '
                      f'<span class="rmeta">긍정 {f2(it["pos_ratio"])}% · ★{f2(it["avg"])} · 후기 {it["n"]:,}</span>'
                      f'<br><span class="shared">공통 키워드: {shared}</span></li>')
        sim_html += (f'<div class="simblock"><div class="anchor">‘{esc(s["anchor"])}’ 와 비슷한 강점의 상품</div>'
                     f'<ul class="simlist">{items}</ul></div>')

    # (2-b) 같은 카테고리 유사 상품
    simcat_html = ""
    for s in rec.get("similar_cat", []):
        items = ""
        for it in s["items"]:
            shared = " · ".join(esc(w) for w in it["shared"]) if it["shared"] else "같은 카테고리"
            items += (f'<li><b>{esc(it["name"])}</b> '
                      f'<span class="rmeta">긍정 {f2(it["pos_ratio"])}% · ★{f2(it["avg"])} · 후기 {it["n"]:,}</span>'
                      f'<br><span class="shared">공통 키워드: {shared}</span></li>')
        simcat_html += (f'<div class="simblock"><div class="anchor">‘{esc(s["anchor"])}’ 와 같은 카테고리'
                        f'(<b>{esc(s["cat"])}</b>)의 유사 상품</div>'
                        f'<ul class="simlist">{items}</ul></div>')

    # (3) 상품군 추천 — 키워드 > 카테고리 > 상품
    grp_html = ""
    for g in grps:
        cat_blocks = ""
        for cb in g.get("cats", []):
            names = " · ".join(f'{esc(it["name"])} ({f2(it["pos_ratio"])}%)' for it in cb["items"])
            cat_blocks += (f'<div class="grpcat"><span class="grpcatname">{esc(cb["cat"])}'
                           f'<i>{cb["n"]}개</i></span><span class="grpcatitems">{names}</span></div>')
        grp_html += (f'<div class="grpblock"><div class="grphead"><span class="grpkw">{esc(g["keyword"])}</span>'
                     f'<span class="grpcnt">강점 상품 {g["n_products"]}개</span></div>'
                     f'<div class="grpcats">{cat_blocks}</div></div>')

    return f'''<section>
<h2 id="sec4">④ 판매 추천 <span class="tag">리뷰·키워드 기반 · 무엇을 더 밀지</span></h2>
<p class="lead">후기 20건 이상 상품을 대상으로, 만족도와 키워드를 분석해 판매를 확대할 후보를 제안합니다. 참고용 데이터이며 최종 판단은 운영 맥락과 함께 보세요.</p>

<h3 class="rec-h">카테고리 추천 <span class="rtag">만족도 높은 카테고리 · 행을 클릭하면 상품 목록</span></h3>
<table><thead><tr><th>카테고리</th><th class="num help" title="후기 20건 이상인 상품의 개수">상품수</th><th class="num help" title="해당 상품들의 전체 후기 수 (긍정·부정 모두 포함)">후기</th><th class="num help" title="전체 후기 중 별점 4점 이상(긍정) 비율">긍정비율</th><th class="num help" title="해당 상품들의 평균 별점">평균별점</th></tr></thead>
<tbody>{cat_rows}</tbody></table>

<h3 class="rec-h">유사 상품 추천 <span class="rtag">인기 상품과 강점이 겹치는 상품</span></h3>
<div class="simwrap">{sim_html}</div>

<h3 class="rec-h">같은 카테고리 유사 상품 <span class="rtag">인기 상품과 같은 카테고리 내 유사 상품</span></h3>
<div class="simwrap">{simcat_html}</div>

<h3 class="rec-h">상품군 추천 <span class="rtag">같은 강점을 공유하는 상품 묶음</span></h3>
<div class="grpwrap">{grp_html}</div>
</section>'''

def HTML_TEMPLATE(d):
    s = d['summary']; bm = d['bench']

    mx = d['over'][0][1] if d['over'] else 1
    over_html = ""
    for w, c in d['over']:
        pct = round(c / mx * 100)
        over_html += f'<div class="kwrow"><div class="kwname">{esc(w)}</div><div class="kwbar"><div class="bar"><div class="bar-fill" style="width:{pct}%;background:var(--amber)"></div></div></div><div class="kwcnt">{c:,}</div></div>'

    mxp = d['top_count'][0][2] if d['top_count'] else 1
    rankA = ""
    for i, (name, nt, npos, pr, avg, push, watch) in enumerate(d['top_count'], 1):
        pct = round(npos / mxp * 100)
        cls = ' is-push' if push else (' is-watch' if watch else '')
        rankA += f'''<div class="rrow{cls}">
          <div class="rnum">{i}</div>
          <div class="rname">{esc(name)} {badge(push, watch)}</div>
          <div class="rbar"><div class="bar"><div class="bar-fill" style="width:{pct}%;background:var(--green)"></div></div></div>
          <div class="rpos">{int(npos):,}</div>
          <div class="rmeta">{f2(pr)}% · ★{f2(avg)}</div>
        </div>'''

    rankB = ""
    for i, (name, nt, npos, pr, avg, push, watch) in enumerate(d['top_ratio'], 1):
        cls = 'is-push' if push else ('is-watch' if watch else '')
        rankB += f'''<tr class="{cls}" data-n="{int(nt)}" data-ratio="{pr}" data-avg="{avg}"><td class="bi rk">{i}</td><td>{esc(name)} {badge(push, watch)}</td>
          <td class="num">{int(nt):,}</td><td class="num pos">{f2(pr)}%</td><td class="num">★{f2(avg)}</td></tr>'''

    cards = ""
    import json as _json
    for idx, p in enumerate(d['products']):
        chips = "".join(
            f'<span class="{"chip sig" if sig else "chip"}">{esc(w)}<i>{c}</i></span>'
            for w, c, sig in p['chips'])
        qlist = p.get('quotes', [])
        # 앞 2개는 기본 노출, 나머지(최대 10)는 숨김(.extra)
        qhtml = ""
        for qi, q in enumerate(qlist):
            cls = "qt" if qi < 2 else "qt extra"
            qhtml += f'<blockquote class="{cls}">“{esc(q)}”</blockquote>'
        dls = p.get('downloads', [])
        more_avail = p.get('n_total', 0) > len(qlist)   # 표시분보다 실제 후기가 더 많으면 다운로드 제공
        btn = ""
        if len(qlist) > 2:
            btn += (f'<button class="morebtn" data-idx="{idx}" onclick="onToggle(this)">'
                    f'더보기 (+{len(qlist)-2})</button>')
        if more_avail and dls:
            dl_json = _json.dumps(dls, ensure_ascii=False).replace('<', '\\u003c')
            btn += (f'<button class="dlbtn" data-idx="{idx}" data-name="{esc(p["name"])}" '
                    f'onclick="downloadReviews(this)">리뷰 내려받기 ({len(dls)}개)</button>'
                    f'<script type="application/json" id="dl-{idx}">{dl_json}</script>')
        ratio_cls = "warn" if p['pos_ratio'] < 85 else "pos"
        cards += f'''<article class="{'card is-push' if p['push'] else ('card is-watch' if p.get('watch') else 'card')}">
          <header class="card-h">
            <div class="card-top"><span class="cat">{esc(p['cat'])}</span>{badge(p['push'], p.get('watch'))}</div>
            <h3>{esc(p['name'])}</h3>
            <div class="card-stats">
              <span class="st"><b>{p['n_pos']:,}</b><small>긍정 후기</small></span>
              <span class="st"><b class="{ratio_cls}">{f2(p['pos_ratio'])}%</b><small>긍정 비율</small></span>
              <span class="st"><b>★{f2(p['avg'])}</b><small>평균 별점</small></span>
            </div>
          </header>
          <div class="chips">{chips}</div>
          <p class="why">{esc(p['note'])}</p>
          <div class="quotes" data-card="{idx}">{qhtml}</div>
          {btn}
        </article>'''

    # 추천 섹션(④) HTML
    rec = d.get('rec', {})
    rec_html = render_rec(rec)

    return f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>긍정 리뷰 분석 · 원룸만들기</title>
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" rel="stylesheet">
<style>
:root{{--paper:#FAF9F6;--ink:#1B1A17;--muted:#6E6B63;--amber:#D98313;--amber-soft:#FBEFDD;
--green:#2F7A57;--green-soft:#E6F1EA;--warn:#B85638;--line:#E7E3DA;--chip:#F1EEE6;}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:Pretendard,system-ui,sans-serif;
line-height:1.6;-webkit-font-smoothing:antialiased;font-feature-settings:"tnum";
word-break:keep-all;overflow-wrap:break-word;}}
.wrap{{max-width:1140px;margin:0 auto;padding:56px 32px 96px}}
.eyebrow{{font-size:13px;letter-spacing:.14em;color:var(--amber);font-weight:700;text-transform:uppercase}}
h1{{font-size:34px;font-weight:800;letter-spacing:-.02em;margin:.3em 0 .1em;line-height:1.2}}
.sub{{color:var(--muted);font-size:15px;margin-bottom:8px}}
.meta-note{{font-size:13px;color:var(--muted);border-left:3px solid var(--line);padding:6px 0 6px 14px;margin-top:18px}}
section{{margin-top:56px}}
h2{{font-size:20px;font-weight:800;letter-spacing:-.01em;margin:0 0 4px;display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}}
h2 .tag{{font-size:13px;font-weight:600;color:var(--muted)}}
.lead{{color:var(--muted);font-size:14px;margin:0 0 22px}}
.band{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);
border:1px solid var(--line);border-radius:14px;overflow:hidden;margin-top:28px}}
.band .cell{{background:var(--paper);padding:20px 18px}}
.band b{{display:block;font-size:28px;font-weight:800;letter-spacing:-.02em}}
.band small{{color:var(--muted);font-size:13px}}
.band .accent{{color:var(--green)}}
.bench{{margin-top:22px;border:1px solid var(--line);border-radius:14px;padding:20px 22px;background:#fff}}
.bench h4{{margin:0 0 10px;font-size:14.5px;font-weight:800}}
.bench p{{margin:0 0 8px;font-size:13.5px;line-height:1.7;color:#33312C}}
.bench .crit{{margin-top:12px;padding:11px 14px;background:var(--green-soft);border-radius:10px;font-size:13px;color:#1f5840}}
.bench .crit b{{color:var(--green)}}
.bench .src{{font-size:11.5px;color:var(--muted);margin-top:10px}}
.push{{display:inline-block;background:var(--green);color:#fff;font-size:11px;font-weight:700;
padding:2px 8px;border-radius:20px;vertical-align:middle;white-space:nowrap;letter-spacing:.02em}}
.watch{{display:inline-block;background:var(--amber);color:#fff;font-size:11px;font-weight:700;
padding:2px 8px;border-radius:20px;vertical-align:middle;white-space:nowrap;letter-spacing:.02em}}
.bar{{height:9px;background:var(--chip);border-radius:6px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:6px}}
.kwrow{{display:grid;grid-template-columns:96px 1fr 56px;align-items:center;gap:14px;padding:5px 0}}
.kwgrid{{display:grid;grid-template-columns:1fr 1fr;gap:0 44px}}
.kwname{{font-weight:600;font-size:14px}}
.kwcnt{{text-align:right;color:var(--muted);font-size:13px;font-variant-numeric:tabular-nums}}
.rrow{{display:grid;grid-template-columns:26px 1.5fr 1fr 64px 110px;align-items:center;gap:14px;
padding:11px 8px;border-bottom:1px solid var(--line);border-radius:8px}}
.rrow.is-push{{background:var(--green-soft)}}
.rrow.is-watch{{background:#FCE6C8}}
.rnum{{font-weight:800;color:var(--muted);font-size:14px;text-align:center}}
.rname{{font-weight:600;font-size:14.5px}}
.rpos{{text-align:right;font-weight:800;font-variant-numeric:tabular-nums}}
.rmeta{{text-align:right;color:var(--muted);font-size:12.5px;font-variant-numeric:tabular-nums}}
table{{width:100%;border-collapse:separate;border-spacing:0;font-size:14px}}
th,td{{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left}}
th{{font-size:12px;color:var(--muted);font-weight:700;letter-spacing:.03em}}
td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}
td.bi{{color:var(--muted);font-weight:700;width:30px}}
td.pos{{color:var(--green);font-weight:700}}
tr.is-push td{{background:var(--green-soft)}}
tr.is-watch td{{background:#FCE6C8}}
.cards{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:24px}}
.card{{border:1px solid var(--line);border-radius:16px;padding:22px;background:#fff}}
.card.is-push{{border-color:var(--green);box-shadow:0 0 0 1px var(--green) inset}}
.card.is-watch{{border-color:var(--amber);box-shadow:0 0 0 1px var(--amber) inset}}
.card-top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;gap:8px}}
.cat{{display:inline-block;border:1px solid var(--line);color:var(--muted);font-size:11.5px;
font-weight:700;padding:2px 9px;border-radius:20px;background:var(--paper)}}
.card-h h3{{font-size:16.5px;font-weight:800;margin:0 0 14px;letter-spacing:-.01em}}
.card-stats{{display:flex;gap:18px;margin-bottom:16px}}
.st{{display:flex;flex-direction:column}}
.st b{{font-size:19px;font-weight:800;line-height:1.1;font-variant-numeric:tabular-nums}}
.st small{{color:var(--muted);font-size:11.5px;margin-top:2px}}
.pos{{color:var(--green)}} .warn{{color:var(--warn)}}
.chips{{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:14px}}
.chip{{background:var(--chip);border-radius:8px;padding:4px 9px;font-size:12.5px;font-weight:600;color:#5a574f}}
.chip i{{color:var(--muted);font-style:normal;font-weight:500;margin-left:5px;font-size:11px}}
.chip.sig{{background:var(--amber-soft);color:#9a5a08;border:1px solid #F1D9B8}}
.chip.sig i{{color:#b9802f}}
.why{{font-size:13.5px;line-height:1.7;margin:0 0 14px;color:#33312C}}
blockquote{{margin:8px 0 0;padding:9px 13px;background:var(--chip);border-radius:0 10px 10px 0;
border-left:3px solid var(--amber);font-size:12.5px;color:#4A4842;line-height:1.55}}
.qt.extra{{display:none}}
.morebtn{{margin-top:10px;font-size:12px;font-weight:700;color:#6E6B63;background:#fff;
border:1px solid var(--line);border-radius:8px;padding:6px 12px;cursor:pointer}}
.morebtn:hover{{border-color:var(--amber);color:#9a5a08}}
.dlbtn{{margin:10px 0 0 8px;font-size:12px;font-weight:700;color:#9a5a08;background:var(--amber-soft);
border:1px solid #F1D9B8;border-radius:8px;padding:6px 12px;cursor:pointer}}
.dlbtn:hover{{background:#F6E4C8}}
tr.catrow{{cursor:pointer}}
tr.catrow:hover td{{background:var(--amber-soft)}}
tr.catrow td:first-child::before{{content:'▸';color:var(--amber);font-size:11px;margin-right:7px;display:inline-block}}
tr.catrow.open td:first-child::before{{content:'▾'}}
tr.prow{{display:none;background:#FbF9F4}}
tr.prow>td{{padding:6px 14px;font-size:12px;color:#4A4842;border-bottom:1px solid #EFEAE0}}
tr.prow .pname{{padding-left:30px;font-weight:600}}
tr.prow .pname::before{{content:'·';color:var(--amber);margin-right:8px}}
th.help{{cursor:help;text-decoration:underline dotted #C9C2B4;text-underline-offset:3px}}
th.sortable{{cursor:pointer;user-select:none;white-space:nowrap}}
th.sortable:hover{{color:var(--amber)}}
.sarr{{font-size:10px;color:var(--amber)}}
.sidenav{{position:fixed;right:16px;top:50%;transform:translateY(-50%);display:flex;flex-direction:column;gap:9px;z-index:50}}
.sidenav a{{display:flex;align-items:center;gap:9px;padding:7px 15px 7px 8px;background:rgba(255,255,255,.96);
border:1px solid var(--line);border-radius:24px;box-shadow:0 1px 5px rgba(0,0,0,.07);
text-decoration:none;white-space:nowrap;transition:border-color .15s}}
.sidenav a b{{display:flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;
background:var(--amber-soft);color:var(--amber);font-size:13px;font-weight:800;flex:none}}
.sidenav a .lbl{{font-size:12px;font-weight:700;color:#4A4842}}
.sidenav a:hover{{border-color:var(--amber)}}
.sidenav a:hover .lbl{{color:#9a5a08}}
h2[id]{{scroll-margin-top:20px}}
@media(max-width:1300px){{.sidenav{{display:none}}}}
.rec-h{{font-size:15px;font-weight:800;margin:26px 0 10px;display:flex;align-items:baseline;gap:8px}}
.rec-h .rtag{{font-size:12px;font-weight:600;color:var(--muted)}}
.simwrap{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.simblock{{border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:#fff}}
.anchor{{font-size:13px;font-weight:800;margin-bottom:8px;color:#33312C}}
.simlist{{margin:0;padding-left:18px;font-size:12.5px;line-height:1.7}}
.simlist li{{margin-bottom:7px}}
.shared{{color:#9a5a08;font-size:11.5px}}
.simlist .rmeta{{color:var(--muted);font-size:11.5px;font-variant-numeric:tabular-nums}}
.grpwrap{{display:flex;flex-direction:column;gap:10px}}
.grpblock{{border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:#fff}}
.grphead{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}
.grpkw{{background:var(--amber-soft);color:#9a5a08;border:1px solid #F1D9B8;border-radius:8px;
padding:3px 10px;font-size:13px;font-weight:700}}
.grpcnt{{font-size:11.5px;color:var(--muted)}}
.grpcats{{display:flex;flex-direction:column;gap:6px}}
.grpcat{{display:grid;grid-template-columns:110px 1fr;gap:10px;align-items:baseline;
padding:5px 0;border-top:1px solid #F0ECE3}}
.grpcatname{{font-size:12px;font-weight:700;color:#33312C}}
.grpcatname i{{font-style:normal;color:var(--muted);font-weight:500;margin-left:5px;font-size:11px}}
.grpcatitems{{font-size:12px;color:#4A4842;line-height:1.6}}
.legend{{font-size:12px;color:var(--muted);margin:14px 0 0;display:flex;gap:18px;flex-wrap:wrap}}
.legend span{{display:inline-flex;align-items:center;gap:6px}}
.dot{{width:11px;height:11px;border-radius:3px;display:inline-block}}
footer{{margin-top:64px;padding-top:24px;border-top:1px solid var(--line);font-size:12.5px;color:var(--muted);line-height:1.7}}
footer b{{color:var(--ink)}}
@media(max-width:680px){{.band{{grid-template-columns:repeat(2,1fr)}}.cards{{grid-template-columns:1fr}}.simwrap{{grid-template-columns:1fr}}.kwgrid{{grid-template-columns:1fr}}
.rrow{{grid-template-columns:22px 1fr 64px}}.rrow .rbar,.rrow .rmeta{{display:none}}h1{{font-size:27px}}}}
</style></head>
<body><div class="wrap">

<div class="eyebrow">원룸만들기 · 고객 리뷰 분석</div>
<h1>긍정 리뷰가 많은 상품과<br>고객이 만족하는 이유</h1>
<div class="sub">분석 기간 {s['period']} · 해당 기간 작성 리뷰 기준</div>
<div class="meta-note">선택 기간 내 고객 후기 <b>{s['N_cust']:,}건</b> 기준 (판매자 작성 후기 제외). 긍정 = 별점 {4}점 이상. 키워드는 자유 텍스트 후기에서만 추출했으며, 정해진 문구를 클릭하는 '빠른리뷰'와 네이버페이 자동 문구는 제외했습니다. 모든 수치는 소수점 2자리 반올림.</div>

<div class="band">
  <div class="cell"><b>{s['N_cust']:,}</b><small>고객 후기 수</small></div>
  <div class="cell"><b class="accent">{f2(s['pos_ratio'])}%</b><small>긍정 비율 (4점+)</small></div>
  <div class="cell"><b>{s['n_prod']:,}</b><small>리뷰 보유 상품</small></div>
  <div class="cell"><b>★{f2(s['avg'])}</b><small>평균 별점</small></div>
</div>

<div class="bench">
  <h4>📊 타 쇼핑몰 대비 객관적 위치</h4>
  <p>업계 벤치마크상 이커머스 상품의 <b>평균 별점은 {bm['ind_avg']}★</b>(≈90% 환산)입니다.<br>평점이 4.0~4.7★ 구간일 때 실제 구매로 이어지는 비율(전환율)이 가장 높게 나오는 경향이 있고, 90% 이상이면 최상위로 강한 고객 호응을 뜻합니다.<br>(별점이 무조건 높다고 좋은 건 아니며, 5.0★처럼 너무 완벽하면 오히려 신뢰도가 떨어지기도 합니다.)</p>
  <p>원룸만들기 매장 전체는 <b>평균 {f2(s['avg'])}★ · 긍정 {f2(s['pos_ratio'])}%</b>로 업계 평균({bm['ind_avg']}★) 수준입니다.<br>그 위로 올라서는 상품을 두 단계('적극 추진' / '추진 검토')로 표시했습니다.</p>
  <div class="crit"><span class="push">▲ 적극 추진</span> <b>평균 ★{bm['avg']} 이상 + 긍정 {int(bm['ratio'])}% 이상 + 후기 {bm['min_n']}건 이상</b> → 전체 {s['n_prod']:,}개 중 <b>{bm['n_push']}개</b><br><span class="watch">△ 추진 검토</span> <b>평균 ★{bm['watch_avg']} 이상 + 긍정 {int(bm['watch_ratio'])}% 이상 + 후기 {bm['min_n']}건 이상</b> (적극 추진 제외) → <b>{bm['n_watch']}개</b></div>
  <p class="src">출처: PowerReviews(25.4M+ 상품 페이지 분석), Amazon 평점 기준 등 공개 이커머스 벤치마크</p>
</div>

<section>
<h2>전체 긍정 키워드 <span class="tag">긍정 후기에서 가장 자주 언급된 만족 요인</span></h2>
<p class="lead">고객이 어떤 점에 만족하는지를 한눈에. 막대는 해당 키워드가 등장한 긍정 후기 수입니다.</p>
<div class="kwgrid">{over_html}</div>
</section>

<section>
<h2 id="sec1">① 긍정 리뷰가 많은 상품 <span class="tag">긍정 후기 절대 수 기준 TOP 12</span></h2>
<p class="lead">잘 팔리고 후기도 많은 핵심 상품. 시장 평균을 상회하는 상품은 <span class="push">▲ 적극 추진</span>으로 강조했습니다.</p>
{rankA}
</section>

<section>
<h2 id="sec2">② 만족도가 가장 높은 상품 <span class="tag">긍정 비율 기준 · 후기 {bm['min_n']}건 이상</span></h2>
<p class="lead">후기 수는 적어도 거의 불만이 없는 '숨은 만족 상품'. <span class="push">▲ 적극 추진</span> 상품은 객관적으로 시장 평균을 분명히 상회해, 판매 확대 시 리스크가 낮습니다.</p>
<table id="tbl-sat">
<thead><tr><th class="bi">#</th><th>상품명</th><th class="num sortable" onclick="sortTable(this,'n')">후기 <span class="sarr"></span></th><th class="num sortable" data-dir="desc" onclick="sortTable(this,'ratio')">긍정비율 <span class="sarr"> ▼</span></th><th class="num sortable" onclick="sortTable(this,'avg')">평균별점 <span class="sarr"></span></th></tr></thead>
<tbody>{rankB}</tbody>
</table>
</section>

<section>
<h2 id="sec3">③ 상품별 심층 분석 <span class="tag">카테고리 · 만족 이유 · 실제 고객의 말</span></h2>
<p class="lead">긍정 후기 상위 {len(d['products'])}개 상품. 각 카드에 카테고리를 표시하고, 그 카테고리의 핵심 긍정 키워드를 <b style="color:#9a5a08">진한 색</b>으로 강조했습니다.</p>
<div class="legend">
  <span><span class="dot" style="background:var(--amber-soft);border:1px solid #F1D9B8"></span> 카테고리 핵심 긍정 키워드</span>
  <span><span class="dot" style="background:var(--chip)"></span> 일반 키워드</span>
  <span><span class="push" style="padding:1px 7px">▲ 적극 추진</span> 시장 평균 분명히 상회</span>
  <span><span class="watch" style="padding:1px 7px">△ 추진 검토</span> 그다음 우수</span>
</div>
<div class="cards">{cards}</div>
</section>

{rec_html}

<footer>
<b>분석 방법</b><br>
· 데이터: 카페24 리뷰 데이터 연동 (게시판 API 자동 수집, {s['N_all']:,}건), 분석 기간 {s['period']}<br>
· 긍정 정의: 별점 4점 이상 (5점 비중이 커 긍정 쏠림이 큼)<br>
· 제외 처리: 판매자(관리자) 작성 후기, 클릭형 '빠른리뷰', 네이버페이 자동 삽입 문구, 본문 HTML 태그<br>
· 키워드: 한국어 형태소 분석(명사·형용사) 추출, 후기당 중복 1회 집계, 동의어 통합, 부정어는 카테고리 키워드에서 제외<br>
· 적극 추진: 평균 ★{bm['avg']}+ · 긍정 {int(bm['ratio'])}%+ · 후기 {bm['min_n']}건+ / 추진 검토: 평균 ★{bm['watch_avg']}+ · 긍정 {int(bm['watch_ratio'])}%+ · 후기 {bm['min_n']}건+ (업계 평균 {bm['ind_avg']}★ / 90%) · 모든 수치 소수점 2자리 반올림<br>
· 추천: 후기 20건 이상 상품 대상. 유사 상품=키워드 자카드 유사도, 카테고리/상품군=만족도 기준 (참고용)
</footer>

<nav class="sidenav" aria-label="섹션 바로가기">
  <a href="#sec1"><b>①</b><span class="lbl">긍정 많은 상품</span></a>
  <a href="#sec2"><b>②</b><span class="lbl">만족도 높은 상품</span></a>
  <a href="#sec3"><b>③</b><span class="lbl">상품별 심층 분석</span></a>
  <a href="#sec4"><b>④</b><span class="lbl">판매 추천</span></a>
</nav>
<script>
function onToggle(btn){{
  var card = btn.closest('article');
  var extras = card.querySelectorAll('.quotes .qt.extra');
  var expanded = btn.getAttribute('data-expanded') === '1';
  if(!expanded){{
    extras.forEach(function(e){{ e.style.display='block'; }});
    btn.setAttribute('data-expanded','1');
    btn.textContent = '접기';
  }} else {{
    extras.forEach(function(e){{ e.style.display='none'; }});
    btn.setAttribute('data-expanded','0');
    btn.textContent = '더보기 (+' + extras.length + ')';
  }}
}}
function sortTable(th, key){{
  var table = th.closest('table');
  var tbody = table.querySelector('tbody');
  var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
  var dir = th.getAttribute('data-dir') === 'desc' ? 'asc' : 'desc';
  table.querySelectorAll('th.sortable').forEach(function(h){{
    h.removeAttribute('data-dir'); var a = h.querySelector('.sarr'); if(a) a.textContent='';
  }});
  th.setAttribute('data-dir', dir);
  var arrow = th.querySelector('.sarr'); if(arrow) arrow.textContent = dir==='desc' ? ' ▼' : ' ▲';
  rows.sort(function(a,b){{
    var va = parseFloat(a.getAttribute('data-'+key)), vb = parseFloat(b.getAttribute('data-'+key));
    return dir==='desc' ? vb-va : va-vb;
  }});
  rows.forEach(function(r,i){{ tbody.appendChild(r); var rk=r.querySelector('.rk'); if(rk) rk.textContent=(i+1); }});
}}
function onCatRow(row){{
  var grp = row.getAttribute('data-grp');
  var rows = document.querySelectorAll('.prow-'+grp);
  var open = row.classList.contains('open');
  rows.forEach(function(r){{ r.style.display = open ? 'none' : 'table-row'; }});
  row.classList.toggle('open', !open);
}}
function downloadReviews(btn){{
  var idx = btn.getAttribute('data-idx');
  var name = btn.getAttribute('data-name') || 'reviews';
  var el = document.getElementById('dl-'+idx);
  if(!el){{ return; }}
  var rows;
  try {{ rows = JSON.parse(el.textContent); }} catch(e){{ alert('리뷰 데이터를 읽지 못했습니다.'); return; }}
  var NL = String.fromCharCode(10), BOM = String.fromCharCode(0xFEFF);
  function cell(v){{ return '"' + String(v==null?'':v).replace(/"/g,'""') + '"'; }}
  var lines = [['별점','작성일','리뷰내용'].join(',')];
  rows.forEach(function(r){{ lines.push([cell(r.rating), cell(r.date), cell(r.content)].join(',')); }});
  var csv = BOM + lines.join(NL);
  var blob = new Blob([csv], {{type:'text/csv;charset=utf-8;'}});
  var fname = name.replace(/[^0-9A-Za-z가-힣]+/g,'_') + '_리뷰.csv';
  if(window.navigator && window.navigator.msSaveOrOpenBlob){{ window.navigator.msSaveOrOpenBlob(blob, fname); return; }}
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url; a.download = fname; a.style.display='none';
  document.body.appendChild(a); a.click();
  setTimeout(function(){{ document.body.removeChild(a); URL.revokeObjectURL(url); }}, 120);
}}
</script>

</div></body></html>'''
