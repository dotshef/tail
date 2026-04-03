---
name: translator
description: gutenberg-raw 영문 원문을 한국어로 순수 번역
---

# Translator Skill

gutenberg-raw의 영문 원문을 한국어로 순수 번역하는 스킬.

## 역할 범위

- 원문의 내용을 자연스러운 한국어로 **번역만** 한다
- 구조 변경, 에피소드 분할, 대화문 추가/확장, 등장인물 소개 등 재구성은 하지 않는다
- 원문에 없는 내용을 창작하지 않는다

## 입력

- `gutenberg-raw/{id}_{slug}.txt` 내의 특정 이야기
- `tail-candidates/tail-candidates.csv`에서 해당 이야기의 `title_original`로 원문 내 위치를 찾는다

## 출력

- 저장 경로: `translated/{no}_{title_ko}.md`
- no는 tail-candidates.csv의 번호 (예: `01_개미와_베짱이.md`)

## 번역 규칙

### 문체

- 의역 기조: 한국어로 자연스럽게 읽히는 것을 우선한다
- 단, 원문의 의미를 왜곡하지 않는다
- 고유명사는 원문 그대로 유지하되, 한국어 독자에게 익숙한 이름이 있으면 병기한다 (예: Tortoise → 거북이)
- 문맥을 파악하여 동물 이름, 사물 이름 등 일반 명사는 한국어로 번역한다

### 구조

- 원문의 문단 구분을 그대로 유지한다
- 원문의 대화문은 대화문으로, 서술문은 서술문으로 번역한다
- 원문에 제목/소제목이 있으면 그대로 번역한다
- 원문에 삽화 설명, 편집자 주석 등 본문이 아닌 부분은 제거한다

### 파일 헤더

번역 파일 상단에 다음 메타데이터를 포함한다:

```markdown
---
no: {번호}
title_ko: {한국어 제목}
title_original: {원제}
source: gutenberg-raw/{파일명}
translator: claude
---
```

## 주의사항

- gutenberg-raw 파일에는 여러 이야기가 포함된 선집(anthology)이 많다
- 반드시 해당 이야기만 추출하여 번역한다
- 원문에서 해당 이야기를 찾지 못하면 번역하지 않고 에러를 보고한다
