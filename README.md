# 원룸만들기 · 알파리뷰 긍정 리뷰 분석 리포트

알파리뷰 내보내기 CSV 한 개로 "긍정 리뷰가 많은 상품 + 만족 이유" 리포트(`index.html`)를
자동 생성해 GitHub Pages로 발행한다.

---

## 폴더 구조

```
.
├─ data/
│   └─ alpha_review_latest.csv      ← 알파리뷰에서 내보낸 최신 CSV (이 이름으로 덮어쓰기)
├─ scripts/
│   ├─ build_report.py              ← 집계·키워드·HTML 생성 (설정값은 파일 상단 '설정' 블록)
│   ├─ report_template.py           ← HTML 디자인 템플릿
│   └─ requirements.txt
├─ site/
│   └─ index.html                   ← 생성 결과물 (자동 생성, 직접 수정 X)
└─ .github/workflows/build-report.yml
```

---

## 1) 최초 1회 설정

1. 이 저장소를 GitHub에 올린다 (예: `jenny287/oneroom-review-report`).
2. **Settings → Pages → Build and deployment → Source 를 `GitHub Actions` 로 변경**한다.
   (브랜치 방식이 아니라 Actions 배포 방식을 쓴다 — 생성 파일을 커밋해둘 필요가 없어 깔끔하다.)
3. 끝. 이후 push 또는 수동 실행 때마다 자동으로 빌드·배포된다.
   주소는 `https://jenny287.github.io/oneroom-review-report/` 형태가 된다.

> 비공개로 두고 싶으면: 무료 플랜의 Pages는 공개 URL이다. 링크를 모르면 접근이 어렵지만
> 완전 비공개가 필요하면 별도 인증(예: Cloudflare Access) 또는 유료 플랜이 필요하다.

---

## 2) 리포트 갱신 방법 (주기적 운영)

가장 단순하고 안정적인 방식 = **"새 CSV를 올리면 자동으로 다시 만든다"**.

1. 알파리뷰 관리자에서 후기를 CSV로 내보낸다.
2. 그 파일을 `data/alpha_review_latest.csv` 로 덮어쓰기 해서 push한다.
   (GitHub 웹에서 파일 업로드로 교체해도 된다 — 터미널 불필요.)
3. Actions가 자동으로 돌아 `index.html` 을 새로 만들고 Pages에 배포한다. 1~2분이면 반영.

수동으로 다시 돌리고 싶으면 **Actions 탭 → Build & deploy review report → Run workflow**.

> 참고: GitHub Actions의 `schedule`(cron) 자동 실행은 실행 누락이 잦은 편이라,
> "데이터 올리면 그때 빌드"하는 위 방식이 더 안정적이다. 데이터가 안 바뀌면
> 리포트도 안 바뀌므로, CSV 교체를 트리거로 삼는 게 자연스럽다.

---

## 3) 로컬에서 직접 만들기 (선택)

```bash
pip install -r scripts/requirements.txt
python scripts/build_report.py data/alpha_review_latest.csv site/index.html
# site/index.html 을 브라우저로 열어 확인
```

---

## 4) 자주 손대는 설정값

`scripts/build_report.py` 상단 **설정** 블록만 고치면 된다.

| 값 | 의미 | 기본값 |
|---|---|---|
| `POS_MIN` | 긍정 기준 별점(이상) | 4 |
| `MIN_N` | 만족도 순위·적극추진 최소 후기 수 | 30 |
| `BENCH_AVG` / `BENCH_RATIO` | 적극추진 판정 기준(평균★ / 긍정%) | 4.75 / 95.0 |
| `CATEGORY_RULES` | 상품명 키워드 → 카테고리 자동 분류 규칙 | (편집 가능) |
| `PRODUCT_NOTES` | 상품별 손글씨 만족 이유. 없으면 키워드 기반 자동 문장 | (상위 10개 작성됨) |

> 상위 상품이 바뀌면 새 상품코드의 `PRODUCT_NOTES`를 추가하면 더 풍부한 설명이 들어가고,
> 비워두면 키워드 기반 자동 문장으로 채워진다(빌드는 항상 성공).

---

## 데이터 처리 원칙 (왜 신뢰할 수 있나)

- 판매자(관리자)가 직접 쓴 후기는 제외 → 고객 목소리만 분석
- 클릭형 '빠른리뷰'(정해진 문구 클릭)는 키워드에서 제외 → 상품별 차이 보존
- 네이버페이 자동 삽입 문구 제거 → 실제 고객 텍스트만 사용
- 긍정/부정은 별점으로 1차 분류(AI 비용 0) → 키워드 추출만 형태소 분석 사용

---

## ⚠️ 개인정보 주의 (반드시 읽기)

알파리뷰 원본 CSV에는 **작성자명·작성자ID·주문번호** 등 개인정보가 들어있다.
저장소가 공개면 그대로 노출되므로, `data/` 에는 **분석에 필요한 7개 컬럼만** 남긴 CSV를 올린다:

```
리뷰평점, 상품명, 상품코드, 리뷰내용, 리뷰작성일시, 작성자종류, 빠른리뷰
```

이 7개만 있으면 리포트는 동일하게 생성된다(이미 그렇게 정리된 샘플이 들어있다).
발행되는 `index.html` 자체는 이름 없는 후기 일부만 인용하므로(집계 + 익명 인용) 공개돼도 안전하다.
