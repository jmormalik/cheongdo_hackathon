# 배포 및 실제 SDK 검증 준비

이 문서는 **이번 주 농사** P0의 실제 Copilot SDK 호출과 Azure Container Apps 배포를 시작하기 전에 팀이 준비할 항목을 정리한다. 제품 요구사항은 [PRD.md](PRD.md), 기술 요구사항은 [TRD.md](TRD.md), 구현 경계는 [TDD.md](TDD.md), 역할 분담은 [CONTRIBUTING.md](CONTRIBUTING.md)를 따른다.

## 절대 공유하지 않을 정보

다음 값은 채팅, 이슈, PR, 커밋, `.env`, 로그, 브라우저 코드에 넣지 않는다.

- GitHub Copilot 인증 토큰
- Azure 접근 토큰·클라이언트 비밀·연결 문자열
- 실제 사용자 질문 원문과 식별 가능한 입력

비밀 값은 Azure Container Apps Secret에만 저장한다. 팀에는 값이 아니라 **등록 완료 여부**만 공유한다.

## 1. GitHub Copilot 서버 인증

### 필요한 것

- GitHub Copilot 사용 권한이 있는 GitHub 계정 또는 조직 인증 방식
- 서버 환경용 Copilot 인증 토큰

### 준비 방법

1. 사용할 GitHub 계정 또는 조직에 Copilot 사용 권한과 Copilot CLI 사용 정책이 허용되어 있는지 확인한다.
2. [GitHub Copilot SDK 인증 문서](https://github.com/github/copilot-sdk/blob/main/docs/auth/authenticate.md)에 따라 서버에서 사용할 인증 방식을 선택한다.
3. 해커톤 P0에서는 SDK가 우선 확인하는 `COPILOT_GITHUB_TOKEN`을 Azure Container Apps Secret으로 저장한다.
4. Container App의 런타임 환경 변수 `COPILOT_GITHUB_TOKEN`이 해당 Secret을 참조하도록 설정한다.

GitHub Copilot 인증은 Azure Managed Identity로 대체할 수 없다. Managed Identity는 Azure 리소스 접근에 사용하며, Copilot SDK는 GitHub 인증이 필요하다.

### 완료 기준

- 토큰 값은 노출하지 않은 채 Azure Secret 등록을 완료했다.
- 컨테이너 런타임에서만 `COPILOT_GITHUB_TOKEN`을 읽을 수 있다.
- 브라우저 응답, 로그, 저장소에서 토큰이 발견되지 않는다.

## 2. Azure 구독과 권한

### 필요한 것

- 사용할 Azure 구독
- 배포할 리소스 그룹
- 배포 가능한 Azure 지역
- 리소스 그룹에 대한 배포자의 `Contributor` 권한

### 준비 방법

1. Azure Portal에서 사용할 구독을 선택한다. 학생 구독은 Container Apps 지역·할당량을 먼저 확인한다.
2. 팀 전용 리소스 그룹을 만들거나 기존 리소스 그룹을 사용한다.
3. 배포 담당 계정에 해당 리소스 그룹의 `Contributor` 역할을 부여한다.
4. Azure CLI로 구독을 선택하고 확인한다.

```bash
az login
az account list --output table
az account set --subscription "<구독 ID 또는 이름>"
az account show --output table
```

Aspire 또는 Container Apps 배포 중 리소스 공급자 등록 권한 오류가 발생하면 구독 관리자에게 필요한 공급자 등록을 요청한다. 예상 공급자는 `Microsoft.App`, `Microsoft.ContainerRegistry`, `Microsoft.OperationalInsights`다.

### 완료 기준

- 배포자가 지정 구독과 리소스 그룹을 조회할 수 있다.
- 배포 지역이 결정됐다.
- 필요한 공급자·할당량 오류가 없는지 확인했다.

## 3. 로컬 배포 도구

J 역할의 현재 구현은 Python 3.11 이상, .NET 9 AppHost, Docker, Azure CLI, Aspire를 사용한다.

| 도구 | 용도 | 확인 명령 |
| --- | --- | --- |
| Python 3.11+ | FastAPI·Copilot SDK 실행 | `python3 --version` |
| Docker | 단일 컨테이너 이미지 빌드 | `docker --version` |
| Azure CLI | 구독 선택·Azure 로그인·배포 확인 | `az --version` |
| .NET 9 SDK | `AppHost/` 빌드·실행 | `dotnet --info` |
| Aspire CLI | AppHost 실행·배포 | `aspire --version` |

프로젝트는 다음 Python 패키지 버전을 고정했다.

- `agent-framework-github-copilot==2.1.1`
- `github-copilot-sdk==1.0.28`
- `fastapi==0.115.12`
- `uvicorn==0.34.0`

패키지 설치와 컨테이너 빌드는 J 역할에서 검증했지만, 실제 Copilot 인증·Aspire 배포는 아직 검증되지 않았다.

## 4. 팀 인계 조건

| 담당 | 다음 통합에 필요한 산출물 | 상태 |
| --- | --- | --- |
| J | FastAPI·SSE·Agent 게이트웨이·Dockerfile·AppHost | `feature/runtime-agent`에 구현됨 |
| T | `app/guidance.py`, `app/data/guidance.json`, 고정 시나리오와 근거 검증 | 필요 |
| S | `app/static/` UI, 카드·근거 보기·SSE 상태 처리 | 필요 |

T 자료가 연결되면 J는 `GuidanceService` 인터페이스로 실제 카드를 반환하고, `GetCropGuidance`가 실제 도구 호출로 자료를 가져오는 E2E를 검증한다. S UI가 연결되면 공개 동선과 SSE 상태를 함께 검증한다.

## 5. 준비 완료 공유 형식

비밀 값 없이 다음 항목만 공유한다.

```text
Azure Secret 등록: 완료 / 미완료
구독 ID: <식별자>
리소스 그룹: <이름>
배포 지역: <지역>
az 로그인: 완료 / 미완료
Aspire 설치: 완료 / 미완료
T 자료 구현: 완료 / 진행 중
S UI 구현: 완료 / 진행 중
```

## 6. 실제 검증 순서

1. `GET /healthz`가 Container Apps 공개 URL에서 응답하는지 확인한다.
2. T의 정적 자료로 `GET /api/guidance`가 카드·근거를 반환하는지 확인한다.
3. Azure Secret을 주입한 상태에서 질문 요청이 실제 `GitHubCopilotAgent`와 `GetCropGuidance` 호출로 이어지는지 확인한다.
4. 서버가 모델 답변의 근거 ID를 자료 결과와 대조한 뒤에만 SSE `result`를 보내는지 확인한다.
5. 시간 초과·취소·AI 오류에서 질문 원문과 비밀이 로그에 없고, 카드가 유지되는지 확인한다.

실제 SDK 또는 Azure 배포를 검증하기 전에는 성공했다고 주장하지 않는다.
