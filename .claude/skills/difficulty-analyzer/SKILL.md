---
name: difficulty-analyzer
description: tail-raw의 동화 마크다운을 읽어 외국인 학습자 기준 한국어 난이도를 분석하고 tail-diff-analyzed에 저장하는 진입점
---

# Difficulty Analyzer Skill (진입점)

이 스킬은 난이도 분석 에이전트를 spawn하는 진입점이다.

## 사용법

사용자가 난이도 분석을 요청하면 `.claude/agents/difficulty-analyzer.md`에 정의된 에이전트를 Agent 도구로 spawn한다.

예시 트리거:
- "여우와 두루미 난이도 분석해줘"
- "/difficulty-analyzer 여우와 두루미"
- "/difficulty-analyzer all" (전체 분석)

## 규약 (Convention)

### 입력

- 스토리 마크다운: `tail-raw/{스토리명}.md`

### 출력

- 분석 완료 마크다운: `tail-diff-analyzed/{스토리명}.md`
  - 원본 내용 + frontmatter에 난이도 메타데이터 추가

## 동작

1. 사용자의 요청에서 대상 스토리명을 파악한다
2. `tail-raw/{스토리명}.md`가 존재하는지 확인한다 (없으면 에러 보고)
3. `tail-diff-analyzed/` 폴더가 없으면 생성한다
4. **difficulty-analyzer 에이전트를 Agent 도구로 spawn한다**
   - 입력: 스토리명
   - 동작: raw 마크다운을 읽고 난이도 분석 후 메타데이터 태깅
   - 출력: `tail-diff-analyzed/{스토리명}.md`
5. 에이전트 완료 후 결과를 사용자에게 보고한다

## 병렬 실행

여러 스토리를 한 번에 요청한 경우 (예: "전부 분석해줘"):

- **스토리별로 병렬 spawn** — 서로 다른 스토리는 독립적이므로 여러 에이전트를 동시 실행 가능
