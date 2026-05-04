# Exercise 에이전트 도입 계획

Graded Reader 요건 중 **장별 독해 확인 질문**과 **장별 어휘·문법 연습 문제**를 추가하기 위한 파이프라인 확장안.

### 목표

각 장 끝에 다음을 삽입하고, 책 말미에 전체 정답 키 섹션을 붙인다.

- **독해 확인** 3~5문제 (사실형 객관식 + 인과 단답 + 추론)
- **어휘 연습** 3~4문제 (빈칸 채우기, 의미 매칭, 문맥 활용)
- **문법 연습** 2~3문제 (문형 완성, 문장 변환, 오류 찾기)

문제 소재는 `tail-analyzed`에 이미 선별된 expressions로 한정하여 학습 범위 일관성을 유지한다.

### 신규 에이전트

#### exercise-writer
- **입력**: `tail-analyzed/{스토리명}.md`
- **출력**: `tail-exercises/{스토리명}.md`
- **역할**: 한국어 기준 문제 원본 생성. 문제·선택지·정답·해설 모두 포함.
- **실행 시점**: `difficulty-analyzer` 완료 후.

#### exercise-localizer
- **입력**: `tail-exercises/{스토리명}.md`
- **출력**: `tail-exercises-localized/{lang}/{스토리명}.md`
- **역할**: 지시문·보기 설명·해설만 대상 언어로 번역. 본문 인용·어휘·문법 대상·정답은 한국어 유지.
- **실행 시점**: `exercise-writer` 완료 후. `localizer`와 병렬 가능.

### 파이프라인 배치

기존 상단(분석) 레인에서 분기하는 제3 레인으로 추가한다.

```
tail-raw ─► difficulty-analyzer ─► tail-analyzed ─► localizer ─► tail-localized/{lang} ─┐
                                         │                                              │
                                         └─► exercise-writer ─► tail-exercises          │
                                                    └─► exercise-localizer ─►           │
                                                        tail-exercises-localized/{lang}─┤
                                                                                        ▼
tail-raw ─► story-writer ─► tail-story ─► story-translator ─► tail-translated/{lang} ──► book-editor ─► tail-bookform/{lang} ─► pdf-generator ─► tail-pdf/{lang}
```

### tail-analyzed에서 분기하는 이유

- expressions가 이미 선별되어 있어 어휘·문법 문제 타겟을 재사용 가능.
- 본문과 expressions 주석이 한 파일에 있어 독해 질문 생성에도 충분.
- `tail-raw`에서 다시 뽑으면 학습 범위 불일치가 발생.

### writer/localizer 분리 이유

기존 `difficulty-analyzer → localizer` 패턴과 동일한 근거.

- 문제·정답은 한국어 기준으로 한 번만 생성 (단일 소스).
- 언어 추가 시 localizer만 재실행하면 되고, 정답 일관성이 자동 보장.

### 소스 파일 포맷 (언어 중립)

expressions와 동일한 HTML 주석 패턴으로 book-editor 파싱을 단순화한다.

```markdown
<!-- exercises:chapter-1
[comprehension]
- type: choice
  q: 여우가 두루미를 초대한 진짜 이유는?
  choices: [친해지려고, 놀리려고, 요리를 자랑하려고, 사과하려고]
  answer: 2
- type: short
  q: 여우는 수프를 어떤 그릇에 담았는가?
  answer: 넓적하고 얕은 접시

[vocabulary]
- type: fill
  sentence: 여우는 처음부터 두루미를 놀려 먹을 ____이었다.
  answer: 속셈
  source: 속셈

[grammar]
- type: transform
  base: 부리 끝이 수프에 닿는다
  target_pattern: -을 뿐이다
  answer: 부리 끝이 수프에 닿을 뿐이다
-->
```

`q`·`choices`의 지시문·선택지만 로컬라이즈 대상, 나머지는 원문 유지.

### book-editor 수정 범위

- 각 장 translation 블록 뒤에 해당 장 exercise 블록 삽입.
- 책 맨 끝에 "정답 (Answer Key)" 섹션 추가. 각 장의 answer 필드를 취합.
- pdf-builder CSS에 exercise 블록·정답 섹션 스타일 추가.

### 품질 확보 포인트

- **난이도 동기화**: frontmatter `difficulty.level`에 따라 객관식/단답 비율 조정 (저레벨은 객관식 위주).
- **분량 상한**: 장당 최대 10문제로 고정해 PDF 페이지 수 예측 가능.
- **expressions 외 어휘 금지**: exercise-writer가 본문에서 새 어휘를 뽑지 않도록 제약.

### 실행 순서 요약

1. `difficulty-analyzer` 완료 → `tail-analyzed` 생성
2. `exercise-writer` 실행 → `tail-exercises` 생성
3. `localizer`와 `exercise-localizer` 병렬 실행
4. `story-translator`까지 포함해 모든 로컬라이즈드 산출물 준비 완료
5. `book-editor` 실행 → `tail-bookform/{lang}` 생성
6. `pdf-generator` 실행 → `tail-pdf/{lang}` 생성
