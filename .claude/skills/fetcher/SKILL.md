# Gutenberg Fetcher Skill

Project Gutenberg에서 공개 도메인 텍스트를 다운로드하여 `gutenberg-raw/`에 저장하는 스킬.

## 동작 규칙

### 1. 체크리스트 확인
- `tail-candidates/checklist.md`에서 `[ ]` (미완료) 항목을 찾는다
- 각 항목에서 Gutenberg ID를 추출한다 (`` `G #숫자` `` 패턴)
- `△G #` 표시는 해당 ID에 원하는 이야기가 포함되어 있지 않을 수 있다는 뜻이므로, 다운로드 후 내용 확인 필요
- 한국 전래 (72-86)처럼 Gutenberg ID가 없는 항목은 스킵한다

### 2. 다운로드
- URL을 순서대로 시도하여 **plain text** 응답을 받을 때까지 fallback한다:
  1. `https://www.gutenberg.org/cache/epub/{ID}/pg{ID}.txt`
  2. `https://www.gutenberg.org/files/{ID}/{ID}-0.txt`
  3. `https://www.gutenberg.org/files/{ID}/{ID}.txt`
- 동일 Gutenberg ID가 여러 항목에 걸쳐 있으면 **한 번만 다운로드**

### 3. 출력 규칙
- 파일명 형식: `{번호}_{제목}.txt`
  - 번호: **Gutenberg ID**
  - 제목: 책 제목의 소문자, 공백은 `_`로 치환, 특수문자 제거
- 예시: `2591_grimms_fairy_tales.txt`, `500_the_adventures_of_pinocchio.txt`
- 저장 위치: `gutenberg-raw/`

### 4. 검증
- 다운로드 후 파일 크기가 0보다 큰지 확인
- 파일 첫 줄이 `<!DOCTYPE` 또는 `<html`로 시작하면 HTML(404 에러 페이지)이므로 **실패로 간주**
- 정상 파일은 `The Project Gutenberg eBook` 등 plain text로 시작해야 함
- 검증 실패 시 해당 파일 삭제하고 다음 fallback URL 시도

### 5. 체크리스트 업데이트
- 다운로드 성공 시 해당 Gutenberg ID를 공유하는 **모든 항목**의 `[ ]`를 `[x]`로 변경
- 다운로드 실패 시 체크하지 않음

### 6. 병렬 처리
- 고유 Gutenberg ID 기준으로 병렬 다운로드 가능
- 단, Gutenberg 서버 부하를 고려하여 동시 요청은 최대 5개로 제한