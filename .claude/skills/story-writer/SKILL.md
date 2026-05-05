---
name: story-writer
description: tail-raw의 동화 마크다운에서 대사 태그를 제거하여 tail-story에 저장하는 진입점
---

# Story Writer Skill (진입점)

이 스킬은 story-writer 에이전트를 spawn하는 진입점이다.

## 사용법

예시 트리거:
- "여우와 두루미 스토리 만들어줘"
- "/story-writer 여우와 두루미"
- "/story-writer all" (전체 변환)

## 규약 (Convention)

### 입력

- 원본 마크다운: `tail-raw/{스토리명}.md`

### 출력

- `tail-story/{스토리명}/story.md`

## 동작

1. 사용자의 요청에서 대상 스토리명을 파악한다
2. `tail-raw/{스토리명}.md`가 존재하는지 확인한다 (없으면 에러 보고)
3. `tail-story/` 폴더가 없으면 생성한다
4. **story-writer 에이전트를 spawn한다**
   - 입력: 스토리명
   - 동작: raw를 읽고 대사 태그(`- 캐릭터:`)와 원작자를 제거
   - 출력: `tail-story/{스토리명}/story.md`
5. 에이전트 완료 후 결과를 사용자에게 보고한다

## 병렬 실행

- **스토리별 병렬**: 여러 스토리를 요청한 경우 스토리별로 병렬 실행 가능
