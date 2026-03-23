# JobMate — Software Design Document

> 취준생 멘탈 케어 멀티에이전트 챗봇
> 최종 수정: 2026-03-23

---

## 1. 프로젝트 개요

### 1.1 목적
취업 준비생의 멘탈 관리를 위한 AI 멀티에이전트 그룹채팅 서비스. 4명의 AI 에이전트가 가상 오피스에서 근무하며, Slack 스타일 그룹채팅으로 사용자를 지원한다.

### 1.2 핵심 차별점
- **멀티에이전트 그룹채팅**: 단일 챗봇이 아닌 4명의 캐릭터가 자연스럽게 대화에 참여
- **2D 픽셀아트 오피스**: Gather Town 스타일 가상 오피스에서 에이전트 행동 시각화
- **Tool Calling 기반 실제 기능**: 채용공고 검색, 이력서 피드백 등 실용적 도구 연동

### 1.3 기술 스택

| 계층 | 기술 |
|------|------|
| LLM | Gemini Flash (google-generativeai) |
| 에이전트 오케스트레이션 | LangGraph |
| 백엔드 | Python 3.12+ / FastAPI |
| 실시간 통신 | WebSocket (FastAPI WebSocket) |
| DB | PostgreSQL 16 |
| 캐시/세션 | Redis 7 |
| 프론트엔드 | React 18 + TypeScript 5 |
| 픽셀아트 오피스 | Pixi.js 8 |
| 채팅 UI | 커스텀 Slack-style 컴포넌트 |
| 컨테이너 | Docker + docker-compose |
| CI/CD | GitHub Actions |
| 배포 | GCP Cloud Run 또는 AWS ECS |

---

## 2. 에이전트 설계

### 2.1 에이전트 프로필

#### 김서연 (Career Coach)
- **역할**: 이력서/자소서 피드백, 면접 준비
- **성격**: 따뜻하지만 직설적. "이 부분은 좋은데, 여기는 고치자"
- **담당 Tools**: `resume_feedback`, `mock_interview`
- **오피스 행동**: 노트북 타이핑, 서류 검토, 화이트보드 작성

#### 박준호 (Job Researcher)
- **역할**: 채용공고 검색, 시장 분석
- **성격**: 데이터 중심, 꼼꼼. "이 회사 최근 채용 트렌드를 보면..."
- **담당 Tools**: `search_jobs`, `analyze_market`
- **오피스 행동**: 모니터 여러 개 보기, 데이터 정리, 검색

#### 이하은 (Mental Care)
- **역할**: 감정 케어, 루틴 관리, 호흡 운동
- **성격**: 공감형, 차분. "지금 많이 힘들지? 잠깐 같이 쉬어보자"
- **담당 Tools**: `breathing_exercise`, `schedule_routine`
- **오피스 행동**: 차 마시기, 식물 돌보기, 명상

#### 정민수 (Industry Mentor)
- **역할**: 현실적 조언, 업계 인사이트
- **성격**: 형/누나 느낌, 유머. "나도 그때 그랬어 ㅋㅋ"
- **담당 Tools**: `get_motivation_content`, `industry_insight`
- **오피스 행동**: 폰 보기, 커피 마시기, 동료와 잡담

### 2.2 에이전트 참여 로직

```
사용자 메시지 → [Router Node]
  │
  ├─ 감정 분석 (모든 메시지)
  │   └─ 긴급 (패닉/극도 불안) → 이하은 즉시 개입
  │
  ├─ 의도 분류
  │   ├─ 이력서/면접 → 김서연 (primary) + 정민수 (보조 코멘트)
  │   ├─ 채용공고/시장 → 박준호 (primary) + 김서연 (보조)
  │   ├─ 멘탈/감정 → 이하은 (primary) + 정민수 (공감)
  │   ├─ 커리어 고민 → 정민수 (primary) + 김서연 (보조)
  │   └─ 일반 대화 → 1~2명 자연스럽게 참여
  │
  └─ 응답 순서 결정 (primary → 보조, 0.5~2초 딜레이)
```

### 2.3 그룹채팅 자연스러움 규칙
- 모든 에이전트가 매번 응답하지 않음 (1~3명)
- Primary 에이전트가 먼저, 보조는 딜레이 후 참여
- 에이전트끼리 서로 언급 가능 ("준호가 찾아준 공고 봤어?")
- 이모티콘/리액션으로만 참여하는 경우도 있음

---

## 3. Tool Calling 설계

### 3.1 Tool 목록

| Tool | 담당 에이전트 | 외부 API | 설명 |
|------|-------------|----------|------|
| `search_jobs` | 박준호 | 사람인 API + 공공데이터포털 | 조건 기반 채용공고 검색 |
| `resume_feedback` | 김서연 | LLM 내부 | 이력서/자소서 첨삭 피드백 |
| `mock_interview` | 김서연 | LLM 내부 | 모의 면접 질문 생성 + 답변 피드백 |
| `breathing_exercise` | 이하은 | 내부 로직 | 호흡/마인드풀니스 가이드 |
| `schedule_routine` | 이하은 | Google Calendar API | 취준 루틴 등록/리마인드 |
| `get_motivation_content` | 정민수 | YouTube Data API | 동기부여 콘텐츠 추천 |
| `analyze_market` | 박준호 | 내부 분석 | 직군별 채용 트렌드 분석 |
| `industry_insight` | 정민수 | LLM 내부 | 업계 현실 조언 |

### 3.2 Tool 스키마 예시

```python
# search_jobs
{
    "name": "search_jobs",
    "description": "사람인 API와 공공데이터포털에서 채용공고를 검색합니다",
    "parameters": {
        "type": "object",
        "properties": {
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "검색 키워드 (예: ['백엔드', 'Python'])"
            },
            "location": {
                "type": "string",
                "description": "근무 지역 (예: '서울', '경기')"
            },
            "career_level": {
                "type": "string",
                "enum": ["신입", "경력 1-3년", "경력 3-5년", "무관"],
                "description": "경력 수준"
            },
            "limit": {
                "type": "integer",
                "default": 5,
                "description": "결과 수"
            }
        },
        "required": ["keywords"]
    }
}
```

### 3.3 Tool → 오피스 행동 매핑

| Tool 호출 | 에이전트 오피스 행동 |
|-----------|-------------------|
| `search_jobs` 실행 중 | 박준호: 모니터 3개 빠르게 전환 |
| `resume_feedback` 실행 중 | 김서연: 서류 들고 빨간펜 체크 |
| `mock_interview` 실행 중 | 김서연: 화이트보드 앞에서 질문 작성 |
| `breathing_exercise` 실행 중 | 이하은: 요가매트 위 명상 포즈 |
| `schedule_routine` 실행 중 | 이하은: 캘린더/플래너 작성 |
| `get_motivation_content` 실행 중 | 정민수: 폰으로 영상 검색 |
| `analyze_market` 실행 중 | 박준호: 차트/그래프 분석 |
| `industry_insight` 실행 중 | 정민수: 턱 괴고 생각하는 포즈 |

---

## 4. 디렉토리 구조

```
jobmate/
├── SDD.md
├── docker-compose.yml
├── .github/
│   └── workflows/
│       ├── ci-backend.yml
│       └── ci-frontend.yml
│
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI 앱 엔트리포인트
│   │   ├── config.py                # 환경변수, 설정
│   │   ├── dependencies.py          # FastAPI 의존성 주입
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chat.py          # WebSocket 채팅 엔드포인트
│   │   │   │   ├── auth.py          # 인증 (JWT)
│   │   │   │   ├── users.py         # 사용자 프로필
│   │   │   │   └── rooms.py         # 채팅방 관리
│   │   │   └── middleware/
│   │   │       ├── __init__.py
│   │   │       └── auth.py          # JWT 미들웨어
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py             # LangGraph 메인 그래프
│   │   │   ├── router.py            # 의도 분류 + 에이전트 라우팅
│   │   │   ├── profiles.py          # 에이전트 프로필/프롬프트 정의
│   │   │   ├── nodes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── seo_yeon.py      # 김서연 에이전트 노드
│   │   │   │   ├── jun_ho.py        # 박준호 에이전트 노드
│   │   │   │   ├── ha_eun.py        # 이하은 에이전트 노드
│   │   │   │   └── min_su.py        # 정민수 에이전트 노드
│   │   │   └── state.py             # LangGraph 상태 정의
│   │   │
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── search_jobs.py       # 채용공고 검색
│   │   │   ├── resume_feedback.py   # 이력서 피드백
│   │   │   ├── mock_interview.py    # 모의 면접
│   │   │   ├── breathing.py         # 호흡 운동
│   │   │   ├── schedule.py          # 루틴 스케줄링
│   │   │   ├── motivation.py        # 동기부여 콘텐츠
│   │   │   ├── market.py            # 시장 분석
│   │   │   └── insight.py           # 업계 인사이트
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py              # User ORM 모델
│   │   │   ├── conversation.py      # Conversation ORM 모델
│   │   │   ├── message.py           # Message ORM 모델
│   │   │   └── agent_state.py       # AgentState ORM 모델
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── chat.py              # 채팅 Pydantic 스키마
│   │   │   ├── user.py              # 사용자 Pydantic 스키마
│   │   │   └── agent.py             # 에이전트 Pydantic 스키마
│   │   │
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── chat_service.py      # 채팅 비즈니스 로직
│   │       ├── session_service.py   # Redis 세션 관리
│   │       └── llm_service.py       # Gemini API 래퍼
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_agents/
│       │   ├── __init__.py
│       │   ├── test_router.py
│       │   └── test_graph.py
│       ├── test_tools/
│       │   ├── __init__.py
│       │   ├── test_search_jobs.py
│       │   └── test_resume_feedback.py
│       └── test_api/
│           ├── __init__.py
│           ├── test_chat.py
│           └── test_auth.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── public/
│   │   └── assets/
│   │       ├── agents/              # 에이전트 일러스트 프로필
│   │       │   ├── seo-yeon.png
│   │       │   ├── jun-ho.png
│   │       │   ├── ha-eun.png
│   │       │   └── min-su.png
│   │       └── office/              # 픽셀아트 오피스 스프라이트
│   │           ├── tileset.png
│   │           ├── furniture.png
│   │           └── characters/
│   │               ├── seo-yeon-sprite.png
│   │               ├── jun-ho-sprite.png
│   │               ├── ha-eun-sprite.png
│   │               └── min-su-sprite.png
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── vite-env.d.ts
│       │
│       ├── components/
│       │   ├── chat/
│       │   │   ├── ChatRoom.tsx       # 메인 채팅방
│       │   │   ├── MessageList.tsx     # 메시지 리스트
│       │   │   ├── MessageBubble.tsx   # 메시지 버블 (에이전트별 스타일)
│       │   │   ├── MessageInput.tsx    # 입력창
│       │   │   ├── TypingIndicator.tsx # 타이핑 인디케이터
│       │   │   └── ReactionBar.tsx     # 이모지 리액션
│       │   │
│       │   ├── office/
│       │   │   ├── OfficeView.tsx      # 픽셀아트 오피스 메인
│       │   │   ├── PixiStage.tsx       # Pixi.js 캔버스
│       │   │   ├── AgentSprite.tsx     # 에이전트 스프라이트
│       │   │   ├── FurnitureLayer.tsx  # 가구 레이어
│       │   │   └── StatusBubble.tsx    # 행동 상태 말풍선
│       │   │
│       │   ├── sidebar/
│       │   │   ├── Sidebar.tsx         # 사이드바 (채널 목록)
│       │   │   ├── AgentProfile.tsx    # 에이전트 프로필 카드
│       │   │   └── ChannelList.tsx     # 채널 리스트
│       │   │
│       │   └── common/
│       │       ├── Avatar.tsx          # 아바타 컴포넌트
│       │       ├── Layout.tsx          # 전체 레이아웃
│       │       └── ToolStatus.tsx      # Tool 실행 상태 표시
│       │
│       ├── hooks/
│       │   ├── useWebSocket.ts        # WebSocket 연결 훅
│       │   ├── useChat.ts             # 채팅 상태 관리
│       │   └── useOffice.ts           # 오피스 상태 관리
│       │
│       ├── stores/
│       │   ├── chatStore.ts           # 채팅 상태 (Zustand)
│       │   ├── officeStore.ts         # 오피스 상태 (Zustand)
│       │   └── authStore.ts           # 인증 상태
│       │
│       ├── types/
│       │   ├── chat.ts                # 채팅 타입 정의
│       │   ├── agent.ts               # 에이전트 타입 정의
│       │   └── office.ts              # 오피스 타입 정의
│       │
│       └── utils/
│           ├── api.ts                 # API 클라이언트
│           └── constants.ts           # 상수 정의
│
└── infra/
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    └── nginx.conf
```

---

## 5. DB 스키마

### 5.1 ERD

```
users ||--o{ conversations : creates
conversations ||--o{ messages : contains
messages }o--|| agents : sent_by (nullable)
users ||--o{ user_emotion_logs : has
```

### 5.2 테이블 정의

#### users
```sql
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname      VARCHAR(50) NOT NULL,
    avatar_url    VARCHAR(500),
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);
```

#### agents
```sql
CREATE TABLE agents (
    id            VARCHAR(20) PRIMARY KEY,  -- 'seo_yeon', 'jun_ho', etc.
    name          VARCHAR(50) NOT NULL,      -- '김서연'
    role          VARCHAR(100) NOT NULL,     -- 'Career Coach'
    personality   TEXT NOT NULL,             -- 프롬프트용 성격 설명
    avatar_url    VARCHAR(500) NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
```

#### conversations
```sql
CREATE TABLE conversations (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL REFERENCES users(id),
    title         VARCHAR(200),
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
```

#### messages
```sql
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    sender_type     VARCHAR(10) NOT NULL CHECK (sender_type IN ('user', 'agent')),
    agent_id        VARCHAR(20) REFERENCES agents(id),  -- NULL if sender_type='user'
    content         TEXT NOT NULL,
    tool_calls      JSONB,           -- Tool 호출 정보 (있을 경우)
    tool_results    JSONB,           -- Tool 결과 (있을 경우)
    emotion_tag     VARCHAR(20),     -- 감정 태그 (분석 결과)
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

#### user_emotion_logs
```sql
CREATE TABLE user_emotion_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    conversation_id UUID REFERENCES conversations(id),
    emotion         VARCHAR(20) NOT NULL,  -- 'anxious', 'depressed', 'angry', 'hopeful', 'neutral'
    intensity       SMALLINT NOT NULL CHECK (intensity BETWEEN 1 AND 5),
    context         TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_emotion_logs_user_id ON user_emotion_logs(user_id);
CREATE INDEX idx_emotion_logs_created_at ON user_emotion_logs(created_at);
```

---

## 6. API 스펙

### 6.1 REST Endpoints

#### Auth
| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/auth/register` | 회원가입 |
| POST | `/api/auth/login` | 로그인 → JWT 발급 |
| POST | `/api/auth/refresh` | 토큰 갱신 |

#### Users
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/users/me` | 내 프로필 조회 |
| PATCH | `/api/users/me` | 프로필 수정 |

#### Conversations
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/conversations` | 대화 목록 |
| POST | `/api/conversations` | 새 대화 생성 |
| GET | `/api/conversations/{id}` | 대화 상세 (메시지 포함) |
| DELETE | `/api/conversations/{id}` | 대화 삭제 |

#### Agents
| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/agents` | 에이전트 목록 + 현재 상태 |
| GET | `/api/agents/{id}` | 에이전트 프로필 상세 |

### 6.2 WebSocket

#### 연결
```
ws://localhost:8000/ws/chat/{conversation_id}?token={jwt_token}
```

#### Client → Server 메시지
```json
{
    "type": "user_message",
    "content": "오늘 면접 망한 것 같아...",
    "timestamp": "2026-03-23T14:30:00Z"
}
```

#### Server → Client 메시지

**에이전트 타이핑 시작**
```json
{
    "type": "agent_typing",
    "agent_id": "ha_eun",
    "office_action": "thinking"
}
```

**에이전트 메시지 (스트리밍)**
```json
{
    "type": "agent_message_chunk",
    "agent_id": "ha_eun",
    "chunk": "일단 심호흡부터",
    "is_final": false
}
```

**Tool 호출 시작**
```json
{
    "type": "tool_call_start",
    "agent_id": "jun_ho",
    "tool_name": "search_jobs",
    "office_action": "searching_monitors"
}
```

**Tool 호출 결과**
```json
{
    "type": "tool_call_result",
    "agent_id": "jun_ho",
    "tool_name": "search_jobs",
    "result_summary": "3건의 채용공고를 찾았습니다",
    "office_action": "idle"
}
```

**에이전트 리액션**
```json
{
    "type": "agent_reaction",
    "agent_id": "min_su",
    "emoji": "💪"
}
```

**오피스 상태 업데이트**
```json
{
    "type": "office_state",
    "agents": {
        "seo_yeon": {"action": "typing", "position": {"x": 3, "y": 2}},
        "jun_ho": {"action": "searching_monitors", "position": {"x": 7, "y": 2}},
        "ha_eun": {"action": "making_tea", "position": {"x": 5, "y": 5}},
        "min_su": {"action": "idle", "position": {"x": 9, "y": 4}}
    }
}
```

---

## 7. LangGraph 에이전트 플로우

### 7.1 그래프 구조

```
                    ┌──────────────┐
                    │  START       │
                    │  (user_msg)  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  analyze     │  감정 분석 + 의도 분류
                    │  _emotion    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  route       │  참여 에이전트 결정
                    │  _agents     │  (primary + 보조)
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌────▼─────┐ ┌────▼─────┐
        │ agent_1  │ │ agent_2  │ │ agent_3  │  병렬 실행
        │ (primary)│ │ (assist) │ │ (react)  │  (필요시)
        └─────┬────┘ └────┬─────┘ └────┬─────┘
              │            │            │
              │     ┌──────▼───────┐    │
              │     │  tool_calls  │    │   Tool 호출 (필요시)
              │     └──────┬───────┘    │
              │            │            │
        ┌─────▼────────────▼────────────▼─────┐
        │          compose_responses          │  응답 순서 정렬
        │          + delay scheduling         │  + 딜레이 설정
        └─────────────────┬───────────────────┘
                          │
                   ┌──────▼───────┐
                   │  stream      │  WebSocket으로 순차 전송
                   │  _to_client  │
                   └──────┬───────┘
                          │
                   ┌──────▼───────┐
                   │  save_state  │  DB 저장 + 감정 로그
                   └──────┬───────┘
                          │
                       [END]
```

### 7.2 State 정의

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph import add_messages

class AgentResponse(TypedDict):
    agent_id: str
    content: str
    tool_calls: list[dict] | None
    delay_ms: int  # 이전 응답 대비 딜레이
    response_type: Literal["message", "reaction"]

class JobMateState(TypedDict):
    messages: Annotated[list, add_messages]
    user_message: str
    emotion: str
    emotion_intensity: int
    intent: str
    active_agents: list[str]          # 참여할 에이전트 ID 목록
    agent_responses: list[AgentResponse]
    conversation_id: str
    user_id: str
```

---

## 8. 픽셀아트 오피스 설계

### 8.1 오피스 레이아웃 (타일맵 12x8)

```
[벽][벽][벽][벽][벽][창][벽][창][벽][벽][벽][벽]
[벽][서연책상    ][  ][  ][준호책상    ][  ][벽]
[벽][  ][서연의자][  ][  ][준호의자][  ][  ][벽]
[벽][  ][  ][화이트보드  ][  ][  ][  ][  ][벽]
[벽][  ][  ][  ][소파][소파][  ][  ][  ][벽]
[벽][하은책상    ][  ][식물][  ][민수책상  ][벽]
[벽][  ][하은의자][  ][  ][  ][민수의자][  ][벽]
[벽][벽][벽][문][문][벽][벽][벽][벽][벽][벽][벽]
```

### 8.2 에이전트 스프라이트 상태

각 에이전트는 다음 상태별 스프라이트 프레임을 가짐:

| 상태 | 프레임 수 | 설명 |
|------|----------|------|
| `idle` | 4 | 가만히 앉아 있음 (미세 움직임) |
| `typing` | 4 | 키보드 타이핑 |
| `thinking` | 4 | 턱 괴고 생각 |
| `searching` | 6 | 모니터 빠르게 전환 |
| `reading` | 4 | 서류 읽기 |
| `walking` | 8 | 이동 (4방향 × 2프레임) |
| `drinking` | 4 | 음료 마시기 |
| `meditating` | 4 | 명상 포즈 |
| `talking` | 4 | 대화 (말풍선 표시) |

### 8.3 상태 전이

```
Tool 미호출 시: idle → thinking → talking → idle
Tool 호출 시:  idle → [tool별 행동] → talking → idle
대기 시:       idle → (랜덤) drinking / walking / idle
```

---

## 9. 인증/세션 설계

### 9.1 JWT 플로우
```
로그인 → Access Token (15분) + Refresh Token (7일)
WebSocket 연결 시 → query param으로 Access Token 전달
Redis에 세션 저장 → { user_id, active_conversation_id, connected_at }
```

### 9.2 Redis 키 구조
```
session:{user_id}          → 세션 정보 (TTL: 24h)
typing:{conversation_id}   → 현재 타이핑 중인 에이전트 (TTL: 10s)
office:{conversation_id}   → 오피스 에이전트 상태 (TTL: 30s)
```

---

## 10. 개발 로드맵

### Phase 1: 기반 구축 (Week 1-2)
- [ ] 프로젝트 스캐폴딩 + Docker 환경
- [ ] DB 스키마 + Alembic 마이그레이션
- [ ] FastAPI 기본 구조 + JWT 인증
- [ ] Gemini Flash 연동 + 기본 채팅 (단일 에이전트)

### Phase 2: 멀티에이전트 (Week 3-4)
- [ ] LangGraph 그래프 구현 (라우터 + 4개 에이전트 노드)
- [ ] Tool Calling 구현 (8개 Tool)
- [ ] 에이전트 프롬프트 엔지니어링 + 성격 튜닝
- [ ] WebSocket 스트리밍

### Phase 3: 프론트엔드 (Week 5-6)
- [ ] Slack 스타일 채팅 UI
- [ ] Pixi.js 픽셀아트 오피스
- [ ] 에이전트 스프라이트 제작 + 애니메이션
- [ ] Tool 실행 ↔ 오피스 행동 연동

### Phase 4: 완성 (Week 7-8)
- [ ] 감정 분석 고도화 + 대화 흐름 개선
- [ ] 에이전트 간 자연스러운 상호작용
- [ ] Docker 배포 + CI/CD
- [ ] 성능 최적화 + 에러 핸들링
