#!/usr/bin/env python3
"""
원룸만들기 · 알파리뷰 긍정 리뷰 분석 리포트 생성기
사용법:  python scripts/build_report.py <입력CSV> <출력HTML>
예:      python scripts/build_report_db.py <공개CSV_URL 또는 파일경로> site/index.html

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
WATCH_AVG   = 4.6       # 추진검토(한 단계 아래): 평균 별점 기준
WATCH_RATIO = 90.0      # 추진검토: 긍정 비율(%) 기준
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
    ('침구·매트리스', ['이불','매트리스','베개','침구','패드','담요','후드']),
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
 '봉투밀착 밀폐 센서휴지통':"손대지 않아도 센서로 자동 개폐되는 편리함이 만족의 핵심. 봉투 교체가 쉽고 냄새 차단도 호평. 다만 상위 상품 중 긍정비율이 낮은 편으로, 센서 인식 속도·뚜껑 고정력 아쉬움이 일부 반복됨.",
 '앞접시 초미니국자 세트':"라면·마라탕 같은 국물요리에 딱 맞는 '작은 국자' 사이즈가 니즈에 정확히 적중('내가 찾던 거'). 사이즈 만족과 귀여움이 핵심이고 선물용 다회 구매가 많음. 대형 상품 중 긍정비율 최고 수준.",
 '올인홈 롤팩 매트리스':"롤팩으로 압축 배송돼 자취방 반입·설치가 쉽다는 점이 결정적. 너무 딱딱하지도 무르지도 않은 '푹신하면서 탄탄한' 쿠션감과 가격 대비 만족도가 높음.",
 '더커진 냉각 손선풍기':"냉각모드의 시원한 바람 세기가 핵심 만족 포인트이고 여름 시즌 가성비도 호평. 다만 크기·무게가 다소 무겁다는 의견이 함께 나옴.",
 '자동 먼지비움 괴물청소기':"먼지를 자동으로 비워줘 손이 거의 안 가는 편리함이 가장 큰 만족. 가벼운 무게, 강한 흡입력, 물걸레 겸용까지 '다기능 가성비'로 인식됨.",
 '셀카모드 초미니 키링캠':"작고 귀여운 디자인과 빈티지 '감성'이 압도적 호감 요인(키워드 '귀엽다' 단일 1위). 여행 휴대성도 강점. 감성 소품으로 포지셔닝돼 만족도 높음.",
 '유어메이트 워싱 차렵이불':"가벼우면서 따뜻하고 디자인이 예쁘다는 점, 타 쇼핑몰 대비 최저가 가성비가 핵심. 다만 두께가 얇다는 호불호가 있어 상위 상품 중 긍정비율은 낮은 편.",
 '프라데라 대용량 텀블러':"대용량과 예쁜 색상·디자인이 여름 시즌 니즈와 맞물려 호평. 다만 무게, 사은품 미니텀블러 색상, 뚜껑 개폐 등 소소한 불만도 존재.",
 '330W 흡입력 괴물 청소기':"10만 원 이하 가격에 강한 흡입력과 가벼움을 동시에 갖춘 '가성비 청소기'로 인식. 조립·거치 간편함도 호평(거치대 견고성은 소소한 아쉬움).",
 '애프터샤워 바디드라이어':"센 바람 세기와 시원함, 가성비가 만족 요인. 다만 '소음'이 반복 언급되는 약점으로, 상위 상품 중 긍정비율이 가장 낮음 — 개선 우선순위 후보.",
 "집순이 탈부착 후드 담요":"포근하고 따뜻한 극세사 촉감에 후드 탈부착·잠옷 같은 편안함이 더해져 겨울 보온템으로 압도적 호평(긍정 96%대 상위 최상위). 다만 똑딱이(스냅) 불량 등 검수 관련 불만이 일부 있음.",
 "고속충전 자바라 거치대":"누워서 폰·태블릿 보기 좋은 각도 조절과 고속충전이 핵심 만족('침대 붙박이 생활'). 다만 사용 기간이 지나면 봉·판 고정력이 약해져 흔들린다는 불만이 반복되는 편.",
 "칸막이 문걸이 화장대":"문에 걸어 자투리 공간을 화장대·수납으로 활용하는 아이디어가 호평. 다만 거울이 양면테이프 고정이라 떨어져 깨졌다는 안전 관련 불만이 반복돼, 상위 상품 중 긍정비율이 낮은 편 — 개선 우선순위 후보.",
 "써머쿨링 냉감 여름이불":"냉감 촉감과 시원함으로 '에어컨 없이도 여름을 난다'는 호평. 가볍고 색감·디자인도 예쁘다는 평. 색상이 사진과 다르다는 의견은 일부.",
 "빈티지 초미니 키링캠":"작고 귀여운 키링형 디자인과 빈티지 '감성'이 핵심 호감 요인. 휴대성·선물용으로 인기이고 화질도 기대 이상이라는 평. (셀카모드 키링캠과 유사 라인)",
 "2초발열 방수 욕실히터":"추운 욕실을 빠르게 데워 샤워 시 따뜻하다는 점이 만족 요인. 다만 초기 고장·AS 지연, 사용 시 냄새 등 불만이 적지 않아 상위 상품 중 긍정비율이 낮은 편.",
 "듀라론100% 매쉬 쿨매트":"냉감 효과가 확실하다는 평이 많고, 색이 없는 흰색이 오히려 효과가 좋다는 인식으로 만족도 높음. 부드러운 촉감도 호평.",
 "북극곰 양면 토퍼 13cm":"양면 사용에 푹신하고 따뜻해 겨울 난방비 절약 효과까지 호평. 다만 초기 털빠짐, 외곽 쿠션감 부족 같은 불만도 일부.",
 "디얼 셀피 카메라":"'막 찍어도 미친 감성'이라는 빈티지 감성과 귀여운 디자인이 핵심 호감. 셀카·여행용으로 인기, 화질도 기대 이상. 일부 초기 화면 불량 사례는 있음.",
 "더라이트 먼지비움 청소기":"가벼운 무게에 자동 먼지비움·물걸레까지 갖춘 가성비가 핵심. 다만 흡입력이 약하다는 의견도 일부 있어 호불호.",
 "탈부착 보조배터리 충전기":"보조배터리+무드등+맥세이프 충전을 한데 모은 '올인원' 구성이 만족 요인. 다만 상위 상품 중 긍정비율이 가장 낮은 편이라 기대와 실사용 간 편차가 있는 편.",
 "조립식 투명 회전 책장":"공간 대비 수납량이 좋고 무거운 책도 부드럽게 도는 회전 기능이 호평. 다만 조립·분해가 다소 힘들다는 의견이 함께.",
 "이지 스마트 빔프로젝터":"원룸에서 유튜브·넷플릭스 보기 좋은 가성비가 강점. 다만 소음·해상도 등에서 기대 이하라는 의견이 많아 상위 상품 중 긍정비율이 가장 낮음.",
 "내솥분리 멀티 포트":"내솥 분리로 설거지가 편하고 라면·간단 조리에 좋다는 평. 색상·디자인이 예뻐 선물용 재구매도 많음.",
 "더버한일 워셔블 탄소매트":"빠르게 따뜻해지고 전기 소음이 없어 겨울 난방용으로 만족도 높음. 커버 분리 세탁 가능, 가성비도 호평.",
 "자국없는 벨크로 암막커튼":"벨크로로 자국 없이 간편 설치되면서 얇아도 암막 차단이 잘 된다는 점이 호평. 햇빛 차단으로 숙면에 도움.",
 "스위프 진동 침구청소기":"이불·침구 먼지 제거와 살균 기능이 만족 요인. 다만 머리카락이 한 번에 안 빨려 여러 번 문대야 한다는 등 효용성에 호불호.",
 "스트라이프 소다 쿨매트":"깔자마자 느껴지는 냉감과 부드러운 촉감으로 여름나기 좋다는 평, 디자인도 예쁘다는 평. 다만 기대와 다르다는 의견도 일부.",
 "멜로우 전동드라이버 세트":"작고 귀여운 디자인에 가구 조립이 손쉬워진다는 점이 핵심. 여성도 쓰기 편하고 의외로 튼튼하다는 평으로 만족도 높음.",
 "홈리아 무선 핸디청소기":"원룸에 딱 맞는 크기와 가벼움, 예쁜 디자인이 호평. 흡입력도 컴팩트한 크기 대비 좋다는 평.",
 "이동식 바지걸이 행거":"바지를 가지런히 정리해 한눈에 보이는 수납 편의가 핵심. 가격 대비 만족도 매우 높음(상위권 최상위). 일부 흔들림 불만은 소수.",
 "냉감 코끼리 필로우":"시원한 냉감과 푹신함이 만족 요인이고 아이들이 좋아한다는 평. 다만 크기가 생각과 다르다는 편차와 마감 불만이 있어 상위 상품 중 긍정비율이 낮은 편.",
 "꺼짐없는 2중솜 토퍼매트":"2중솜의 푹신함으로 꺼진 침대 위에 깔기 좋다는 평. 다만 바닥에서 밀려 고정이 안 된다는 불만이 일부.",
 "공간분리 화장품 정리함":"칸 분리 수납으로 화장품이 깔끔하게 정리되고 먼지도 막아준다는 점이 호평. 용량도 넉넉하다는 평으로 만족도 높음.",
 "더 폭신 듀라픽셀 쿨패드":"선풍기·에어컨과 함께 쓰면 확실히 시원하고 고정끈으로 안 밀린다는 점이 호평('삶의 질 상승템'). 다만 세탁 후 줄어든다는 불만은 일부.",
 "극세사 인절미 이불":"쫀득하고 부드러운 극세사 촉감과 따뜻함이 인기(전기장판 없이 난다는 평). 다만 세탁 후 솜뭉침·실빠짐 불만이 반복돼 호불호.",
 "유어메이트 냉감 여름이불":"가볍고 시원한 냉감에 화사한 색감·디자인이 더해져 호평. 패드와 함께 쓰면 더 좋다는 평. 색이 사진과 다르다는 의견은 일부.",
 "원룸만들기 파자마 세트":"부드러운 소재와 넉넉한 사이즈로 착용감이 편하다는 점이 핵심. 피부 자극 없는 원단이라는 평으로 만족도 높음.",
 "초대형 6인치 손선풍기":"큰 팬에서 나오는 시원한 바람 세기가 핵심 만족 포인트이고, 큰 크기 대비 가볍다는 평. 다만 휴대용으론 너무 크다는 의견도(탁상용으로 호평).",
 "대용량 에어프라이어 오븐":"예쁜 디자인에 대용량·다양한 기능을 저렴하게 갖춘 가성비가 호평. 다만 초기 냄새가 난다는 의견은 일부.",
 "대용량 화장품 정리함":"넉넉한 용량으로 화장대가 한 번에 정리되고, 자석 여닫이·깔끔한 디자인이 호평.",
 "와이드 높이조절 롤클리너":"넓은 폭으로 한 번에 청소되는 효율과 접착력이 '신세계'라는 호평(선물·재구매 많음). 다만 시트 교체가 다소 불편하다는 의견.",
 "5in1 에어롤 헤어스타일러":"가볍고 바람이 강해 웨이브·스타일링이 잘 된다는 가성비가 호평. 다만 영상만큼 컬이 안 잡힌다는 의견도 일부.",
 "큐브 음식물 처리기 2.5L":"자취방에 맞는 작은 크기로 음식물·냄새·날파리 걱정을 덜어준다는 점이 핵심('자취생 구원템'). 기대와 다르다는 의견도 일부 있어 만족도는 중간대.",
 "원룸만들기 여름 파자마":"시원한 색감과 좋은 재질, 넉넉한 핏으로 여름 잠옷으로 호평. 다만 봉제가 터졌다는 불만이 일부.",
 "칸칸이 강력밀폐 도시락통":"국물이 새지 않는 강력 밀폐와 전자레인지 사용 가능이 만족 요인. 다만 옵션 오배송 등 배송 관련 불만이 일부.",
 "반반 매트리스 토퍼 10cm":"앞뒤(딱딱/푹신) 양면으로 쓸 수 있고 꺼진 매트리스 위에 깔기 좋다는 평. 포근해서 꿀잠 잔다는 호평.",
 "브리타 필터정수기 5종":"생수를 안 사도 돼 공간·쓰레기를 줄여준다는 점과 좋은 물맛이 핵심. 원룸 자취에 잘 맞아 만족도 최상위권.",
 "락앤락 푸드워머 1/2구":"음식을 식지 않게 따뜻하게 유지해주는 점이 만족 요인(식은 음식 데우기 좋음). 다만 사용 몇 개월 만에 고장났다는 불만이 일부.",
 "커버분리 코끼리 필로우":"말랑·폭신한 촉감과 안정감이 호평이고 커버 분리 세탁 가능. 다만 봉제가 터졌다는 불만과 큰 베개 호불호가 있는 편.",
}
# ────────────────────────────────────────────────────────────────────────────

def f2(x): return f"{x:.2f}"
def is_push(a, r, n): return (a >= BENCH_AVG) and (r >= BENCH_RATIO) and (n >= MIN_N)
def is_watch(a, r, n): return (not is_push(a, r, n)) and (a >= WATCH_AVG) and (r >= WATCH_RATIO) and (n >= MIN_N)

import html as _html
def clean(t):
    t = re.sub(r'\(\s*\d{4}-\d{2}-\d{2}[^)]*네이버\s*페이\s*구매평\s*\)', ' ', t)
    t = re.sub(r'<[^>]+>', ' ', t)          # HTML 태그 제거 (<p>, <br>, <span> 등)
    t = _html.unescape(t)                    # &amp; &nbsp; 등 엔티티 복원
    t = t.replace('\xa0', ' ')               # nbsp 잔여
    t = re.sub(r'[\t\r\n]+', ' ', t); t = re.sub(r'\s+', ' ', t).strip(); return t

COMPLAINT = re.compile(r'아쉽|안되|안돼|불량|별로|최악|망했|느림|느려|느리|느립|허술|헐렁|사치|안열|깨져|무겁|시끄|소음|냄새가 많|강하지는 않|않아요|단점|힘들|타이트|근데|하지만|다만|아쉬|못생|안맞|안쓸|잘모르|써보진|아직 안')

def load(csv_path):
    df = pd.read_csv(csv_path)
    df['리뷰내용'] = df['리뷰내용'].fillna('').astype(str)
    df = df[~df['상품명'].astype(str).str.startswith('추가_')].copy()   # 옵션·사은품성 '추가_' 상품 제외
    cust = df.copy()                                       # 게시판 API엔 판매자 글이 없음(검증완료) → 전체가 고객후기
    cust['clean'] = cust['리뷰내용'].map(clean)
    cust['is_pos'] = cust['리뷰평점'] >= POS_MIN
    cust['is_neg'] = cust['리뷰평점'] <= 2
    cust['is_quick'] = cust['빠른리뷰여부'].astype(str).str.upper() == 'Y'   # 빠른리뷰 플래그
    return df, cust

def extract_keywords(cust):
    kiwi = Kiwi(); KEEP = ('NNG','NNP','XR','VA','VA-I')
    STOP_N = set('것 거 수 때 점 제품 상품 구매 사용 정도 생각 때문 주문 리뷰 후기 사진 별 별점 분 번 개 원 한번 하나 자체 정말 진짜 완전 조금 약간 부분 이거 그거 저거 저희 우리 다음 동안 이번 요즘 가지 중 등 거기 여기 좀 더 또 잘 안 못 수도 듯 만큼 모두 다들 보니 게 데 줄 척 채 뿐 마음 구입 사용감 느낌 첫 게요 거예요'.split())
    STOP_A = set('이러 그러 저러 같 어떻'.split())
    src = cust[(cust['is_pos']) & (cust['is_quick'] == False) & (cust['clean'].str.len() >= 2)]
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

def quotes(cust, code, k=10):
    # 표시용: 긍정·비빠른리뷰·불만어 없는 깔끔한 후기 최대 k개 (앞 2개만 기본 노출, 나머지 토글)
    s = cust[(cust['상품코드'] == code) & (cust['is_pos']) & (cust['is_quick'] == False)]
    s = s[s['clean'].str.len().between(15, 140)]
    s = s[~s['clean'].str.contains(COMPLAINT)]
    out = []; seen = set()
    for v in s['clean']:
        if v in seen: continue
        seen.add(v); out.append(v)
        if len(out) >= k: break
    return out

def download_rows(cust, code, cap=100):
    # 다운로드용: 고객이 직접 작성한 후기만(빠른리뷰 템플릿 제외) 최신순 최대 cap개
    s = cust[(cust['상품코드'] == code) & (cust['is_quick'] == False)].sort_values('dt', ascending=False)
    rows = []
    for _, r in s.head(cap).iterrows():
        rows.append({
            "rating": int(r['리뷰평점']),
            "date": (r['dt'].strftime('%Y-%m-%d') if pd.notna(r['dt']) else ''),
            "content": r['clean'],
        })
    return rows

def auto_note(name, chips, r):
    # 손글씨가 없는 상품용 자동 설명 — 실제 키워드+수치로 자연스러운 문장 생성
    sig = [w for w, c, s in chips if s] or [w for w, c, _ in chips]
    sig = [w for w in sig if w not in GENERIC][:3] or [w for w, c, _ in chips][:3]
    ratio = r['pos_ratio']; avg = r['avg']; push = r['push']
    drivers = '·'.join(sig) if sig else '전반적인 사용 경험'
    # 만족도 수준 표현
    if push:
        tail = f"긍정 비율 {f2(ratio)}%·평균 ★{f2(avg)}로 시장 평균을 분명히 웃도는 '적극 추진' 후보입니다."
    elif ratio >= 90:
        tail = f"긍정 비율 {f2(ratio)}%·평균 ★{f2(avg)}로 만족도가 높은 편입니다."
    elif ratio >= 85:
        tail = f"긍정 비율 {f2(ratio)}%·평균 ★{f2(avg)}로 무난한 만족도입니다."
    else:
        tail = f"긍정 비율 {f2(ratio)}%·평균 ★{f2(avg)}로, 상위 상품 중에서는 만족도가 낮은 편이라 개선 여지가 있습니다."
    return f"고객은 주로 {drivers} 측면을 높이 평가합니다. {tail}"

def build(csv_path, out_path):
    df, cust = load(csv_path)
    cust['dt'] = pd.to_datetime(cust['리뷰작성일시'], errors='coerce', utc=True).dt.tz_convert('Asia/Seoul').dt.tz_localize(None)
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
    agg['watch'] = agg.apply(lambda r: is_watch(r['avg'], r['pos_ratio'], r['n_total']), axis=1)
    n_push = int(agg['push'].sum())
    n_watch = int(agg['watch'].sum())
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
        note = PRODUCT_NOTES.get(name) or auto_note(name, chips, r)
        products.append(dict(code=code, name=name, cat=cat, n_pos=int(r['n_pos']), n_total=int(r['n_total']),
            pos_ratio=float(r['pos_ratio']), avg=float(r['avg']), push=bool(r['push']), watch=bool(r['watch']),
            chips=chips, quotes=quotes(cust, code), note=note,
            downloads=download_rows(cust, code)))

    # ── 판매 추천 3종 ──────────────────────────────────────────────
    # 분석 신뢰를 위해 후기 20건 이상 상품만 추천 풀로 사용
    REC_MIN = 20
    pool = agg[agg['n_total'] >= REC_MIN].copy()
    pool['cat'] = pool['상품명'].map(categorize)
    # 상품별 대표 키워드 집합(비제너릭, 상위 8개)
    def kwset(code):
        ks = [w for w, _ in merge_counter(per_kw.get(code, Counter())).most_common(12)
              if w not in GENERIC and w not in NEG_KW]
        return set(ks[:8])
    pool_kw = {row['상품코드']: kwset(row['상품코드']) for _, row in pool.iterrows()}

    # (1) 카테고리 추천: 후기 충분한 카테고리의 만족도 순
    catg = pool.groupby('cat').agg(
        n_products=('상품코드', 'nunique'), n_reviews=('n_total', 'sum'),
        pos=('n_pos', 'sum')).reset_index()
    catg['avg_rating'] = pool.groupby('cat')['avg'].mean().round(2).values
    catg['pos_ratio'] = (catg['pos'] / catg['n_reviews'] * 100).round(2)
    catg = catg[catg['cat'] != '기타'].sort_values(['pos_ratio', 'n_reviews'], ascending=[False, False]).head(6)
    rec_categories = []
    for _, x in catg.iterrows():
        members = pool[pool['cat'] == x['cat']].sort_values(['pos_ratio', 'n_total'], ascending=[False, False])
        plist = [dict(name=mm['상품명'], pos_ratio=float(mm['pos_ratio']), avg=float(mm['avg']), n=int(mm['n_total']))
                 for _, mm in members.head(30).iterrows()]
        rec_categories.append(dict(cat=x['cat'], n_products=int(x['n_products']), n_reviews=int(x['n_reviews']),
                               pos_ratio=float(x['pos_ratio']), avg=float(x['avg_rating']), products=plist))

    # (2) 유사 상품 추천: 상위 5개 앵커 각각에 대해 키워드 자카드 유사 상품 top3
    anchors = list(top_count['상품코드'])[:5]
    rec_similar = []
    for ac in anchors:
        aset = pool_kw.get(ac, kwset(ac))
        if not aset: continue
        sims = []
        for code2, kset in pool_kw.items():
            if code2 == ac or not kset: continue
            inter = len(aset & kset); union = len(aset | kset)
            if inter == 0: continue
            jac = inter / union
            sims.append((jac, code2, sorted(aset & kset)))
        sims.sort(reverse=True)
        items = []
        for jac, code2, shared in sims[:3]:
            rr = amap.loc[code2]
            items.append(dict(name=rr['상품명'], shared=shared[:4],
                              pos_ratio=float(rr['pos_ratio']), avg=float(rr['avg']), n=int(rr['n_total'])))
        if items:
            rec_similar.append(dict(anchor=amap.loc[ac, '상품명'], items=items))

    # (3) 상품군 추천: 강점 키워드별로, 그 키워드를 가진 상품을 다시 카테고리로 묶음
    STRENGTH = ['가성비', '편하다', '시원하다', '귀엽다', '예쁘다', '가볍다', '자동', '튼튼하다']
    rec_groups = []
    for kw in STRENGTH:
        members = [amap.loc[code2] for code2, kset in pool_kw.items() if kw in kset]
        if len(members) < 3: continue
        bycat = {}
        for rr in members:
            bycat.setdefault(categorize(rr['상품명']), []).append(rr)
        cats_list = []
        for cat, rrs in bycat.items():
            rrs = sorted(rrs, key=lambda r: (r['pos_ratio'], r['n_total']), reverse=True)
            items = [dict(name=r['상품명'], pos_ratio=float(r['pos_ratio']), n=int(r['n_total'])) for r in rrs[:5]]
            cats_list.append(dict(cat=cat, n=len(rrs), items=items))
        cats_list = sorted(cats_list, key=lambda c: (c['cat'] == '기타', -c['n']))
        rec_groups.append(dict(keyword=kw, n_products=len(members), cats=cats_list))
    rec_groups = sorted(rec_groups, key=lambda g: g['n_products'], reverse=True)[:5]

    data = dict(
        summary=dict(N_all=N_all, N_cust=N_cust, N_pos=N_pos, pos_ratio=pos_ratio, n_prod=n_prod, avg=avg, period=period),
        bench=dict(avg=BENCH_AVG, ratio=BENCH_RATIO, min_n=MIN_N, n_push=n_push, ind_avg=IND_AVG,
                   watch_avg=WATCH_AVG, watch_ratio=WATCH_RATIO, n_watch=n_watch),
        over=over,
        top_count=[[x['상품명'], int(x['n_total']), int(x['n_pos']), float(x['pos_ratio']), float(x['avg']), bool(x['push']), bool(x['watch'])] for _, x in top_count.iterrows()],
        top_ratio=[[x['상품명'], int(x['n_total']), int(x['n_pos']), float(x['pos_ratio']), float(x['avg']), bool(x['push']), bool(x['watch'])] for _, x in top_ratio.iterrows()],
        products=products,
        rec=dict(categories=rec_categories, similar=rec_similar, groups=rec_groups))

    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    open(out_path, 'w').write(HTML_TEMPLATE(data))
    print(f"생성 완료 → {out_path} | 고객후기 {N_cust:,} · 긍정 {f2(pos_ratio)}% · 적극추진 {n_push}개 · 추진검토 {n_watch}개")

if __name__ == '__main__':
    csv = sys.argv[1] if len(sys.argv) > 1 else 'data/alpha_review_latest.csv'
    out = sys.argv[2] if len(sys.argv) > 2 else 'site/index.html'
    build(csv, out)
