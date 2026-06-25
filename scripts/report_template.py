# -*- coding: utf-8 -*-
"""리포트 HTML 템플릿. build_report.py가 만든 data dict를 받아 HTML 문자열을 돌려준다."""
import html

def f2(x): return f"{x:.2f}"
esc = html.escape
PUSH_BADGE = '<span class="push">▲ 적극 추진</span>'

def HTML_TEMPLATE(d):
    s = d['summary']; bm = d['bench']

    mx = d['over'][0][1] if d['over'] else 1
    over_html = ""
    for w, c in d['over']:
        pct = round(c / mx * 100)
        over_html += f'<div class="kwrow"><div class="kwname">{esc(w)}</div><div class="kwbar"><div class="bar"><div class="bar-fill" style="width:{pct}%;background:var(--amber)"></div></div></div><div class="kwcnt">{c:,}</div></div>'

    mxp = d['top_count'][0][2] if d['top_count'] else 1
    rankA = ""
    for i, (name, nt, npos, pr, avg, push) in enumerate(d['top_count'], 1):
        pct = round(npos / mxp * 100)
        rankA += f'''<div class="rrow{' is-push' if push else ''}">
          <div class="rnum">{i}</div>
          <div class="rname">{esc(name)} {PUSH_BADGE if push else ''}</div>
          <div class="rbar"><div class="bar"><div class="bar-fill" style="width:{pct}%;background:var(--green)"></div></div></div>
          <div class="rpos">{int(npos):,}</div>
          <div class="rmeta">{f2(pr)}% · ★{f2(avg)}</div>
        </div>'''

    rankB = ""
    for i, (name, nt, npos, pr, avg, push) in enumerate(d['top_ratio'], 1):
        rankB += f'''<tr class="{'is-push' if push else ''}"><td class="bi">{i}</td><td>{esc(name)} {PUSH_BADGE if push else ''}</td>
          <td class="num">{int(nt):,}</td><td class="num pos">{f2(pr)}%</td><td class="num">★{f2(avg)}</td></tr>'''

    cards = ""
    for p in d['products']:
        chips = "".join(
            f'<span class="{"chip sig" if sig else "chip"}">{esc(w)}<i>{c}</i></span>'
            for w, c, sig in p['chips'])
        qs = "".join(f'<blockquote>“{esc(q)}”</blockquote>' for q in p['quotes'])
        ratio_cls = "warn" if p['pos_ratio'] < 85 else "pos"
        cards += f'''<article class="{'card is-push' if p['push'] else 'card'}">
          <header class="card-h">
            <div class="card-top"><span class="cat">{esc(p['cat'])}</span>{PUSH_BADGE if p['push'] else ''}</div>
            <h3>{esc(p['name'])}</h3>
            <div class="card-stats">
              <span class="st"><b>{p['n_pos']:,}</b><small>긍정 후기</small></span>
              <span class="st"><b class="{ratio_cls}">{f2(p['pos_ratio'])}%</b><small>긍정 비율</small></span>
              <span class="st"><b>★{f2(p['avg'])}</b><small>평균 별점</small></span>
            </div>
          </header>
          <div class="chips">{chips}</div>
          <p class="why">{esc(p['note'])}</p>
          <div class="quotes">{qs}</div>
        </article>'''

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
body{{margin:0;background:var(--paper);color:var(--ink);font-family:Pretendard,system-ui,sans-serif;
line-height:1.6;-webkit-font-smoothing:antialiased;font-feature-settings:"tnum";}}
.wrap{{max-width:920px;margin:0 auto;padding:56px 24px 96px}}
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
.bar{{height:9px;background:var(--chip);border-radius:6px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:6px}}
.kwrow{{display:grid;grid-template-columns:96px 1fr 56px;align-items:center;gap:14px;padding:5px 0}}
.kwname{{font-weight:600;font-size:14px}}
.kwcnt{{text-align:right;color:var(--muted);font-size:13px;font-variant-numeric:tabular-nums}}
.rrow{{display:grid;grid-template-columns:26px 1.5fr 1fr 64px 110px;align-items:center;gap:14px;
padding:11px 8px;border-bottom:1px solid var(--line);border-radius:8px}}
.rrow.is-push{{background:var(--green-soft)}}
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
.cards{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:24px}}
.card{{border:1px solid var(--line);border-radius:16px;padding:22px;background:#fff}}
.card.is-push{{border-color:var(--green);box-shadow:0 0 0 1px var(--green) inset}}
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
.legend{{font-size:12px;color:var(--muted);margin:14px 0 0;display:flex;gap:18px;flex-wrap:wrap}}
.legend span{{display:inline-flex;align-items:center;gap:6px}}
.dot{{width:11px;height:11px;border-radius:3px;display:inline-block}}
footer{{margin-top:64px;padding-top:24px;border-top:1px solid var(--line);font-size:12.5px;color:var(--muted);line-height:1.7}}
footer b{{color:var(--ink)}}
@media(max-width:680px){{.band{{grid-template-columns:repeat(2,1fr)}}.cards{{grid-template-columns:1fr}}
.rrow{{grid-template-columns:22px 1fr 64px}}.rrow .rbar,.rrow .rmeta{{display:none}}h1{{font-size:27px}}}}
</style></head>
<body><div class="wrap">

<div class="eyebrow">원룸만들기 · 알파리뷰 분석</div>
<h1>긍정 리뷰가 많은 상품과<br>고객이 만족하는 이유</h1>
<div class="sub">분석 기간 {s['period']} · 자동 생성 리포트</div>
<div class="meta-note">고객 후기 <b>{s['N_cust']:,}건</b> 기준 (전체 {s['N_all']:,}건 중 판매자 작성 후기 제외). 긍정 = 별점 {4}점 이상. 키워드는 자유 텍스트 후기에서만 추출했으며, 정해진 문구를 클릭하는 '빠른리뷰'와 네이버페이 자동 문구는 제외했습니다. 모든 수치는 소수점 2자리 반올림.</div>

<div class="band">
  <div class="cell"><b>{s['N_cust']:,}</b><small>고객 후기 수</small></div>
  <div class="cell"><b class="accent">{f2(s['pos_ratio'])}%</b><small>긍정 비율 (4점+)</small></div>
  <div class="cell"><b>{s['n_prod']:,}</b><small>리뷰 보유 상품</small></div>
  <div class="cell"><b>★{f2(s['avg'])}</b><small>평균 별점</small></div>
</div>

<div class="bench">
  <h4>📊 타 쇼핑몰 대비 객관적 위치</h4>
  <p>업계 벤치마크상 이커머스 상품의 <b>평균 별점은 {bm['ind_avg']}★</b>(≈90% 환산)이고, 좋은 평점대는 4.0~4.7★, 4.75★가 전환율 최상위 '북극성' 기준입니다. 90% 이상이면 최상위로 강한 고객 호응을 뜻합니다.</p>
  <p>원룸만들기 매장 전체는 <b>평균 {f2(s['avg'])}★ · 긍정 {f2(s['pos_ratio'])}%</b>로 업계 평균({bm['ind_avg']}★) 수준입니다. 그 위로 명확히 올라서는 상품을 '적극 추진 후보'로 표시했습니다.</p>
  <div class="crit">적극 추진 기준 (시장 평균 상회): <b>평균 ★{bm['avg']} 이상 + 긍정 비율 {int(bm['ratio'])}% 이상 + 후기 {bm['min_n']}건 이상</b> &nbsp;→ 전체 {s['n_prod']:,}개 상품 중 <b>{bm['n_push']}개</b>가 해당. 아래 <span class="push">▲ 적극 추진</span> 표시.</div>
  <p class="src">출처: PowerReviews(25.4M+ 상품 페이지 분석), Amazon 평점 기준 등 공개 이커머스 벤치마크</p>
</div>

<section>
<h2>전체 긍정 키워드 <span class="tag">긍정 후기에서 가장 자주 언급된 만족 요인</span></h2>
<p class="lead">고객이 어떤 점에 만족하는지를 한눈에. 막대는 해당 키워드가 등장한 긍정 후기 수입니다.</p>
{over_html}
</section>

<section>
<h2>① 긍정 리뷰가 많은 상품 <span class="tag">긍정 후기 절대 수 기준 TOP 12</span></h2>
<p class="lead">잘 팔리고 후기도 많은 핵심 상품. 시장 평균을 상회하는 상품은 <span class="push">▲ 적극 추진</span>으로 강조했습니다.</p>
{rankA}
</section>

<section>
<h2>② 만족도가 가장 높은 상품 <span class="tag">긍정 비율 기준 · 후기 {bm['min_n']}건 이상</span></h2>
<p class="lead">후기 수는 적어도 거의 불만이 없는 '숨은 만족 상품'. <span class="push">▲ 적극 추진</span> 상품은 객관적으로 시장 평균을 분명히 상회해, 판매 확대 시 리스크가 낮습니다.</p>
<table>
<thead><tr><th class="bi">#</th><th>상품명</th><th class="num">후기</th><th class="num">긍정비율</th><th class="num">평균별점</th></tr></thead>
<tbody>{rankB}</tbody>
</table>
</section>

<section>
<h2>③ 상품별 심층 분석 <span class="tag">카테고리 · 만족 이유 · 실제 고객의 말</span></h2>
<p class="lead">긍정 후기 상위 {len(d['products'])}개 상품. 각 카드에 카테고리를 표시하고, 그 카테고리의 핵심 긍정 키워드를 <b style="color:#9a5a08">진한 색</b>으로 강조했습니다.</p>
<div class="legend">
  <span><span class="dot" style="background:var(--amber-soft);border:1px solid #F1D9B8"></span> 카테고리 핵심 긍정 키워드</span>
  <span><span class="dot" style="background:var(--chip)"></span> 일반 키워드</span>
  <span><span class="push" style="padding:1px 7px">▲ 적극 추진</span> 시장 평균 상회</span>
</div>
<div class="cards">{cards}</div>
</section>

<footer>
<b>분석 방법</b><br>
· 데이터: 알파리뷰 내보내기 CSV ({s['N_all']:,}건), 분석 기간 {s['period']}<br>
· 긍정 정의: 별점 4점 이상 (5점 비중이 커 긍정 쏠림이 큼)<br>
· 제외 처리: 판매자(관리자) 작성 후기, 클릭형 '빠른리뷰', 네이버페이 자동 삽입 문구<br>
· 키워드: 한국어 형태소 분석(명사·형용사) 추출, 후기당 중복 1회 집계, 동의어 통합, 부정어는 카테고리 키워드에서 제외<br>
· 적극 추진 기준: 평균 ★{bm['avg']}+ · 긍정 {int(bm['ratio'])}%+ · 후기 {bm['min_n']}건+ (업계 평균 {bm['ind_avg']}★ / 90% 상회) · 모든 수치 소수점 2자리 반올림
</footer>

</div></body></html>'''
