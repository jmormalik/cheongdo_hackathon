# S 담당 UI 실행과 인계

빌드·외부 패키지 없이 `app/static/`의 HTML/CSS/ES modules를 사용한다. 서버 담당자는 `/`와 `/demo`에서 `app/static/index.html`을 반환하고 `/static/`에 해당 디렉터리를 마운트한다. 브라우저는 같은 출처의 실제 `/api/guidance`, `/api/questions`만 요청한다. 운영 UI에는 mock 모드나 자동 대체 응답이 없다.

## 로컬 mock 시연

```bash
node tests/ui/mock-server.mjs
```

`http://127.0.0.1:4173/demo`에 접속한다. 이 서버는 개발 전용이며 모든 답변은 mock이다. `/`도 같은 화면을 제공한다. `/demo?case=error`, `timeout`, `validation-error`, `disconnect`, `busy`, `slow`, `empty`, `guidance-error`, `reviewed`, `out-of-scope`로 장애·빈 자료·자료 메타데이터 UI를 확인한다. `reviewed`의 example.com 주소 역시 UI 검사용이며 실제 검토 자료가 아니다. `UI_PORT`로 포트를 바꿀 수 있다.

## 검증

```bash
node --test tests/ui/protocol.test.mjs tests/ui/browser.test.mjs
git diff --check
```

Node 22 이상을 사용한다. 브라우저 검사는 설치된 Chrome을 사용하며 npm 패키지나 브라우저를 설치하지 않는다. macOS 기본 Chrome 경로 외에는 `CHROME_BIN`에 실행 파일 경로를 지정한다. Chrome이 없으면 브라우저 검사는 skip으로 보고된다. 검사는 390px/1440px 가로 넘침, Tab/Enter, 카드 맥락, fixture/AI 표시, 발행일 미상과 검토일, 오류·취소·수동 재시도·범위 안내, HTML 안전 렌더링을 확인한다. 실제 스크린리더 낭독과 공개 Azure E2E는 별도 확인이 필요하다.

## API 연결 기준

TDD v0.3의 필드명을 사용한다. `GET /api/guidance`는 `{scenarioId,dataKind,reviewedAt,sources,cards}`를 반환한다. 출처는 `{id,title,url,publishedAt,scope}`, 카드는 `{id,title,reason,caution,evidenceIds}`다. 선택 필드 `source.usageTerms`, `source.reviewedAt`이 있으면 함께 표시한다. 주간 범위는 자료 발행일과 분리해 Asia/Seoul 월~일로 표시한다.

`POST /api/questions` 본문은 `{scenarioId,question,cardId?}`다. 카드 버튼은 질문과 맥락을 입력창에 채우며, 사용자가 질문 보내기로 제출한다. 추천 질문도 입력창에 채운다. 텍스트 영역에서는 줄바꿈을 허용하고 Ctrl/Cmd+Enter 또는 질문 보내기 버튼의 Enter로 제출한다. 질문·답변을 localStorage, 쿠키, 로그에 저장하지 않는다.

SSE는 `event:`와 JSON `data:`를 사용한다. 모든 이벤트에 `requestId`, 증가하는 정수 `seq`가 필요하다.

- `status`: `{requestId,seq,stage}`. 표시 단계는 `accepted`, `queued`, `tool_running`, `tool_done`, `generating`, `validating`이며 모르는 단계는 일반 진행 문구로 표시한다. 모델 원문은 표시하지 않는다.
- `result`: `{requestId,seq,answer:{kind,text,evidenceIds},sources,dataKind,reviewedAt?}`. `kind`는 `grounded` 또는 `out_of_scope`다. 검증된 최종 답변 1개만 받는다.
- `error`: `{requestId,seq,code,message,retryable}`. 알려진 오류 코드는 사용자 안내로 매핑하며 원시 서버 메시지를 그대로 출력하지 않는다.
- `complete`: `{requestId,seq,outcome:"success"|"error"}`. 성공 결과와 성공 완료가 모두 있어야 답변을 표시한다. 서버는 완료 후 스트림을 닫는다.

서버 전체 제한 45초에 더해 브라우저는 무응답 연결을 50초에 중단한다. 취소 시 AbortController로 연결을 닫는다. 서버 쪽 세션·슬롯 해제는 J의 구현과 실제 통합으로 확인해야 한다. HTTP 400/413/422는 입력 안내, 429는 용량 안내로 처리한다. 자동 재접속·자동 재시도는 없다.

공유 계약 파일과 실제 백엔드는 현재 브랜치에 없어 실제 API·SDK·Azure 연결은 미검증이다. 위 필드명은 TDD의 구체화이므로 J의 공유 계약 확정 시 대조해야 한다. 생산성 관찰(수동/앱 수행 시간, 실패)은 미측정이며 효과를 주장하지 않는다. PRD/TRD 갱신은 해당 담당자와 실제 측정 후 진행한다.
