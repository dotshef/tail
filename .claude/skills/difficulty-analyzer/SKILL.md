---
name: difficulty-analyzer
description: tail-raw의 동화 마크다운을 읽어 외국인 학습자 기준 한국어 난이도를 분석하고 tail-analyzed에 저장하는 진입점
---

# Difficulty Analyzer Skill (진입점)

이 스킬은 두 에이전트를 순차적으로 오케스트레이션하는 진입점이다.

1. **vocab-analyzer** — `analyze-vocab.py`를 실행하여 어휘 분석 JSON 생성
2. **difficulty-analyzer** — JSON + 본문을 읽고 최종 난이도 판정 + expressions 추가

## 사용법

예시 트리거:
- "여우와 두루미 난이도 분석해줘"
- "/difficulty-analyzer 여우와 두루미"
- "/difficulty-analyzer all" (전체 분석)

## 규약 (Convention)

### 입력

- 스토리 마크다운: `tail-raw/{스토리명}.md`

### 중간 산출물

- 어휘 분석 JSON: `tail-analyzed/{스토리명}/vocab.json` (vocab-analyzer가 생성)

### 출력

- 분석 완료 마크다운: `tail-analyzed/{스토리명}/analysis.md`

## 동작

1. 사용자의 요청에서 대상 스토리명을 파악한다
2. `tail-raw/{스토리명}.md`가 존재하는지 확인한다 (없으면 에러 보고)
3. `tail-analyzed/` 폴더가 없으면 생성한다
4. **vocab-analyzer 에이전트를 spawn한다** (순차 — difficulty-analyzer보다 먼저)
   - 입력: 스토리명
   - 동작: `analyze-vocab.py` 실행
   - 출력: `tail-analyzed/{스토리명}/vocab.json`
5. vocab-analyzer 완료 후, **difficulty-analyzer 에이전트를 spawn한다**
   - 입력: 스토리명
   - 동작: vocab JSON + raw 마크다운을 읽고 난이도 분석
   - 출력: `tail-analyzed/{스토리명}/analysis.md`
6. 모든 에이전트 완료 후 결과를 사용자에게 보고한다

## 병렬 실행

여러 스토리를 한 번에 요청한 경우 (예: "전부 분석해줘"):

- **스토리별로 병렬 실행** — 서로 다른 스토리는 독립적이므로 동시 실행 가능
- 단, **같은 스토리 내에서는 vocab-analyzer → difficulty-analyzer 순차 실행** (난이도 분석은 vocab JSON에 의존)