---
name: image-generator
description: temp-story의 동화 마크다운을 읽어 각 컷별로 프롬프트를 작성하고 Gemini 이미지를 생성하는 진입점
---

# Image Generator Skill (진입점)

이 스킬은 두 에이전트를 순차적으로 오케스트레이션하는 진입점이다.

1. **prompt-writer** — 마크다운에서 각 컷의 본문·대사를 읽고 시각적 프롬프트를 작성해 `prompts.json`에 저장
2. **image-generator** — `prompts.json`을 읽고 Gemini API로 각 컷 이미지를 생성

## 사용법

사용자가 특정 스토리의 이미지 생성을 요청하면 아래 파이프라인을 실행한다.

예시 트리거:
- "여우와 두루미 이미지 생성해줘"
- "/image-generator 여우와 두루미"

## 규약 (Convention)

### 입력

- 스토리 마크다운: `temp-story/{스토리명}.md`
  - `#### 컷 N - {장면 설명}` 형식으로 컷이 정의되어 있음
- 레퍼런스 이미지: `temp-image/{스토리명}/ref-image/*.png|jpg|jpeg|webp`
  - 사용자가 직접 넣어둔다 (캐릭터, 스타일 레퍼런스)
  - 없으면 이미지 생성 단계는 중단된다

### 중간 산출물

- 프롬프트 파일: `temp-image/{스토리명}/prompts.json`
  - prompt-writer가 생성
  - 사용자가 수동 편집할 수 있음 (JSON 스키마는 prompt-writer 에이전트 문서 참조)

### 출력

- 컷 이미지: `temp-image/{스토리명}/cuts/컷_{N:02d}.png`

## 동작

1. 사용자의 요청에서 대상 스토리명을 파악한다
2. `temp-story/{스토리명}.md`가 존재하는지 확인한다 (없으면 에러 보고)
3. **prompt-writer 에이전트를 Agent 도구로 spawn한다**
   - 입력: 스토리명
   - 출력: `temp-image/{스토리명}/prompts.json`
   - 기존 prompts.json이 있어도 **덮어쓴다**
4. `temp-image/{스토리명}/ref-image/`에 레퍼런스 이미지가 있는지 확인한다
   - 없으면 사용자에게 레퍼런스를 먼저 넣어달라고 요청하고 **이미지 생성 단계는 중단**한다
   - (prompts.json은 이미 작성되어 있으므로 사용자가 레퍼런스 준비 후 skill을 재호출하면 이어서 진행 가능)
5. **image-generator 에이전트를 Agent 도구로 spawn한다**
   - 입력: 스토리명
   - 동작: prompts.json의 각 컷에 대해 gen_image.py 호출
   - 출력: `temp-image/{스토리명}/cuts/*.png`
6. 두 에이전트의 완료 후 결과를 사용자에게 보고한다
   - 작성된 컷 수
   - 생성된 이미지 수
   - 실패 항목

## 병렬 실행

여러 스토리를 한 번에 요청한 경우 (예: "temp-story 전부 이미지 생성"):

- **스토리별로 병렬 spawn** — 서로 다른 스토리는 독립적이므로 여러 (prompt-writer + image-generator) 쌍을 동시 실행 가능
- 단, **같은 스토리 내에서는 prompt-writer → image-generator 순차 실행** (이미지 생성은 prompts.json에 의존)

## 주의사항

- 이미지 생성은 Gemini API 비용이 발생한다 (장당 약 $0.04)
- 동일 스토리를 재실행할 경우:
  - `prompts.json`은 **덮어쓴다** (prompt-writer 재작성)
  - `cuts/*.png`는 **덮어쓴다** (image-generator 재생성)
- 레퍼런스 이미지가 없으면 이미지 생성 단계는 실패하지만, prompts.json은 이미 작성되어 있으므로 사용자가 레퍼런스 준비 후 skill을 재호출하면 이어서 진행할 수 있다
- `GEMINI_API_KEY`는 프로젝트 루트의 `.env`에 이미 설정되어 있다 (스크립트가 자동 로드)
