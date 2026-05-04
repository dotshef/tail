---
name: story-translator
description: tail-story의 한국어 본문을 각국 언어(영어, 일본어)로 번역하여 tail-translated/{lang} 폴더에 저장하는 진입점
---

# Story Translator Skill (진입점)

이 스킬은 story-translator 에이전트를 spawn하는 진입점이다.

## 사용법

사용자가 번역을 요청하면 `.claude/agents/story-translator.md`에 정의된 에이전트를 Agent 도구로 spawn한다.

예시 트리거:
- "여우와 두루미 번역해줘"
- "/story-translator 여우와 두루미"
- "/story-translator all" (전체 번역)

## 규약 (Convention)

### 입력

- 스토리 본문: `tail-story/{스토리명}.md`

### 출력

- 영어: `tail-translated/en/{스토리명}.md`
- 일본어: `tail-translated/jp/{스토리명}.md`

## 동작

1. 사용자의 요청에서 대상 스토리명을 파악한다
2. `tail-story/{스토리명}.md`가 존재하는지 확인한다 (없으면 에러 보고)
3. 출력 폴더(`tail-translated/en/`, `tail-translated/jp/`)가 없으면 생성한다
4. **언어별로 story-translator 에이전트를 병렬 spawn한다** (2개 동시)
   - 각 에이전트에 스토리명과 대상 언어를 전달한다
   - 동작: story 본문을 읽고, `#`/`##` 제목에 `<sub>` 병렬 표기 추가, 각 페이지 본문 뒤에 `<!-- translation -->` 블록 삽입
   - 출력: `tail-translated/{lang}/{스토리명}.md`
5. 모든 에이전트 완료 후 결과를 사용자에게 보고한다

## 결과물 규칙

- frontmatter는 생성하지 않는다 (tail-story에 frontmatter가 없으므로)
- `<!-- translation -->` 블록은 페이지 단위로 하나씩 삽입한다 (장 단위 병합은 book-editor의 책임)
- expressions·gloss는 다루지 않는다 (localizer의 책임)

## 병렬 실행

- **언어별 병렬**: 같은 스토리의 2개 언어는 독립적이므로 동시 실행
- **스토리별 병렬**: 여러 스토리를 요청한 경우에도 스토리별로 병렬 실행 가능
- **localizer와 독립 실행**: story-translator와 localizer는 서로 참조하지 않으므로 동시 실행 가능
