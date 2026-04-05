---
name: translator
description: tail-raw 영문 원문을 한국어로 순수 번역
---

# Translator Skill (진입점)

이 스킬은 번역 에이전트를 spawn하는 진입점이다.

## 사용법

사용자가 번역을 요청하면 `.claude/agents/translator.md`에 정의된 translator 에이전트를 Agent 도구로 spawn한다.

## 동작

1. 사용자의 요청에서 번역 대상을 파악한다 (id 범위, 제목, 카테고리 등)
2. `tail-catalog/checklist.csv`에서 대상 항목을 확인한다
3. Agent 도구로 translator 에이전트를 spawn한다
   - 병렬 번역이 가능한 경우 여러 에이전트를 동시에 spawn한다
   - 프롬프트에 번역 대상 id와 title_en을 명시한다
4. 에이전트 완료 후 결과를 사용자에게 보고한다
