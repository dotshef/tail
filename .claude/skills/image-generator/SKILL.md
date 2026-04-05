---
name: image-generator
description: temp-story의 동화 마크다운을 읽어 각 컷별로 Gemini 이미지를 생성하는 진입점
---

# Image Generator Skill (진입점)

이 스킬은 이미지 생성 에이전트를 spawn하는 진입점이다.

## 사용법

사용자가 특정 스토리의 이미지 생성을 요청하면 `.claude/agents/image-generator.md`에 정의된 image-generator 에이전트를 Agent 도구로 spawn한다.

예시 트리거:
- "여우와 두루미 이미지 생성해줘"
- "/image-generator 여우와 두루미"

## 규약 (Convention)

### 입력

- 스토리 마크다운: `temp-story/{스토리명}.md`
  - `#### 컷 N - {장면 설명}` 형식으로 컷이 정의되어 있음
- 레퍼런스 이미지: `temp-image/{스토리명}/ref-image/*.png|jpg`
  - 사용자가 직접 넣어둔다 (캐릭터, 스타일 레퍼런스)
  - 레퍼런스가 없으면 에이전트는 생성을 거부하고 사용자에게 요청한다

### 출력

- 생성된 컷 이미지: `temp-image/{스토리명}/cuts/컷_{N}.png`
- 메타데이터(선택): `temp-image/{스토리명}/metadata.json`

## 동작

1. 사용자의 요청에서 대상 스토리명을 파악한다
2. `temp-story/{스토리명}.md`가 존재하는지 확인한다
3. `temp-image/{스토리명}/ref-image/`에 레퍼런스 이미지가 있는지 확인한다
   - 없으면 사용자에게 레퍼런스를 먼저 넣어달라고 요청하고 중단한다
4. Agent 도구로 image-generator 에이전트를 spawn한다
   - 여러 스토리를 병렬로 처리할 수 있는 경우 여러 에이전트를 동시에 spawn한다
   - 프롬프트에 스토리명과 절대 경로를 명시한다
5. 에이전트 완료 후 결과(생성된 컷 수, 실패 항목)를 사용자에게 보고한다

## 주의사항

- 이미지 생성은 Gemini API를 호출하므로 비용이 발생한다 (장당 약 $0.04)
- 동일 스토리를 재실행할 경우 기존 `cuts/` 폴더의 파일이 덮어써진다 — 필요시 사용자 확인 후 진행
- 레퍼런스 이미지가 캐릭터 일관성의 핵심이므로, 레퍼런스 없이는 생성하지 않는다
