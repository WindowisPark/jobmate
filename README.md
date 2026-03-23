# JobMate — 취준생 멘탈 케어 멀티에이전트 챗봇

> 4명의 AI 에이전트가 가상 오피스에서 함께 일하며, 취업 준비생의 멘탈과 커리어를 케어하는 그룹채팅 서비스

## Overview

취업 준비는 외롭고 힘든 과정입니다. JobMate는 단순한 챗봇이 아닌, **4명의 전문가 팀**이 Slack 스타일 그룹채팅에서 함께 응답하는 멀티에이전트 서비스입니다. 사용자의 감정을 분석하고, 상황에 맞는 에이전트가 자연스럽게 대화에 참여합니다.

### 에이전트 팀

| 에이전트 | 역할 | 성격 | 담당 Tool |
|---------|------|------|----------|
| **김서연** 📝 | 커리어 코치 | 따뜻하지만 직설적 | 이력서 피드백, 모의 면접 |
| **박준호** 🔍 | 취업 리서처 | 데이터 중심, 꼼꼼 | 채용공고 검색, 시장 분석 |
| **이하은** 🌿 | 멘탈 케어 | 공감형, 차분 | 호흡 운동, 루틴 관리 |
| **정민수** 💡 | 현직자 멘토 | 유머 + 현실 조언 | 동기부여 콘텐츠, 업계 인사이트 |

## Key Features

### LLM Tool Calling
- OpenAI Function Calling (`tool_choice: auto`)으로 GPT가 상황에 맞는 Tool을 자동 호출
- 8개 Tool: 채용검색(외부 API), 이력서 피드백, 모의면접, 호흡운동, 루틴관리, 동기부여(YouTube API), 시장분석, 업계인사이트

### 멀티에이전트 파이프라인
- LangGraph 기반 그래프: 감정분석 → 의도분류 → 에이전트 라우팅 → 병렬 응답
- 감정 강도 4 이상 시 멘탈 케어 에이전트 자동 개입
- 에이전트 간 상호작용 (서로 언급, 보조 참여)

### Slack 스타일 UI
- 그룹채팅 + @멘션 + 1:1 DM
- 실시간 WebSocket 스트리밍
- 에이전트별 SVG 일러스트 프로필
- 멘션 팝업, 프로필 모달, 온보딩 화면

### 픽셀아트 가상 오피스
- Canvas 기반 타일맵 오피스 (책상, 소파, 커피머신, 식물 등)
- 에이전트 캐릭터가 사무실을 돌아다니다가 → 응답 시 책상으로 이동 → 앉아서 타이핑
- 캐릭터별 외형 차이 (머리스타일, 안경, 귀걸이 등)

## Tech Stack

| 계층 | 기술 |
|------|------|
| LLM | GPT-4o mini (OpenAI Function Calling) |
| Agent Orchestration | LangGraph |
| Backend | Python 3.12 / FastAPI / WebSocket |
| Database | PostgreSQL 16 + Redis 7 |
| Frontend | React 18 + TypeScript 5 + Vite |
| Office View | Canvas 2D (타일맵 + 스프라이트 애니메이션) |
| State Management | Zustand |
| Container | Docker + docker-compose |
| CI/CD | GitHub Actions |

## Architecture

```
사용자 메시지 (WebSocket)
  │
  ├─ [감정 분석] GPT → emotion, intensity, intent
  │
  ├─ [에이전트 라우팅] intent + emotion → 참여 에이전트 결정
  │
  ├─ [에이전트 실행] 각 에이전트 → GPT + Tool Calling
  │   ├─ GPT가 tool 호출 판단 (auto)
  │   ├─ Tool 실행 (외부 API / LLM / 내부 로직)
  │   └─ Tool 결과 반영한 최종 응답
  │
  └─ [WebSocket 스트리밍] 타이핑 → 오피스 행동 → 메시지
```

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 22+
- Docker & Docker Compose
- OpenAI API Key

### 1. Clone & Setup

```bash
git clone https://github.com/WindowisPark/jobmate.git
cd jobmate
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# .env 설정
cp .env.example .env
# .env에 JOBMATE_OPENAI_API_KEY 입력
```

### 3. Database (Docker)

```bash
cd ..
docker compose up -d postgres redis
cd backend
alembic upgrade head
```

### 4. Run Backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. Frontend

```bash
cd ../frontend
npm install
npm run dev
```

### 6. Open

http://localhost:5173 에서 확인

## Project Structure

```
jobmate/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph 에이전트
│   │   │   ├── graph.py     # 메인 그래프
│   │   │   ├── router.py    # 감정분석 + 라우팅
│   │   │   ├── profiles.py  # 에이전트 프로필/프롬프트
│   │   │   └── nodes/       # 4개 에이전트 노드
│   │   ├── tools/           # 8개 Tool 구현
│   │   │   ├── schemas.py   # OpenAI Function Calling 스키마
│   │   │   ├── search_jobs.py    # 공공데이터포털 + 사람인 API
│   │   │   ├── motivation.py     # YouTube Data API
│   │   │   └── ...
│   │   ├── api/routes/      # FastAPI 라우트
│   │   ├── models/          # SQLAlchemy ORM
│   │   ├── schemas/         # Pydantic 스키마
│   │   └── services/        # LLM 서비스 (Tool Calling 포함)
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── chat/        # 채팅 UI (메시지, 입력, 멘션)
│       │   ├── office/      # 픽셀아트 오피스 (Canvas)
│       │   ├── sidebar/     # 사이드바 (채널, DM)
│       │   └── common/      # 공통 (아바타, 모달, 온보딩)
│       ├── hooks/           # WebSocket 훅
│       ├── stores/          # Zustand 스토어
│       └── types/           # TypeScript 타입
└── docker-compose.yml
```

## Tool Calling Details

| Tool | 유형 | 담당 | 설명 |
|------|------|------|------|
| `search_jobs` | 외부 API | 박준호 | 공공데이터포털 + 사람인 채용검색 |
| `get_motivation_content` | 외부 API | 정민수 | YouTube 동기부여 콘텐츠 |
| `resume_feedback` | LLM | 김서연 | 이력서/자소서 첨삭 (점수+강점+개선점) |
| `mock_interview` | LLM | 김서연 | 면접 질문 생성 + 답변 팁 |
| `analyze_market` | LLM | 박준호 | 직군별 채용 트렌드 분석 |
| `industry_insight` | LLM | 정민수 | 업계 현실 인사이트 |
| `breathing_exercise` | 내부 | 이하은 | 4-7-8 / 박스 호흡법 가이드 |
| `schedule_routine` | 내부 | 이하은 | 취준 루틴 등록 + 리마인드 |

## License

MIT
