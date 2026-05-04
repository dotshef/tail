---
name: exercise-localizer
description: tail-exercises의 한국어 연습 문제에서 지시문·해설만 각국 언어(영어, 일본어)로 번역하여 tail-exercises-localized/{lang} 폴더에 저장하는 진입점
---

# Exercise Localizer Skill (진입점)

이 스킬은 exercise-localizer 에이전트를 spawn하는 진입점이다.

## 사용법

사용자가 연습 문제 로컬라이즈를 요청하면 `.claude/agents/exercise-localizer.md`에 정의된 에이전트를 Agent 도구로 spawn한다.

예시 트리거:
- "여우와 두루미 연습 문제 로컬라이즈해줘"
- "/exercise-localizer 여우와 두루미"
- "/exercise-localizer all" (전체 로컬라이즈)

## 규약 (Convention)

### 입력

- 한국어 연습 문제: `tail-exercises/{스토리명}.md`

### 출력

- 영어: `tail-exercises-localized/en/{스토리명}.md`
- 일본어: `tail-exercises-localized/jp/{스토리명}.md`

## 동작

1. 사용자의 요청에서 대상 스토리명을 파악한다
2. `tail-exercises/{스토리명}.md`가 존재하는지 확인한다 (없으면 에러 보고)
3. 출력 폴더(`tail-exercises-localized/en/`, `tail-exercises-localized/jp/`)가 없으면 생성한다
4. **언어별로 exercise-localizer 에이전트를 병렬 spawn한다** (2개 동시)
   - 각 에이전트에 스토리명과 대상 언어를 전달한다
   - 동작: 한국어 연습 문제를 읽고 지시문·해설만 대상 언어로 번역, 정답·본문 인용·한국어 학습 대상은 그대로 유지
   - 출력: `tail-exercises-localized/{lang}/{스토리명}.md`
5. 모든 에이전트 완료 후 결과를 사용자에게 보고한다

## 다른 파이프라인과의 관계

- **exercise-writer 이후 실행**: tail-exercises가 입력
- **localizer와 독립**: 서로 참조하지 않으므로 동시 실행 가능
- **book-editor가 결과 사용**: 장별 exercise 블록을 bookform에 합성

## 병렬 실행

- **언어별 병렬**: 같은 스토리의 2개 언어는 독립적이므로 동시 실행
- **스토리별 병렬**: 여러 스토리를 요청한 경우에도 스토리별로 병렬 실행 가능
- **localizer와 동시 실행 가능**: 입력 파일이 다르므로 충돌 없음
