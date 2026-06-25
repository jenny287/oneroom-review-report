#!/usr/bin/env python3
"""
원룸만들기 · 알파리뷰 긍정 리뷰 분석 리포트 생성기
사용법:  python scripts/build_report.py <입력CSV> <출력HTML>
예:      python scripts/build_report.py data/alpha_review_latest.csv site/index.html

알파리뷰 내보내기 CSV 한 개만 있으면 리포트(index.html)를 만든다.
자주 바뀌는 값은 아래 '설정' 블록에만 모아두었다.
"""
import sys, os, re
from collections import Counter
import pandas as pd
from kiwipiepy import Kiwi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_template import HTML_TEMPLATE

# ──────────────────────────── 설정 (여기만 바꾸면 됨) ────────────────────────────
POS_MIN     = 4         # 긍정 기준 별점(이상)
MIN_N       = 30        # 만족도 순위·적극추진 판정 최소 후기 수
BENCH_AVG   = 4.75      # 적극추진: 평균 별점 기준 (업계 '북극성')
BENCH_RATIO = 95.0      # 적극추진: 긍정 비율(%) 기준
IND_AVG     = 4.5       # 업계 평균 별점(벤치마크)
N_CARDS     = 10        # ③ 심층분석 카드 상품 수

# ── 기간 필터 ── 아래 중 하나만 설정하면 됨. 셋 다 비우면(=None/0) 전체 기간.
#  · REPORT_DAYS  : 가장 최근 리뷰 기준 최근 N일 (예: 90). 정기 리포트에 가장 자연스러움.
#  · REPORT_START / REPORT_END : 'YYYY-MM-DD' 명시 기간 (START가 있으면 DAYS보다 우선).
# 워크플로/수동 실행 때 같은 이름의 환경변수로 덮어쓸 수 있다.
REPORT_DAYS  = 90
REPORT_START = None
REPORT_END   = None
REPORT_DAYS  = int(os.environ['REPORT_DAYS']) if os.environ.get('REPORT_DAYS') else REPORT_DAYS
REPORT_START = os.environ.get('REPORT_START') or REPORT_START
REPORT_END   = os.environ.get('REPORT_END') or REPORT_END

GENERIC = {'만족','배송','가격','빠르다','감사','최고','괜찮다','만족스럽다'}   # 흔해서 강조 제외
NEG_KW  = {'소음','소리','무겁다','아쉽다','아쉽','불편','시끄럽다'}            # 부정어: 카테고리 키워드 제외
MERGE   = {'이쁘다':'예쁘다','시원':'시원하다','편리':'편하다','깔끔':'깔끔하다','튼튼':'튼튼하다','만족':'만족스럽다'}

# 카테고리 자동 분류 (상품명에 키워드 포함 시 매칭, 위에서부터 우선)
CATEGORY_RULES = [
    ('청소기',        ['청소기','진공']),
    ('계절가전',      ['선풍기','손풍기','쿨매트','냉감','냉각','서큘','히터','온풍']),
    ('침구·매트리스', ['이불','매트리스','베개','침구','패드']),
    ('주방용품',      ['국자','수저','그릇','반찬','주방','도마','텀블러','보틀']),
    ('욕실가전',      ['드라이어','샤워','욕실','바디']),
    ('디지털·전자',   ['캠','카메라','충전','거치대','케이블','이어폰','스피커']),
    ('수납·정리',     ['휴지통','수납','정리','행거','옷걸이','선반','보관']),
]
def categorize(name):
    for cat, kws in CATEGORY_RULES:
        if any(k in name for k in kws): return cat
    return '기타'

# 손으로 쓴 만족 이유(있으면 사용, 없으면 키워드 기반 자동 문장으로 대체).
# 상위 상품이 바뀌면 새 상품코드를 추가하거나, 비워두면 자동 문장이 들어간다.
PRODUCT_NOTES = {
 'P0000OCC':"손대지 않아도 센서로 자동 개폐되는 편리함이 만족의 핵심. 봉투 교체가 쉽고 냄새 차단도 호평. 다만 상위 상품 중 긍정비율이 낮은 편으로, 센서 인식 속도·뚜껑 고정력 아쉬움이 일부 반복됨.",
 'P0000UHB':"라면·마라탕 같은 국물요리에 딱 맞는 '작은 국자' 사이즈가 니즈에 정확히 적중('내가 찾던 거'). 사이즈 만족과 귀여움이 핵심이고 선물용 다회 구매가 많음. 대형 상품 중 긍정비율 최고 수준.",
 'P0000ROG':"롤팩으로 압축 배송돼 자취방 반입·설치가 쉽다는 점이 결정적. 너무 딱딱하지도 무르지도 않은 '푹신하면서 탄탄한' 쿠션감과 가격 대비 만족도가 높음.",
 'P0000WKS':"냉각모드의 시원한 바람 세기가 핵심 만족 포인트이고 여름 시즌 가성비도 호평. 다만 크기·무게가 다소 무겁다는 의견이 함께 나옴.",
 'P0000RKO':"먼지를 자동으로 비워줘 손이 거의 안 가는 편리함이 가장 큰 만족. 가벼운 무게, 강한 흡입력, 물걸레 겸용까지 '다기능 가성비'로 인식됨.",
 'P0000VRJ':"작고 귀여운 디자인과 빈티지 '감성'이 압도적 호감 요인(키워드 '귀엽다' 단일 1위). 여행 휴대성도 강점. 감성 소품으로 포지셔닝돼 만족도 높음.",
 'P0000MME':"가벼우면서 따뜻하고 디자인이 예쁘다는 점, 타 쇼핑몰 대비 최저가 가성비가 핵심. 다만 두께가 얇다는 호불호가 있어 상위 상품 중 긍정비율은 낮은 편.",
 'P0000WGG':"대용량과 예쁜 색상·디자인이 여름 시즌 니즈와 맞물려 호평. 다만 무게, 사은품 미니텀블러 색상, 뚜껑 개폐 등 소소한 불만도 존재.",
 'P0000MTQ':"10만 원 이하 가격에 강한 흡입력과 가벼움을 동시에 갖춘 '가성비 청소기'로 인식. 조립·거치 간편함도 호평(거치대 견고성은 소소한 아쉬움).",
 'P0000WLI':"센 바람 세기와 시원함, 가성비가 만족 요인. 다만 '소음'이 반복 언급되는 약점으로, 상위 상품 중 긍정비율이 가장 낮음 — 개선 우선순위 후보.",
}
# ────────────────────────────────────────────────────────────────────────────

def f2(x): return f"{x:.2f}"
def is_push(a, r, n): return (a >= BENCH_AVG) and (r >= BENCH_RATIO) and (n >= MIN_N)

def clean(t):
    t = re.sub(r'\(\s*\d{4}-\d{2}-\d{2}[^)]*네이버\s*페이\s*구매평\s*\)', ' ', t)
    t = re.sub(r'[\t\r\n]+', ' ', t); t = re.sub(r'\s+', ' ', t).strip(); return t

COMPLAINT = re.compile(r'아쉽|안되|안돼|불량|별로|최악|망했|느림|느려|느리|느립|허술|헐렁|사치|안열|깨져|무겁|시끄|소음|냄새가 많|강하지는 않|않아요|단점|힘들|타이트|근데|하지만|다만|아쉬|못생|안맞|안쓸|잘모르|써보진|아직 안')

def load(csv_path):
    df = pd.read_csv(csv_path)
    df['리뷰내용'] = df['리뷰내용'].fillna('').astype(str)
    cust = df[df['작성자종류'] != '관리자'].copy()        # 판매자 작성 후기 제외
    cust['clean'] = cust['리뷰내용'].map(clean)
    cust['is_pos'] = cust['리뷰평점'] >= POS_MIN
    cust['is_neg'] = cust['리뷰평점'] <= 2
    return df, cust

def extract_keywords(cust):
    kiwi = Kiwi(); KEEP = ('NNG','NNP','XR','VA','VA-I')
    STOP_N = set('것 거 수 때 점 제품 상품 구매 사용 정도 생각 때문 주문 리뷰 후기 사진 별 별점 분 번 개 원 한번 하나 자체 정말 진짜 완전 조금 약간 부분 이거 그거 저거 저희 우리 다음 동안 이번 요즘 가지 중 등 거기 여기 좀 더 또 잘 안 못 수도 듯 만큼 모두 다들 보니 게 데 줄 척 채 뿐 마음 구입 사용감 느낌 첫 게요 거예요'.split())
    STOP_A = set('이러 그러 저러 같 어떻'.split())
    src = cust[(cust['is_pos']) & (cust['빠른리뷰'] == False) & (cust['clean'].str.len() >= 2)]
    overall = Counter(); per = {}
    for code, toks in zip(src['상품코드'].tolist(), kiwi.tokenize(src['clean'].tolist())):
        s = set()
        for t in toks:
            if t.tag in KEEP and len(t.form) >= 2:
                if t.tag in ('NNG','NNP','XR') and t.form in STOP_N: continue
                if t.tag in ('VA','VA-I'):
                    if t.form in STOP_A: continue
                    w = t.form + '다'
                else:
                    w = t.form
                s.add(w)
        overall.update(s); per.setdefault(code, Counter()).update(s)
    return overall, per

def merge_counter(counter, drop=()):
    mc = Counter()
    for w, c in counter.items():
        w2 = MERGE.get(w, w)
        if w2 in drop: continue
        mc[w2] += c
    return mc

def quotes(cust, code, k=2):
    s = cust[(cust['상품코드'] == code) & (cust['is_pos']) & (cust['빠른리뷰'] == False)]
    s = s[s['clean'].str.len().between(22, 95)]
    s = s[~s['clean'].str.contains(COMPLAINT)]
    out = []; seen = set()
    for v in s['clean']:
        if v in seen: continue
        seen.add(v); out.append(v)
        if len(out) >= k: break
    return out

def auto_note(chips, ratio):
    sig = [w for w, c, s in chips if s][:3] or [w for w, c, s in chips][:3]
    return f"주요 만족 요인은 {'·'.join(sig)} 등으로 나타남. 긍정 비율 {f2(ratio)}%."

def build(csv_path, out_path):
    df, cust = load(csv_path)
    cust['dt'] = pd.to_datetime(cust['리뷰작성일시'], format='%y-%m-%d %H:%M', errors='coerce')
    data_min, data_max = cust['dt'].min(), cust['dt'].max()

    # 기간 필터 (최근 N일 또는 명시 기간). 기준점은 '파일 내 최신 리뷰'로 잡아 스냅샷에도 안전.
    if REPORT_START or REPORT_END or REPORT_DAYS:
        end = pd.Timestamp(REPORT_END) if REPORT_END else data_max
        if REPORT_START:
            start = pd.Timestamp(REPORT_START)
        elif REPORT_DAYS:
            start = end - pd.Timedelta(days=REPORT_DAYS)
        else:
            start = data_min
        filtered = cust[(cust['dt'] >= start) & (cust['dt'] < end + pd.Timedelta(days=1))]
        if len(filtered) == 0:
            print(f"[경고] 설정 기간({start:%Y.%m.%d}~{end:%Y.%m.%d})에 리뷰가 없어 전체 기간으로 대체합니다.")
            period = f"{data_min:%Y.%m.%d} – {data_max:%Y.%m.%d}"
        else:
            cust = filtered
            period = f"{start:%Y.%m.%d} – {end:%Y.%m.%d}"
    else:
        period = f"{data_min:%Y.%m.%d} – {data_max:%Y.%m.%d}"

    N_all = len(df); N_cust = len(cust); N_pos = int(cust['is_pos'].sum())
    pos_ratio = round(N_pos / N_cust * 100, 2); n_prod = cust['상품코드'].nunique()
    avg = round(cust['리뷰평점'].mean(), 2)

    overall_kw, per_kw = extract_keywords(cust)
    over = [(w, c) for w, c in merge_counter(overall_kw, drop={'만족스럽다','감사','최고','괜찮다'}).most_common(15)]

    agg = cust.groupby(['상품코드','상품명']).agg(
        n_total=('리뷰평점','size'), n_pos=('is_pos','sum'),
        n_neg=('is_neg','sum'), avg=('리뷰평점','mean')).reset_index()
    agg['pos_ratio'] = (agg['n_pos'] / agg['n_total'] * 100).round(2)
    agg['avg'] = agg['avg'].round(2)
    agg['push'] = agg.apply(lambda r: is_push(r['avg'], r['pos_ratio'], r['n_total']), axis=1)
    n_push = int(agg['push'].sum())
    top_count = agg.sort_values('n_pos', ascending=False).head(12)
    top_ratio = agg[agg['n_total'] >= MIN_N].sort_values(['pos_ratio','n_total'], ascending=[False, False]).head(14)

    def chips_of(code, n=8):
        return [(w, c) for w, c in merge_counter(per_kw.get(code, Counter()), drop={'만족스럽다'}).most_common(n)]

    card_codes = list(top_count['상품코드'])[:N_CARDS]
    cat_group = {}
    amap = agg.set_index('상품코드')
    for code in card_codes:
        cat = categorize(amap.loc[code, '상품명'])
        for w, c in chips_of(code, 12):
            if w in GENERIC or w in NEG_KW: continue
            cat_group.setdefault(cat, Counter())[w] += c
    cat_sig = {cat: set(w for w, _ in cnt.most_common(5)) for cat, cnt in cat_group.items()}

    products = []
    for code in card_codes:
        r = amap.loc[code]; name = r['상품명']; cat = categorize(name); sig = cat_sig.get(cat, set())
        chips = [(w, c, (w in sig)) for w, c in chips_of(code)]
        note = PRODUCT_NOTES.get(code) or auto_note(chips, r['pos_ratio'])
        products.append(dict(code=code, name=name, cat=cat, n_pos=int(r['n_pos']), n_total=int(r['n_total']),
            pos_ratio=float(r['pos_ratio']), avg=float(r['avg']), push=bool(r['push']),
            chips=chips, quotes=quotes(cust, code), note=note))

    data = dict(
        summary=dict(N_all=N_all, N_cust=N_cust, N_pos=N_pos, pos_ratio=pos_ratio, n_prod=n_prod, avg=avg, period=period),
        bench=dict(avg=BENCH_AVG, ratio=BENCH_RATIO, min_n=MIN_N, n_push=n_push, ind_avg=IND_AVG),
        over=over,
        top_count=[[x['상품명'], int(x['n_total']), int(x['n_pos']), float(x['pos_ratio']), float(x['avg']), bool(x['push'])] for _, x in top_count.iterrows()],
        top_ratio=[[x['상품명'], int(x['n_total']), int(x['n_pos']), float(x['pos_ratio']), float(x['avg']), bool(x['push'])] for _, x in top_ratio.iterrows()],
        products=products)

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    open(out_path, 'w').write(HTML_TEMPLATE(data))
    print(f"생성 완료 → {out_path} | 고객후기 {N_cust:,} · 긍정 {f2(pos_ratio)}% · 적극추진 {n_push}개")

if __name__ == '__main__':
    csv = sys.argv[1] if len(sys.argv) > 1 else 'data/alpha_review_latest.csv'
    out = sys.argv[2] if len(sys.argv) > 2 else 'site/index.html'
    build(csv, out)
