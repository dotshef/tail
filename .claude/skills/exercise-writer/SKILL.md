---
name: exercise-writer
description: tail-analyzed의 분석본을 읽고 한국어 기준 장별 연습 문제(독해 확인, 어휘, 문법)를 생성하여 tail-exercises/{스토리명}.md에 저장하는 진입점
---

# Exercise Writer Skill (진입점)

이 스킬은 exercise-writer 에이전트를 spawn하는 진입점이다.

## 사용법

사용자가 연습 문제 생성을 요청하면 `.claude/agents/exercise-writer.md`에 정의된 에이전트를 Agent 도구로 spawn한다.

예시 트리거:
- "여우와 두루미 연습 문제 만들어줘"
- "/exercise-writer 여우와 두루미"

## 규약 (Convention)

### 입력

- 분석 완료 마크다운: `tail-analyzed/{스토리명}.md`

### 출력

- `tail-exercises/{스토리명}.md`

## 동작

1. 사용자의 요청에서 대상 스토리명을 파악한다
2. `tail-analyzed/{스토리명}.md`가 존재하는지 확인한다 (없으면 에러 보고)
3. 출력 폴더(`tail-exercises/`)가 없으면 생성한다
4. **exercise-writer 에이전트를 spawn한다**
   - 에이전트에 스토리명을 전달한다
   - 동작: 분석본을 읽고 expressions를 소재로 장별 연습 문제(독해/어휘/문법)를 한국어로 생성, 정답·해설 포함하여 저장
   - 출력: `tail-exercises/{스토리명}.md`
5. 완료 후 결과를 사용자에게 보고한다

## 다른 파이프라인과의 관계

- **difficulty-analyzer 이후 실행**: tail-analyzed가 입력이므로 분석이 완료되어 있어야 함
- **localizer와 병렬 가능**: 둘 다 tail-analyzed를 읽지만 서로 참조하지 않음
- **exercise-localizer의 선행**: exercise-writer가 끝나야 exercise-localizer 실행 가능

## 병렬 실행

- **스토리별 병렬**: 여러 스토리를 요청한 경우 스토리별로 병렬 실행 가능
- **단일 스토리**: 언어 fanout이 없으므로 1개 에이전트만 spawn
