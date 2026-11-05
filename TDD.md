# 이번 주 농사 — MVP 구현 설계

버전: 0.3 / 2026-11-05 / 기준: PRD v0.4, TRD v0.4
상태: 구현 예정 설계. 아래 경로·계약은 아직 구현된 기능이 아니다.

## 1. 파일 구성
```text
AppHost/                 # 단일 앱 등록, Container Apps 배포 대상
app/main.py              # FastAPI, 정적 UI, API, healthz
app/agent.py             # 공식 SDK 통합, 요청별 세션, 도구 권한
app/guidance.py          # JSON 조회, 근거 ID 검증
app/data/guidance.json   # 시나리오 1개, 카드 최대 3개
app/static/              # 프론트 빌드 결과 또는 HTML/CSS/JS
Dockerfile               # UI와 Python 서버, 필요한 Copilot 런타임
```
Python 서버는 0.0.0.0:8000에서 수신한다. AppHost는 Dockerfile 앱의 target port 8000을 등록하고 외부 HTTP 엔드포인트를 공개한다. 실제 배포 URL은 HTTPS로 검증한다. 브라우저는 동일 출처 `/api/*`만 사용한다. CORS·공개 백엔드 별도 주소가 필요 없는 구성이다.

## 2. 데이터 계약
고정 scenarioId는 `cheongdo-persimmon-postharvest`다.

- Guidance: scenarioId, dataKind(`reviewed_static` 또는 `fixture`), reviewedAt, sources[], cards[].
- Source: id, title, url(예시는 null), publishedAt(미상이면 null), scope.
- Card: id, title, reason, caution, evidenceIds[].
- Answer: text, evidenceIds[]. 모델이 URL이나 날짜 필드를 생성하지 않는다.

실제 자료의 모든 카드에는 유효한 source ID가 있어야 한다. fixture에는 별도 예시 ID를 부여하고 원문 링크를 만들지 않는다. AI도 자료 상태를 그대로 설명한다. `reviewed_static`은 사람이 원문을 대조했다는 뜻이며 전문가가 정확성을 보증한다는 뜻이 아니다.

## 3. HTTP 계약
| 경로 | 요청 | 결과 |
| --- | --- | --- |
| GET /, /demo | 없음 | 동일한 공개 데모 화면 |
| GET /healthz | 없음 | 200 상태 확인. 모델의 가용성을 보증하지 않음 |
| GET /api/guidance | 없음 | 고정 시나리오·현재 주간 범위·자료·카드 JSON |
| POST /api/questions | {scenarioId, cardId?, question} | 검증·용량 검사 후 SSE |

클라이언트가 보낸 카드 내용이나 출처는 신뢰하지 않는다. 질문 처리 시 서버가 같은 시나리오 자료를 다시 읽는다. 입력 오류 400/422, 요청 크기 초과 413, 처리 용량 초과 429는 SSE 연결 전에 JSON 오류로 반환한다.

## 4. 질문과 SSE
브라우저는 POST fetch의 응답 스트림을 읽는다. EventSource는 POST 본문 전송에 사용하지 않는다. SSE 프레임은 빈 줄로 구분하며 네트워크 청크 경계와 이벤트 경계가 다를 수 있으므로 버퍼로 파싱한다.

1. 서버 검증·동시 처리 슬롯 확보 후 requestId를 만든다.
2. 에이전트를 요청별로 생성하고 고정 시나리오, 검증된 선택 cardId(있으면), 서버 계산 주간 범위, 자료 상태, 질문을 전달한다.
3. GetCropGuidance 실제 실행 시에만 tool_running/tool_done 상태를 보낸다. 호출을 유도하는 지침을 두고 실행 추적으로 확인한다.
4. 서버는 완성된 답변의 형식과 근거 ID를 검증한다. 지원 범위 안의 농업 답변에서 도구가 호출되지 않았거나 ID가 없거나 미등록이면 answer_validation_failed로 처리한다. 범위 밖 질문은 범위 안내만 표시하며 농업 답변 성공으로 집계하지 않는다.
5. 검증된 답변을 result로 한 번 보내고 complete로 종료한다.
6. 실패는 error 후 complete로 종료한다. 연결 단절·45초 초과 시 에이전트 세션·작업을 취소/정리하고 처리 슬롯을 반환한다.

이벤트 계약: 모든 이벤트에 requestId와 증가하는 seq를 넣는다. status에는 단계 이름, result에는 Answer와 서버가 매핑한 sources/dataKind, error에는 code/message/retryable, complete에는 outcome(success/error)을 넣는다. 검증 전 모델 텍스트·내부 추론·비밀은 전송하지 않는다. 완료 이전 연결 단절은 UI에서 실패로 표시한다. SSE 진행 상태 구현을 모델 토큰 스트리밍으로 표현하지 않는다.

## 5. 화면과 장애
첫 화면에 서비스 설명, 고정 조건, 점검 목록 버튼을 둔다. 결과에 카드 최대 3개, 근거 펼치기, 추천 질문 3개와 질문 입력을 둔다. fixture 배너는 카드와 답변 모두에 적용한다.

- 로딩: 질문 버튼 비활성화, 실제 실행 상태 문구와 취소 버튼 표시. AbortController로 요청을 중단하고 카드·질문 입력은 보존한다.
- AI 오류/시간 초과: 카드 유지, 오류 문구와 수동 재시도.
- 자료 없음: 빈 상태 표시, AI 요청 비활성화.
- 검증 실패: 생성 답변을 숨기고 근거를 확인할 수 없다는 안내.
- 시스템 설정 오류: 일반 사용자에게 승인·토큰 입력을 요구하지 않고 운영 로그로 구분.

## 6. 팀 작업 순서
- 배포 담당: 단일 Dockerfile, AppHost, Azure 공개 URL, 비밀 전달과 healthz.
- AI/서버 담당: SDK 최소 실행과 도구 권한 검증을 먼저 끝내고 API 계약 구현.
- UI/자료 담당: 고정 시나리오 화면, 카드 자료와 출처 검토, 오류 UI.
실제 담당자 배정은 팀이 정한다. UI는 명시적인 개발용 fixture로 병행할 수 있지만 출시 AI 완료 조건은 실제 서버 연결이다.

## 7. 최소 검증 목록
- 공개 URL 새 세션에서 카드 → 근거 → 질문 → 답변 완료.
- fixture 표시 또는 실제 원문·검토일 표시 확인.
- 질문 길이·미지원 scenario 거부, 미등록 근거 ID 차단.
- 모델 실패·시간 초과·SSE 중단에서 잘못된 성공 없음, 슬롯·세션 정리.
- 도구 실제 호출과 허용 외 기능 거부를 비식별 로그로 확인.
- 모바일 390px 동선, 서버 비밀 비노출, 재배포 및 직전 리비전 복구 절차 확인.

SDK 호출 시그니처·정확한 패키지 버전·인증 설정은 구현 단계에서 설치 버전과 공식 문서를 확인해 고정한다. 이 문서에는 미검증 SDK 코드를 실행 가능 예제로 넣지 않는다.

## 8. UI 및 검증 보완
카드의 ‘이유 질문’은 해당 cardId와 추천 문구를 질문 요청에 넣는다. 자유 질문의 cardId는 생략 가능하다. 서버는 cardId 유효성을 검사한 뒤 서버 자료로 맥락을 재구성한다. 데이터 계약 Answer에 kind(`grounded` 또는 `out_of_scope`)를 추가한다. grounded만 유효한 evidenceIds를 필수로 요구하고, out_of_scope는 농업 조언 없이 지원 범위 안내만 허용한다. 자유 텍스트의 안전성 전체를 스키마 검사만으로 보장할 수 없으므로 대표 범위 밖 질문을 실행 검증한다.

답변에는 ‘AI 생성 설명’ 표식을 둔다. 로딩/오류 영역은 aria-live로 알리고, 입력 label·키보드 포커스·Tab/Enter 동선을 확인한다. 모바일에서 가로 스크롤 없이 카드·질문·근거 링크에 접근해야 한다.

실제 에이전트 이벤트 → 서버 상태 이벤트 → 브라우저 표시를 요청 ID로 연결해 검증한다. 사용자 취소·네트워크 단절·45초 제한 각각에서 자원 해제를 확인한다. 생산성 평가는 PRD의 같은 과업으로 수행하고, 기술 오류 때문에 과업을 못 마친 경우 성공 시간 통계에서 숨기지 않고 실패로 기록한다.
