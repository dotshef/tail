---
name: pdf-generator
description: tail-bookform의 최종본을 PDF로 변환하여 tail-pdf/{lang}에 저장하는 진입점
---

# PDF Generator Skill (진입점)

이 스킬은 pdf-generator 에이전트를 spawn하는 진입점이다.

## 사용법

예시 트리거:
- "여우와 두루미 PDF 만들어줘"
- "/pdf-generator 여우와 두루미 en"
- "/pdf-generator 여우와 두루미 all" (전체 언어)

## 규약 (Convention)

### 입력

- 최종 bookform: `tail-bookform/{lang}/{스토리명}.md`

### 출력

- `tail-pdf/{lang}/{스토리명}.pdf`

## 동작

1. 사용자의 요청에서 대상 스토리명과 언어를 파악한다
2. `tail-bookform/` 하위 폴더를 탐색하여 해당 스토리의 언어별 bookform 존재 여부를 확인한다
   - 언어를 지정한 경우 해당 언어만, "all"이면 존재하는 모든 언어를 처리한다
   - 없으면 에러 보고
3. `tail-pdf/{lang}/` 폴더가 없으면 생성한다
4. **언어별로 pdf-generator 에이전트를 병렬 spawn한다**
   - 각 에이전트에 스토리명과 대상 언어를 전달한다
   - 동작: bookform → HTML 생성 → Puppeteer로 PDF 변환
   - 출력: `tail-pdf/{lang}/{스토리명}.pdf`
5. 모든 에이전트 완료 후 결과를 사용자에게 보고한다

## 병렬 실행

- **언어별 병렬**: 같은 스토리의 각 언어는 독립적이므로 동시 실행
- **스토리별 병렬**: 여러 스토리를 요청한 경우에도 스토리별로 병렬 실행 가능
