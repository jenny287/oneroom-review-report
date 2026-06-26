#!/usr/bin/env python3
"""
build_site.py : 여러 기간(프리셋 + 월별)을 한 번에 생성하고
                각 페이지 상단에 기간/월 전환 버튼 메뉴를 끼워 site/ 폴더에 출력.

사용법:  python scripts/build_site.py <공개CSV_URL 또는 파일경로> <출력폴더>
예:      python scripts/build_site.py "$REVIEW_CSV_URL" site

설정값(기간 프리셋, 월별 개월 수)은 아래 상단에서 조정.
"""
import sys, os, re
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_report_db as core   # 분석/렌더 로직 재사용

# ── 설정 ──
PRESETS = [                      # (파일명, 라벨, days)  days=0 → 전체
    ("index.html", "최근 90일", 90),   # 기본 페이지
    ("p30.html",   "최근 30일", 30),
    ("p180.html",  "최근 6개월", 180),
    ("pall.html",  "전체", 0),
]
MONTHS_BACK = 12                 # 월별 버튼: 최근 N개월

def month_pages(latest: pd.Timestamp, earliest: pd.Timestamp):
    """데이터 범위 내에서, 최신월 기준 최근 MONTHS_BACK개월만 (파일명,라벨,start,end) 생성."""
    out = []
    y, m = latest.year, latest.month
    floor = pd.Timestamp(year=earliest.year, month=earliest.month, day=1)
    for _ in range(MONTHS_BACK):
        start = pd.Timestamp(year=y, month=m, day=1)
        if start < floor:
            break   # 데이터 없는 과거월은 생성하지 않음
        end = (start + pd.offsets.MonthEnd(1))
        label = f"{y}-{m:02d}"
        out.append((f"m{label}.html", label, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")))
        m -= 1
        if m == 0: y -= 1; m = 12
    return out

def nav_html(active_file: str, month_list):
    """상단 기간/월 버튼 메뉴 HTML."""
    def btn(file, label):
        cls = "navbtn active" if file == active_file else "navbtn"
        return f'<a class="{cls}" href="{file}">{label}</a>'
    presets = "".join(btn(f, l) for f, l, _ in PRESETS)
    months  = "".join(btn(f, l) for f, l, _, _ in month_list)
    return f'''<div class="navwrap">
  <div class="navrow"><span class="navlbl">기간</span>{presets}</div>
  <div class="navrow"><span class="navlbl">월별</span>{months}</div>
</div>'''

NAV_CSS = '''
<style>
.navwrap{max-width:1140px;margin:0 auto 0;padding:18px 32px 0;font-family:Pretendard,system-ui,sans-serif}
.navrow{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px}
.navlbl{font-size:12px;font-weight:700;color:#9a8f7d;width:38px;flex:none}
.navbtn{font-size:12.5px;font-weight:600;color:#6E6B63;text-decoration:none;
  padding:4px 11px;border:1px solid #E7E3DA;border-radius:20px;background:#fff;white-space:nowrap}
.navbtn:hover{border-color:#D98313;color:#9a5a08}
.navbtn.active{background:#D98313;border-color:#D98313;color:#fff}
</style>'''

def render_period(df_url, fname, days, start, end):
    """build_report_db의 build()을 특정 기간으로 호출해 HTML 문자열 생성."""
    # 환경변수로 기간 주입 (core가 읽음)
    os.environ.pop("REPORT_START", None); os.environ.pop("REPORT_END", None)
    if start and end:
        os.environ["REPORT_DAYS"] = "0"
        os.environ["REPORT_START"] = start; os.environ["REPORT_END"] = end
    else:
        os.environ["REPORT_DAYS"] = str(days)
    import importlib; importlib.reload(core)   # 환경변수 반영
    tmp = f"/tmp/_{fname}"
    core.build(df_url, tmp)
    return open(tmp, encoding="utf-8").read()

def main(src, outdir):
    os.makedirs(outdir, exist_ok=True)
    # 데이터 최신월 파악 (월별 목록 생성용)
    raw = pd.read_csv(src)
    dt = pd.to_datetime(raw["리뷰작성일시"], errors="coerce", utc=True).dt.tz_convert("Asia/Seoul").dt.tz_localize(None)
    latest = dt.max(); earliest = dt.min()
    months = month_pages(latest, earliest)

    pages = [(f, l, ("days", d, None, None)) for f, l, d in PRESETS] \
          + [(f, l, ("range", None, s, e)) for f, l, s, e in months]

    for fname, label, (kind, days, start, end) in pages:
        html = render_period(src, fname, days or 0, start, end)
        nav = nav_html(fname, months)
        # </head> 앞에 CSS, <body> 직후(.wrap 시작 전)에 nav 삽입
        html = html.replace("</head>", NAV_CSS + "</head>", 1)
        html = html.replace('<body>', '<body>' + nav, 1)
        open(os.path.join(outdir, fname), "w", encoding="utf-8").write(html)
        print(f"  생성: {fname}  ({label})")
    print(f"완료 → {outdir} ({len(pages)}개 페이지)")

if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "data/alpha_review_latest.csv"
    out = sys.argv[2] if len(sys.argv) > 2 else "site"
    main(src, out)
