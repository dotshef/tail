---
name: book-editor
description: tail-story와 tail-localized을 조합하여 tail-bookform/{lang}에 최종 책 형식을 생성하는 진입점
---

# Book Editor Skill (진입점)

이 스킬은 book-editor 에이전트를 spawn하는 진입점이다.

## 사용법

예시 트리거:
- "여우와 두루미 bookform 만들어줘"
- "/book-editor 여우와 두루미"
- "/book-editor all" (전체 생성)

## 규약 (Convention)

### 입력

- 스토리 본문: `tail-story/{스토리명}.md`
- 로컬라이즈 데이터: `tail-localized/{lang}/{스토리명}.md`
- 이미지: `tail-image/{스토리명}/cuts/컷{N}.jpeg`

### 출력

- `tail-bookform/{lang}/{스토리명}.md` (localized에 존재하는 언어별로 생성)

## 동작

1. 사용자의 요청에서 대상 스토리명을 파악한다
2. `tail-story/{스토리명}.md`가 존재하는지 확인한다 (없으면 에러 보고)
3. `tail-localized/` 하위 폴더를 탐색하여 해당 스토리의 언어별 localized 존재 여부를 확인한다
   - 존재하는 언어만 처리한다
   - 어떤 언어에도 없으면 에러 보고
4. `tail-bookform/{lang}/` 폴더가 없으면 생성한다
5. **존재하는 언어별로 book-editor 에이전트를 병렬 spawn한다**
   - 각 에이전트에 스토리명과 대상 언어를 전달한다
   - 동작: story 본문 + localized의 `<sub>`, expressions + 이미지 참조를 조합
   - 출력: `tail-bookform/{lang}/{스토리명}.md`
6. 모든 에이전트 완료 후 결과를 사용자에게 보고한다

## 병렬 실행

- **언어별 병렬**: 같은 스토리의 각 언어는 독립적이므로 동시 실행
- **스토리별 병렬**: 여러 스토리를 요청한 경우에도 스토리별로 병렬 실행 가능
