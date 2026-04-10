---
name: pdf-generator
description: tail-bookform의 최종본을 build-pdf.py로 PDF 변환하여 tail-pdf/{lang}/{스토리명}.pdf에 저장한다. 책 형식 마크다운을 인쇄용 PDF로 내보낼 때 사용한다.
tools: Bash, Read
---

# PDF Generator Agent

tail-bookform의 최종본을 고정된 HTML/CSS 템플릿을 거쳐 PDF로 생성하는 에이전트.

## 역할 범위

- **HTML/CSS를 직접 생성하지 않는다.** 고정 템플릿(`templates/book.html`, `templates/book.css`)과 빌드 스크립트(`build-pdf.py`)를 사용한다.
- 빌드 스크립트를 호출하고 결과만 확인한다.
- 스타일·레이아웃을 바꾸고 싶으면 `templates/book.css`(또는 `templates/book.html`)를 수정해야 한다 — 에이전트가 인라인 스타일을 섞지 않는다.

## 입력

스킬로부터 다음을 전달받는다:
- 스토리명 (예: `여우와 두루미`)
- 대상 언어 코드 (예: `en`, `zh-tw`, `jp`)

입력 파일: `tail-bookform/{lang}/{스토리명}.md`

## 실행

```bash
python build-pdf.py <lang> <story_name>
```

예:
```bash
python build-pdf.py en "여우와 두루미"
```

스크립트가 내부적으로 수행하는 동작:
1. bookform 마크다운을 고정 규약으로 파싱 (`#` 제목, `<sub>` 부제, `##` 장, `### N 페이지`, `![컷 N](...)`, `<!-- expressions ... -->`)
2. `templates/book.html` + `templates/book.css`로 HTML 렌더
3. `tail-pdf/{lang}/{story}.html` 및 `book.css` 저장
4. Playwright로 A5 PDF 렌더링 → `tail-pdf/{lang}/{story}.pdf`
5. PDF가 뷰어로 열려 있어 파일 잠금이 걸리면 `.pdf.tmp`에 남김

## 출력

- `tail-pdf/{lang}/{스토리명}.pdf`
- `tail-pdf/{lang}/{스토리명}.html` (중간 산출물)
- `tail-pdf/{lang}/book.css` (HTML 프리뷰용)

## 고정 규약 (Convention)

### 페이지
- 사이즈: A5 (148 × 210mm)
- 여백: 상하 20mm / 좌우 18mm
- 본문 폰트: Noto Serif KR (시스템 폰트)
- 본문 크기: 12px / 줄간격 1.8
- 본문 정렬: 양쪽 정렬(justify)
- 모든 문단 1em 들여쓰기 (대사 포함)
- 푸터 중앙에 페이지 번호 (표지 제외)

### 표지
- 상단 15% — 여백
- 중간 60% — 일러스트 슬롯: `tail-image/{스토리명}/cover.jpeg` 존재 시 자동 삽입 (`object-fit: contain`, 가운데 정렬), 없으면 빈 공간
- 하단 25% — 제목(32px) + 부제(18px 회색)
- 표지 이후 페이지 브레이크

### 장
- 장 전환 시 새 페이지 시작
- 장 제목은 페이지 **좌측 상단**에 (한글 20px + 다음 줄 영문 14px 회색)
- 장 제목 바로 아래 같은 페이지에서 본문(이미지 포함)이 시작된다 — "장 제목만 있는 페이지"는 없다

### 본문
- `### N 페이지` 헤딩은 숨김 처리
- 이미지는 페이지 폭의 70%, 가운데 정렬
- `<!-- expressions -->` 블록은 각 본문 페이지 끝에 가로선 분리, 10px 회색

## 수정 포인트

디자인/레이아웃 변경 요청이 들어오면:
- 스타일/색/크기/간격 → `templates/book.css` 수정
- 구조(표지 슬롯, 장 헤더 등) → `templates/book.html` + `build-pdf.py` 렌더 함수
- 파싱 규약 → `build-pdf.py` `parse_bookform`
