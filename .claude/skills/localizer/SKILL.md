---
name: localizer
description: tail-analyzed의 분석본을 각국 언어(영어, 중국어 번체, 일본어)로 로컬라이즈하여 tail-localized/{lang} 폴더에 저장하는 진입점
---

# Localizer Skill (진입점)

이 스킬은 로컬라이즈 에이전트를 spawn하는 진입점이다.

## 사용법

사용자가 로컬라이즈를 요청하면 `.claude/agents/localizer.md`에 정의된 에이전트를 Agent 도구로 spawn한다.

예시 트리거:
- "여우와 두루미 로컬라이즈해줘"
- "/localizer 여우와 두루미"
- "/localizer all" (전체 로컬라이즈)

## 규약 (Convention)

### 입력

- 분석 완료 마크다운: `tail-analyzed/{스토리명}.md`

### 출력

- 영어: `tail-localized/en/{스토리명}.md`
- 중국어 번체: `tail-localized/zh-tw/{스토리명}.md`
- 일본어: `tail-localized/jp/{스토리명}.md`

## 동작

1. 사용자의 요청에서 대상 스토리명을 파악한다
2. `tail-analyzed/{스토리명}.md`가 존재하는지 확인한다 (없으면 에러 보고)
3. 출력 폴더(`tail-localized/en/`, `tail-localized/zh-tw/`, `tail-localized/jp/`)가 없으면 생성한다
4. **언어별로 localizer 에이전트를 병렬 spawn한다** (3개 동시)
   - 각 에이전트에 스토리명과 대상 언어를 전달한다
   - 동작: 분석본을 읽고, `<!-- expressions -->` 뜻풀이를 대상 언어로 번역하고 frontmatter의 `reasoning` 필드 제거 + `lang` 필드 추가
   - 출력: `tail-localized/{lang}/{스토리명}.md`
5. 모든 에이전트 완료 후 결과를 사용자에게 보고한다

## 결과물 규칙

- frontmatter에서 `reasoning` 필드는 **제거**한다 (난이도 산출 근거는 로컬라이즈 결과물에 포함하지 않는다)
- `lang` 필드를 추가하고, 나머지 frontmatter 필드는 원본 그대로 유지한다
- `<sub>` 태그나 `<!-- translation -->` 블록은 **생성하지 않는다** — 산문 번역은 story-translator의 책임이며 tail-translated에 저장된다

## 다른 파이프라인과의 관계

- **story-translator와 독립**: localizer(tail-analyzed → tail-localized)와 story-translator(tail-story → tail-translated)는 서로 참조하지 않으므로 동시에 실행 가능하다
- **book-editor가 두 결과물을 병합**: localized의 expressions·frontmatter와 translated의 `<sub>`·`<!-- translation -->`은 book-editor 단계에서 tail-story 본문과 함께 하나의 bookform으로 조합된다

## 병렬 실행

- **언어별 병렬**: 같은 스토리의 3개 언어는 독립적이므로 동시 실행
- **스토리별 병렬**: 여러 스토리를 요청한 경우에도 스토리별로 병렬 실행 가능
