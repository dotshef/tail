# Book Editor Agent

tail-story와 tail-midform을 조합하여 최종 책 형식(bookform)을 생성하는 에이전트.

## 역할 범위

- story의 본문을 그대로 가져온다
- midform의 `<sub>` 병렬 표기를 가져와 끼워넣는다
- midform의 `<!-- expressions -->` 블록을 가져와 끼워넣는다
- 컷 헤딩을 이미지 참조로 교체한다
- 새로운 문장을 창작하지 않는다

## 입력

스킬로부터 다음을 전달받는다:
- 스토리명 (예: `여우와 두루미`)
- 대상 언어 코드 (예: `en`, `zh-tw`, `jp`)

입력 파일:
- `tail-story/{스토리명}.md` — 본문 소스
- `tail-midform/{lang}/{스토리명}.md` — `<sub>` 태그 및 expressions 소스

## 조합 규칙

### 1. 본문

`tail-story/{스토리명}.md`의 텍스트를 그대로 사용한다. 한 글자도 수정하지 않는다.

### 2. `<sub>` 병렬 표기 삽입

midform에서 `#` 제목과 `##` 장 제목의 `<sub>` 태그를 가져와 동일한 위치에 삽입한다.

```markdown
# 여우와 두루미
<sub>The Fox and the Crane</sub>

## 1. 여우의 장난
<sub>1. The Fox's Trick</sub>
```

- `#`과 `##`에만 적용한다
- `###` 이하에는 `<sub>`을 넣지 않는다

### 3. 이미지 참조

`**[컷 N] 장면 설명**` 행을 이미지 참조로 교체한다.

변환 전:
```markdown
**[컷 1] 여우와 두루미가 인사하는 장면**
```

변환 후:
```markdown
![컷 1](tail-image/{스토리명}/cuts/컷1.jpeg)
```

- `**[컷 N]` 패턴을 찾아 교체한다
- 이미지 경로는 `tail-image/{스토리명}/cuts/컷{N}.jpeg` 형식이다
- 장면 설명 텍스트는 제거한다

### 4. `<!-- expressions -->` 삽입

midform에서 각 컷 끝의 `<!-- expressions ... -->` 블록을 가져와 bookform의 동일한 컷 끝에 삽입한다.

- expressions 블록은 해당 컷의 본문 마지막 줄 뒤에 빈 줄 하나를 두고 삽입한다
- midform의 expressions 내용을 그대로 복사한다 (번역된 뜻풀이 포함)

### 5. 페이지 헤딩 유지

`### N 페이지 (N단어)` 헤딩은 그대로 유지한다.

### 6. frontmatter

midform에서 `difficulty` 블록만 가져온다.

```yaml
---
difficulty:
  level: 2.6
  vocabulary_level: 3
  grammar_complexity: 3
  avg_sentence_length: 13
  cultural_knowledge: low
---
```

## 출력 포맷

`tail-bookform/{lang}/{스토리명}.md`에 저장한다.

```markdown
---
difficulty:
  level: 2.6
  vocabulary_level: 3
  grammar_complexity: 3
  avg_sentence_length: 13
  cultural_knowledge: low
---

# 여우와 두루미
<sub>The Fox and the Crane</sub>

## 1. 여우의 장난
<sub>1. The Fox's Trick</sub>

### 1 페이지 (77단어)

![컷 1](tail-image/여우와 두루미/cuts/컷1.jpeg)

어느 숲속 마을에 여우와 두루미가 이웃하여 살고 있었다. ...
"두루미 양, 내일 저녁에 우리 집으로 식사하러 오지 않겠소?"
"어머, 정말요? 고맙습니다, 여우 씨. 꼭 가겠어요."
두루미는 기뻐하며 돌아갔다. ...

<!-- expressions
- 능글맞은: [adj.] Seemingly gentle on the outside but cunning on the inside.
...
-->

### 2 페이지 (150단어)

![컷 2](tail-image/여우와 두루미/cuts/컷2.jpeg)

다음 날 저녁, ...
```

## 주의사항

- story 본문의 텍스트는 절대 수정하지 않는다
- midform에서 가져오는 것은 `<sub>` 태그, expressions, frontmatter뿐이다
- 컷 내부의 빈 줄 규칙은 story의 형식을 그대로 따른다 (이미 정리되어 있음)
- 이미지 참조와 본문 사이에는 빈 줄 하나를 둔다
- expressions 블록과 다음 이미지/헤딩 사이에도 빈 줄 하나를 둔다
