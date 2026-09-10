# JobMate → "힐링 취업 게임" 피벗 플랜

## Context

JobMate(`C:\Users\SKTelecom\project\jobmate`)는 4명의 AI 에이전트가 그룹채팅으로 취준생 멘탈·커리어를 케어하는 서비스다. 원래 SDD에 "Gather Town 스타일 픽셀아트 오피스"가 핵심 정체성이었지만 마지막 커밋(`9d10d7d`)에서 오피스뷰를 언마운트하고 채팅 중심으로 갔다. 이유는 구조적 — 에이전트만 돌아다니고 유저는 구경만 하는 수동적 화면이었기 때문.

오너의 새 방향: **유저가 캐릭터가 되어 싸이월드식 "내 마을"을 방향키/마우스/터치로 돌아다니고, 기능(지원 대시보드·공고 탐방·문서 보관·첨삭)은 건물/NPC로 방문해서 여는 힐링 취업 게임.** 원래 컨셉의 되돌리기가 아니라 완성판.

**성패 원칙 (플랜 전체를 관통):** 건물이 "걸어가서 여는 메뉴 버튼"이면 마을은 마찰만 추가한다. 마을이 존재 가치를 갖는 조건:
1. **상태가 공간에 새겨진다** — D-day≤3 → 지원사무소 불 켜짐, 탈락 연속 → 이하은이 집 앞에 옴, 최종합격 → 마을에 꽃.
2. **NPC가 데이터를 알고 먼저 말 건다** — 박준호: "카카오 서류 마감 내일인데 이력서 v3로 낼 거야?"

### 확정된 결정 (오너)
| 항목 | 결정 |
|---|---|
| 첫 건물 (MVP) | **📝 지원 대시보드** — 오너 노션 "📝 지원" DB 스키마 그대로 포팅 |
| 데이터 저장 | **자체 Postgres** + 노션 CSV 1회 임포트 |
| 렌더링 | **M0 스파이크로 A/B/C 셋 다 그려보고 결정** (Canvas 2D 확장 / Pixi.js+타일셋 / Phaser 3) |
| 모바일 | **v1 동등 지원** (탭 이동 + 가상 조이스틱, 건물은 탭으로도 진입) |

### 검증된 현재 상태
- 오피스 코드는 **삭제 안 됨**: `frontend/src/components/office/OfficeView.tsx`(538줄 Canvas 2D 프로시저럴, 560×360 고정, 입력·카메라 없음), `stores/officeStore.ts`(276줄), `types/office.ts`(`isWalkable`, `TOOL_BEHAVIOR_MAP`). `Layout.tsx`에서 import만 빠짐. `pixi.js ^8.6.0` deps에 있으나 미사용. `langchain-openai`도 미사용(`llm_service.py`는 `openai` 직접 호출).
- LangGraph: `analyze_emotion → plan_tasks → execute_step(loop) → compose_responses`. 플래너 `FAST_PATH_ROUTING` + `_apply_emotion_override`. 9개 툴. Alembic 최신 리비전 **`c3d4e5f6a7b8`**.
- `resume_feedback` JSON 결과를 `MessageBubble.renderToolResult()`가 버림 → 첨삭 건물은 UI만 필요.
- 지원 추적·문서 저장·북마크·프로필 설정 **어디에도 없음**.

### 출시 전 반드시 고칠 결함 (M1에 포함)
- **게스트 전원이 `ANONYMOUS_USER_ID` 공유** + **`chat_service.get_or_create_conversation()`이 `user_id`를 무시**하고 `"general"` → `uuid5("general")` → **모든 유저가 같은 대화방**. 개인 데이터 들어가면 치명적.
- **`jun_ho.py` 툴 실행이 `user_id`만 주입, `db` 세션은 미주입** → `save_job_preferences`가 항상 "DB 세션이 필요합니다" 반환. 새 트래커 툴도 같은 경로 → 공용 executor 필수.
- 쿠키 `secure=False` 하드코딩, CORS `localhost:5173` 고정.
- `pyproject.toml` `>=` 하한만 → 설치본 openai 3.8 / langgraph 1.2. `test_resume_feedback.py`·`test_search_jobs.py`가 실 네트워크 호출.

---

## M0. 렌더링·아트 방향 — ✅ 확정: **픽셀 방(Kenney) + 사람 아닌 픽셀 슬라임 + DOM/CSS**

### 경과 (4회 반복, 오너 판정 기준)
1. 마을 3방식(Canvas/Pixi/Phaser, 임시 손그림) → "셋 다 구림". 렌더러가 아니라 그림 문제.
2. **미니룸 + Kenney CC0 픽셀(Pixi)** → 방은 좋았음. Kenney `sample_indoor.tmx` 파싱으로 타일 역추적.
3. 말랑이 일러스트(saju v2 슬라임 + 코드 폴백 방) → "더 구림". 일러스트 캐릭터가 방 없이 떠 보였고 톤이 앱과 어긋남.
4. **오너 결론: 2번 픽셀 방으로 복귀, 캐릭터는 사람 대신 픽셀 크리처.** 사람 픽셀은 개성 주려면 외주라 회피.

### 확정
| 항목 | 결정 |
|---|---|
| 방 | Kenney 16px 타일 11×8(176×128) — **PIL로 미리 렌더한 `public/room/pixel/bg.png`(3KB)**. 2차 미니룸 레이아웃 그대로(책장·책상·창·문·게시판·거울·소파·침대·티테이블·식물·러그) |
| 캐릭터 | **방 팔레트로 그린 16px 블롭 5종**(`blob_*.png`: 크림=나, 코랄=서연, 파랑=준호, 세이지=하은, 버터=민수). Kenney Tiny Dungeon 슬라임 색상회전판(`slime_*.png`)은 비교용 토글 — 굵은 외곽선이 방과 안 맞아 탈락 |
| 렌더러 | **DOM/CSS만.** 배경 `<img>` + `image-rendering: pixelated`, 방 폭을 176의 **정수배로 스냅**(데스크톱 880=×5, 모바일 352=×2). Pixi·Phaser 없음, 번들 증가 0 |
| 이동 | 가구 탭 hop · 바닥 탭 hop · **방향키/WASD 걷기**(축분리 충돌, 가구 `solid`) · 가구에 부딛혀 멈추는 자리 = stand 반경(±7%,±9%) → 자동 열림 |
| 표기명 | 방 안 NPC는 짧은 이름(구담·설이·까론) + 작은 역할. **채팅 앱 표기(김서연·박준호…)와의 통일은 오너 결정 대기** |
| 말랑이 | `MALLANG_THEME`으로 보관(토글). 삭제하지 않음 — 크로스 훅(saju MBTI 말랑이 = 미니미) 아이디어는 살아 있음 |

### 산출물
- `frontend/src/components/room/roomLayout.ts` — `RoomTheme` 타입, `PIXEL_THEME`(타일→% 변환 `tbox/tpt`), `PIXEL_THEME_KENNEY`, `MALLANG_THEME`, `canStand/hotspotNear(theme,p)`
- `frontend/src/components/room/MallangRoom.tsx` + `.module.css` — 테마 prop, 정수 스냅, 픽셀 CSS(`.pixel`), hop/걷기/충돌/도착 열기, 라벨(모바일 이모지 칩)·말풍선·이름표
- `frontend/public/room/pixel/` — bg.png, blob_*.png ×5, slime_*.png ×5, alt_*.png(유령·박쥐·게), LICENSE
- **`scripts/pixel-room/build.py`** — Kenney 팩 자동 다운로드 → bg.png·블롭·슬라임 재생성(`--preview`). 타일을 바꾸면 여기와 `PIXEL_THEME` 좌표를 함께 고친다
- `frontend/src/spike/SpikePage.tsx` — DEV 미리보기: 테마 3종 토글(픽셀·블롭 / 픽셀·Kenney / 말랑이) + D-day 토글
- `docs/brand/room-art-prompt.md` — 말랑이 테마 배경 프롬프트(보관; 픽셀 테마엔 불필요)

### 검증
tsc strict · 데스크톱 880px/모바일 352px 정수 스냅 · 라벨 탭 → hop → 열기 · 바닥 탭 → 위로 걸어 책상에 막힘 → 열기 · 오른쪽으로 걸어 소파에 막힘 → 열기 · 페이지 에러 0 · 프로덕션 번들 불변.

### M2·M4에 미치는 영향
- M2: `MallangRoom theme={PIXEL_THEME}`가 `/village` 홈. `worldStore`는 `activeHotspot`·`signals`·`npcPrompts`만. 렌더러 슬롯 개념 없음.
- M4 = "신호 연출": `lit` ← `signals`, `npc_prompts` → 말풍선(한 번에 하나), 최종합격 → 픽셀 파티클/꽃 오버레이(CSS). 배경 변형(램프 켜진 책상)은 `build.py`에 타일 한 장 추가로 생성 가능. 추정 1~2일.
- 후속 아트: 블롭 표정 변형(기쁨·걱정) 2~3프레임은 `build.py`의 `draw_blob`에 파라미터 추가로 충분.

---

## M1. 데이터 + API + CSV 임포트 + 운영 수정 (백엔드) — ✅ 완료 (2026-09-09)

**구현:** `models/application.py`(5 모델 · String+CHECK · 라벨 dict) · `alembic d4e5f6a7b8c9`(+`users.is_guest`) · `schemas/application.py` · `services/application_service.py`(D-day·시즌·단계 rank · `change_status` · `build_application_summary` · `format_application_context`) · `services/notion_import.py` · `routes/applications.py`(목록 필터 10종·stats·CRUD·status·CSV) · `routes/companies.py`(companies/tracks/documents 라우터 3개) · `main.py`(라우터 4개 + `settings.cors_origins`) · `auth.py`(`POST /api/auth/guest`, 쿠키 옵션 설정화, `is_guest`) · `chat_service.py`(`room_uuid(conv_id, user_id)` — 전 유저 공유 대화방 버그 수정, anonymous 제거) · `rooms.py`/`jobs.py`(로그인 강제) · `chat.py`(미로그인 WS 4401) · `pyproject.toml`(openai/langgraph 상한 핀, langchain-openai 제거, python-multipart) · `requirements.lock` + Dockerfile lock 설치 · compose/.env.example 에 CORS/쿠키 · 프런트 `LoginPage` 게스트→`/auth/guest`, `authStore.isGuest = user.is_guest`.

**검증:** pytest 48 통과 — 순수 함수(파생 필드·상태 규칙·CSV 정규화 5종 날짜·한글 라벨·종료단계 규칙) + **SQLite 통합 테스트**(`tests/test_api/test_applications_sqlite.py`: 생성→409 중복→필터/시즌/검색→탈락 422→상태 전환·celebration→이력→stats→부분수정→회사 삭제 409/204 · 유저 격리 · CSV dry-run 미저장→커밋→skip→update→임포트 이력이 신호에서 제외). 기존 툴 테스트 2건은 실네트워크 대신 mock. `alembic heads` = d4e5f6a7b8c9. Docker 없어 Postgres 실마이그레이션은 미검증 — 배포 전 `alembic upgrade head` 1회 필요.

**구현 중 결정·교훈:** async 세션에서 `app.history.append` 는 지연 로딩으로 터짐 → 이력은 `db.add` 로. 커밋 후 재조회는 `populate_existing` 으로 identity map 의 stale 관계를 갱신. `zoneinfo("Asia/Seoul")` 은 Windows 에 tzdata 없어 실패 → KST 고정 오프셋. 노션 CSV 날짜는 쉼표 포함("September 12, 2026") — 실제 내보내기는 따옴표로 감싸므로 csv 모듈이 처리.

### (원 계획)

### 1-1. 모델 — `backend/app/models/application.py` (신규, 5 모델)
설계 결정: 상태류는 **`String(30)` + `CheckConstraint`**(기존 `messages.sender_type` 패턴, ENUM `ALTER TYPE` 회피). DB엔 영문 키, 한글 라벨은 `STATUS_LABELS` 등 상수 dict(FE `types/application.ts`에 미러). 파생 필드(D-day·시즌·단계 카운터)는 **Python 서비스 레이어**에서 계산(SQL 뷰 없음).

```python
class ApplicationStatus(StrEnum):  # 노션 상태 12개
    discovered(발견) reviewing(검토중) applied(지원완료) doc_passed(서류통과) coding_test(코테·필기)
    assignment(과제) interview(면접) offer(최종합격) rejected(탈락) withdrawn(포기) no_response(무응답) not_applied(미지원)
ACTIVE_STATUSES = {discovered, reviewing, applied, doc_passed, coding_test, assignment, interview}
EndStage: document/coding_test/written_test/assignment/interview/final  (서류/코테/필기/과제/면접/최종)
EmploymentType: full_time/contract/intern_conversion/intern_experience/bootcamp
HiringType: open_recruitment(공채)/rolling(수시)/always_open(상시)
```

| 테이블 | 컬럼 | 제약 |
|---|---|---|
| `companies` | id, user_id, name(200) NN, industry, size, website, memo, timestamps | `UNIQUE(user_id,name)` |
| `tracks` | id, user_id, name(100) NN, color(7), sort_order | `UNIQUE(user_id,name)` |
| `documents` (stub) | id, user_id, title(200) NN ("이력서 v3"), doc_type CHECK(resume/cover_letter/portfolio), content Text NULL | `UNIQUE(user_id,title)` |
| `applications` | id, user_id, company_id FK RESTRICT NN, track_id FK SET NULL, resume_document_id FK SET NULL, title(300), position(200), posting_url, status default discovered, end_stage NULL, employment_type, hiring_type, discovered_at/applied_at/deadline_at Date, next_event_at DateTime, next_action(500), retrospective Text, timestamps | CHECK status, **CHECK `end_stage IS NULL OR status IN (rejected,withdrawn)`**, `UNIQUE(user_id,company_id,title)`, ix `(user_id,status)`,`(user_id,deadline_at)`,`(user_id,applied_at)` |
| `application_status_history` | id, application_id FK CASCADE, from_status NULL, to_status, changed_at, note, source CHECK(user/agent/import) | ix `(application_id,changed_at)` |

history가 필요한 이유: "14일 내 탈락 3회" 신호는 `updated_at`으로 못 잡음. 임포트 행은 `source="import"`로 신호 계산에서 제외(과거 탈락이 하은 접근을 오발하는 것 방지).
`users.is_guest Boolean default false` 추가(1-5 게스트 수정용).

**Alembic:** `backend/alembic/versions/d4e5f6a7b8c9_add_application_tracker.py`, `down_revision="c3d4e5f6a7b8"`. `models/__init__.py`에 5 모델 export.

### 1-2. 파생 필드 — `backend/app/services/application_service.py` (신규, API/world/chat 공용)
- `today_kst()`; `d_day = (deadline_at - today).days`(None 허용, 음수=마감 지남)
- `season_of`: 기준일 `applied_at or deadline_at or discovered_at` → `"2026 상반기/하반기"`
- 단계 카운터(지원N/서류통과N/면접N): `STATUS_RANK`(discovered0…applied2, doc_passed3, coding_test/assignment4, interview5, offer6) + 종결 상태는 `END_STAGE_RANK`로 도달 단계 환산 → `is_applied(≥2)`, `passed_docs(≥3)`, `reached_interview(≥5)`
- `change_status(app, status, end_stage, note, source)` — 종료단계 검증 단일 지점, history 기록
- `build_application_summary(db, user_id)` — 월드 신호·LangGraph 컨텍스트 공용(M3)

### 1-3. REST — 모두 `Depends(get_current_user_id)`, 스키마 `backend/app/schemas/application.py`, `main.py`에 라우터 4개 등록
`backend/app/api/routes/applications.py`:
| Method | Path | 비고 |
|---|---|---|
| GET | `/api/applications` | 필터 `status*`, `active`, `track_id`, `company_id`, `season`(→날짜 범위), `deadline_from/to`, `event_from/to`, `q`, `sort`, `order`, `limit≤200`, `offset` → `{items, total}`. 5개 뷰 = 이 엔드포인트 + FE 그룹핑 |
| GET | `/stats` | `by_status`, `by_season[]`, `by_track[]`, `funnel` |
| POST | `` | `company_id` **또는** `company_name`(get-or-create), `track_name` 동일. `title` 비면 `"{회사} - {포지션}"`. history 1행 |
| GET/PATCH/DELETE | `/{id}` | PATCH는 status 제외 |
| PATCH | `/{id}/status` | `{status, end_stage?, note?}` — rejected/withdrawn이면 `end_stage` 필수(422), 그 외 서버가 None으로 초기화. `applied` 전환 시 `applied_at` 기본 today. 응답 `celebration: bool` |
| POST | `/import/notion-csv?dry_run&on_duplicate=skip\|update` | multipart (1-4) |

`ApplicationOut` = 컬럼 전부 + `status_label, d_day, season, is_applied, passed_docs, reached_interview, company{}, track{}, resume_document{}`.
`companies.py`(CRUD, 지원서 존재 시 DELETE 409), `tracks.py`(+sort_order), `documents.py`(GET/POST stub). 기존 `routes/jobs.py`의 Pydantic-in-route 패턴 따름.

### 1-4. 노션 CSV 임포트 — `backend/app/services/notion_import.py`
- `python-multipart` 추가. 2MB/2000행 제한, `utf-8-sig`, `csv.DictReader`.
- 헤더 매핑(한글 그대로): `제목→title, 회사→company_name, 포지션→position, 트랙→track_name, 공고 URL→posting_url, 상태→status, 종료단계→end_stage, 고용형태, 채용방식, 발견일, 지원일, 마감일, 다음 일정→next_event_at, 다음 액션→next_action, 한 줄 회고→retrospective, 이력서 버전→resume_document_title`. 수식 열(D-day·시즌·지원N·서류통과N·면접N) 무시. 필수 열 누락 400.
- 정규화: relation 열 `", "` split 첫 값 + 노션 링크 접미 `r"\s*\(https?://(www\.)?notion\.so/[^)]+\)$"` 제거. 날짜 `parse_notion_date`: 범위(`" → "`)면 앞부분; `%Y-%m-%d`, `%Y/%m/%d`, `%B %d, %Y`, `%B %d, %Y %I:%M %p`, `%Y년 %m월 %d일` 순차. select는 라벨 dict 역방향; 상태 빈값→discovered; 미지 값→행 에러; 종료단계 있는데 상태가 탈락/포기 아니면 경고 후 버림.
- 멱등성: `(user_id, company casefold, title casefold)` 매칭 → `skip`(기본)/`update`. 같은 요청 내 get-or-create dict 캐시.
- 응답 `ImportReport{total_rows, created, updated, skipped, errors[{row,field,reason,raw}], preview[10], dry_run}`. dry_run은 전 과정 후 `rollback()`.

### 1-5. 게스트·대화방 격리 (선택안: **게스트도 진짜 `users` 행 + 동일 JWT 쿠키**)
- `POST /api/auth/guest` (`routes/auth.py`): `User(email=f"guest-{uuid4()}@guest.local", password_hash="!guest", nickname="게스트", is_guest=True)` → 기존 `_set_auth_cookies` 재사용.
- 제거: `chat_service.ANONYMOUS_USER_ID`, `ensure_anonymous_user`, `rooms.py`/`jobs.py`의 `_resolve_user_id` → `get_current_user_id`. `chat.py` `"anonymous"` 폴백 → 쿠키 없으면 WS `close(code=4401)`.
- **`get_or_create_conversation`**: 비-UUID 방 id는 `uuid5(NAMESPACE_URL, f"{user_id}:{conversation_id}")` + `user_id` 인자 실제 사용. 기존 anonymous 대화는 고아로 남김(현재도 전 유저 공용이라 손실 아님).
- FE: `LoginPage.tsx::handleGuest` → `api.post("/auth/guest")`; `authStore.isGuest`는 `user.is_guest` 파생(`UserOut`에 추가).

### 1-6. 설정·의존성·테스트 위생
- `config.py`: `cors_origins: list[str]`, `cookie_secure: bool`, `cookie_samesite: str` → `main.py`, `auth.py::COOKIE_OPTS`에서 사용. `docker-compose.yml` env 예시.
- `pyproject.toml`: `openai>=3.8,<4`, `langgraph>=1.2,<2`, `langchain-openai` **제거**, `python-multipart` 추가. `pip freeze > backend/requirements.lock` 커밋, Dockerfile에서 사용. 스모크: `python -c "from app.agents.graph import build_graph; build_graph()"`.
- `tests/test_tools/test_resume_feedback.py`: `generate_response` AsyncMock. `test_search_jobs.py`: `_search_wanted/_search_saramin` mock.
- 신규 순수 함수 테스트: `tests/test_services/test_notion_import.py`(날짜 5종·한글 매핑·종료단계 규칙·dedupe), `test_application_service.py`(d_day/season/rank). DB 통합은 `@pytest.mark.integration`.

### M1 검증
```
cd backend && alembic upgrade head && alembic downgrade -1 && alembic upgrade head && pytest -q
curl -c c.txt -X POST localhost:8000/api/auth/guest
curl -b c.txt -X POST localhost:8000/api/applications -H 'content-type: application/json' \
  -d '{"company_name":"카카오","position":"백엔드 개발자","status":"applied","deadline_at":"2026-09-09"}'
curl -b c.txt "localhost:8000/api/applications?active=true&sort=deadline_at"          # d_day, season 확인
curl -b c.txt -X PATCH localhost:8000/api/applications/<id>/status -d '{"status":"rejected"}'   # 422 종료단계 필수
curl -b c.txt -F file=@notion_export.csv "localhost:8000/api/applications/import/notion-csv?dry_run=true"
curl -b c.txt localhost:8000/api/applications/stats
```
두 번째 게스트 쿠키로 반복 → 데이터 격리 + `/api/conversations`에서 `general` 방이 유저별 분리 확인.

---

## M2. Tracker 건물 UI (프런트) — ✅ 완료 (2026-09-09)

**구현:** `/village` 홈 = `VillageLayout`(MallangRoom + 우측 520px 패널 / 모바일 전체 시트, URL↔열린 가구 동기화, **책상 점등 = 실제 데이터**: 마감 3일 이내 진행 건 → `lit` + 최소 D-day 라벨) · `/village/tracker[/new|/import|/:id]` = `TrackerBuilding`(5개 뷰 탭) · `views.tsx`(🔥보드—빈 컬럼 접기 · 📅캘린더—마감●/일정◆ · 📊시즌별·🧭트랙별—펀넬 헤더+접이식 표 · 📋전체—정렬·검색) · `ApplicationForm`(회사/트랙/이력서 datalist get-or-create, 탈락·포기 시에만 종료단계 필수) · `ApplicationDetail`(이력 타임라인·수정·삭제) · `StatusChangeSheet`(DnD 대신 시트, celebration 토스트) · `ImportCsvDialog`(dry-run 리포트→확정, skip/update) · `applicationStore`(낙관적 상태변경+롤백, 셀렉터) · `worldStore`(activeHotspot, HOTSPOT_ROUTES: mental→`/chat/dm-ha_eun`) · `types/application.ts`(백엔드 라벨 미러) · `api.ts` put/upload(FormData) · `/chat/*` 기존 Layout, 사이드바 "🏡 내 방" · `/documents` `/jobs` 는 ComingSoon 패널.
**개발 환경:** `backend/scripts/dev_sqlite.py` — Postgres·Redis 없이 SQLite+가짜 Redis 로 백엔드 기동(인증·트래커 API 동작, 채팅·공고검색 비활성). 프런트 개발·UI 검증용.
**검증(Playwright, dev_sqlite 백엔드):** 게스트 로그인→온보딩→/village→책상 탭→패널→지원 추가(트랙·이력서 자동 생성, applied→지원일 자동)→상세→상태 변경(서류통과)→탈락 선택 시 종료단계 셀렉트 노출→보드/캘린더/시즌/표→책상 `D-2` 점등→패널 닫기→모바일 방/보드. 페이지 에러 0, tsc 통과.
**교훈:** 모바일 시트 위로 방 라벨이 튀어나옴 → `.room{z-index:0}`으로 stacking context 격리. 520px 패널에 칸반 7컬럼은 안 들어감 → 빈 컬럼 숨김+토글.

### (원 계획)

### 2-1. 라우팅 — `frontend/src/App.tsx`
```
/login, /register (기존)
/* → AuthGuard → Onboarding | <VillageLayout/>
   /village                  VillagePage (홈; "/" → /village)
   /village/tracker          TrackerBuilding — desktop: 우측 480px 패널 over 마을 / ≤768: full-screen sheet
   /village/tracker/:id      ApplicationDetail (패널 내)
   /village/tracker/import   ImportCsvDialog
   /chat, /chat/:roomId      기존 Layout(Sidebar+ChatRoom) 유지 — 이후 "사무실 건물"로 편입
```
`components/village/VillageLayout.tsx` = `<VillageScene/>`(렌더러 슬롯) + `<NpcBubbleLayer/>` + `<TouchControls/>`(모바일) + `<Outlet/>`(건물 패널). 패널 열림 = `worldStore.activeBuilding`이며 URL과 동기화(뒤로가기 → `exitBuilding()`). `Layout.tsx`/`Sidebar.tsx`에 "🏡 마을로" 링크.

### 2-2. `worldStore` — 렌더러 경계 계약 (`stores/worldStore.ts`, `types/world.ts`, `lib/eventBus.ts`)
```ts
type BuildingId = "tracker" | "office" | "resume_studio" | "library";   // v1은 tracker만 enabled
type Vec2 = { x: number; y: number };   // 월드 좌표(타일 단위 float)
interface WorldStore {
  // 렌더러 → 스토어
  player: { pos: Vec2; facing; moving }; setPlayerPosition(); setNearbyNpc(agentId|null);   // 근접 판정(반경 1.5타일)은 렌더러 책임
  requestEnterBuilding(id);           // 문 도착 or 건물 탭 → 거리 검사 후 enterBuilding 또는 moveTarget=door + pendingEnter
  // 입력 계층 → 스토어 (렌더러는 이것만 읽어 이동)
  inputVector: Vec2; setInputVector();   // 키보드/조이스틱, 데드존 적용 후 정규화
  moveTarget: Vec2|null; setMoveTarget(); // tap-to-move (렌더러가 screenToWorld 후 호출). inputVector 우선
  // UI ↔ 스토어
  activeBuilding; enterBuilding(); exitBuilding(); nearbyNpc;
  signals: WorldSignals|null; refreshSignals(); acceptPrompt(id); dismissPrompt(id); ackCelebration(appId);
  on(handler: (e: WorldEvent) => void): () => void;   // building:enter/exit, npc:near/talk, player:arrived, signals:updated
}
interface IWorldRenderer { mount(el); unmount(); resize(w,h); screenToWorld(p): Vec2 }   // M4에서 선택 렌더러가 구현
```
규칙: **스토어는 렌더러를 import하지 않음.** 건물 lit/NPC mood는 `signals`에서만 파생 → 렌더러는 표현만.
M2 플레이스홀더 `components/village/VillageScene.tsx`: DOM/CSS 격자(건물 카드 + `AgentAvatar` NPC + 말풍선), `IWorldRenderer` no-op. 카드 클릭 = `requestEnterBuilding`. 렌더러 없이 전체 플로우 검증.
입력: `components/village/TouchControls.tsx`(가상 조이스틱 반경 48px 데드존 0.15, 화면 탭→`setMoveTarget`, 건물/NPC 탭), `hooks/useKeyboardMovement.ts`(WASD/화살표).

### 2-3. `applicationStore` (`stores/applicationStore.ts`, `types/application.ts`)
- 타입: 백엔드 라벨 dict 미러, `Application`, `Company`, `Track`, `DocumentStub`, `ImportReport`.
- 상태: `byId`, `order`, `companies`, `tracks`, `documents`, `stats`, `view: board|calendar|season|track|table`, `filters`.
- 액션: `fetchAll/fetchStats/create/update/remove/importCsv`, `changeStatus(id,status,endStage?,note?)` — 낙관적 업데이트+롤백, 성공 시 `worldStore.refreshSignals()`.
- 셀렉터(순수): `selectBoardColumns`(ACTIVE 순서, deadline asc nulls last), `selectCalendarEvents(y,m)`(마감● / 다음일정◆), `groupBySeason`, `groupByTrack`.
- `utils/api.ts`에 `put`, `upload(path, FormData)` 추가(현재 항상 `application/json` 헤더 → multipart는 제거 필요).

### 2-4. Tracker 컴포넌트 (`components/tracker/`, `Tracker.module.css`)
`TrackerBuilding`(패널 셸, 뷰 탭 5, "+ 지원 추가", "CSV 가져오기"; `hooks/useIsMobile.ts`로 `Layout.tsx`의 768 분기 추출) · `BoardView`(🔥 7컬럼 가로 스크롤, `DDayChip` ≤3 빨강/≤7 노랑, **DnD 대신 카드 탭→`StatusChangeSheet`**) · `CalendarView`(📅) · `SeasonView`/`TrackView`(funnel 숫자 + 접이식 테이블) · `TableView`(📋 정렬·검색) · `ApplicationForm`(회사 콤보 get-or-create, **rejected/withdrawn일 때만 종료단계 노출·필수**, 이력서 버전 select) · `ApplicationDetail`(+`StatusTimeline`) · `ImportCsvDialog`(dry-run 리포트 → 확정) · `StatusBadge`, `DDayChip`, `StatusChangeSheet`.

### M2 검증
`npm run build`(tsc strict) → `/village` 건물 카드 탭 → 패널/시트, 5개 뷰 전환, 폼에서 `탈락` 선택 시 종료단계 노출, CSV dry-run 미리보기 → 확정, ≤768 DevTools에서 full-screen sheet + 뒤로가기 `exitBuilding`.

---

## M2.5 UX 패스 — ✅ 완료 (2026-09-09, 오너 피드백 4건)

| 피드백 | 조치 |
|---|---|
| 1. 상호작용 진입 전 확인 단계 | 도착 시 **확인 간판**(`{가구} 열기 · Enter` / `{친구}와 이야기하기 · Enter`, ✕ 취소). 같은 대상 재탭·Enter/Space 로 열림. 걷다가 닿아도 자동 열림 없음 |
| 2. 진입 시 UI 분위기 급변 | `/village` 하위 전부 **따뜻한 토큰 오버라이드**(`Village.module.css .layout`) — 트래커·채팅 패널이 방 팔레트를 잇는다. `MoodCheckIn` 하드코딩 네이비 제거, 사람 얼굴 SVG `AgentAvatar` → **블롭 스프라이트**로 전역 교체 |
| 3. 채팅 커버 단위 재계획 | 채팅은 별도 앱이 아니라 **방 안 패널**(`/village/chat/dm-{agent}`, `ChatBuilding` → `ChatRoom embedded`). **한 친구와의 DM 만** — 그룹 채팅·네 명 프레즌스 스트립 제거(오너: "다같이 이야기할 필요가 있을지 고민중"). 기분 체크인은 토닥이 DM 에서만 |
| 4. 맵 아이콘 품질 저하 | 이모지 전부 제거, **Galmuri11 픽셀 폰트 간판**(OFL, `public/fonts/galmuri/`) + 2px 외곽선·하드 섀도. 모바일은 말풍선 1개·준비 중 간판 숨김 |

**이름 확정(전역):** 첨삭이(seo_yeon·커리어 코치) · 탐색이(jun_ho·취업 리서처) · 토닥이(ha_eun·멘탈 케어) · 꿀팁이(min_su·현직자 멘토) — `profiles.py`·`llm_service.py`·`entrypoint.sh`·`types/agent.ts`. README 는 미갱신.
**검증(Playwright):** 확인 간판 표시 → Enter → 트래커 · NPC 탭 → 간판 "토닥이와 이야기하기" → Enter → DM 패널 · Galmuri 로드 · 모바일 방/DM · 페이지 에러 0 · tsc 통과.
**M3 연결:** 말풍선 우선순위(모바일 1개)는 `npc_prompts.priority` 가 정한다. 간판 확인 후 DM 진입 시 `accept` 호출 지점 = `VillageLayout.onOpen(kind:"npc")`.

---

## M2.6 제출물 다대다 — ✅ 완료 (2026-09-10, 자소서 배제 채용 트렌드 대응)

**계기:** 한화생명·SK하이닉스·신한은행 등이 자소서를 빼는 흐름. 승률 엔진 자체는 상태 전이(`application_status_history`) 위에 서 있어 영향이 없지만, **지원 1건 = 이력서 1개** 가정이 병목이었다. 이력서+포트폴리오+경험기술서를 함께 내는 전형에서는 "포트폴리오 v2 를 붙인 지원의 서류 통과율"을 물을 수 없다. 데이터가 쌓이기 전에 처리해 이전 비용을 없앴다.

**구현:**
- `models/application.py` — `ApplicationDocument`(application_id·document_id·attached_at, `UNIQUE(app,doc)`, doc 인덱스). `Application.resume_document_id` **제거**, `Application.documents` 다대다(`secondary`, selectin)로 대체. `DOC_TYPES` 에 `experience`(경험기술서)·`other` 추가 + `DOC_TYPE_LABELS`.
- `alembic e5f6a7b8c9d0` — 테이블 생성 → 기존 `resume_document_id` 값을 조인 테이블로 이전 → 컬럼 드롭 → `ck_documents_doc_type` 교체. downgrade 는 지원별 가장 먼저 붙인 제출물 하나만 되돌리고(나머지 연결 소실), 새 doc_type 값을 `resume` 로 정리한 뒤 CHECK 복원.
- `application_service.py` — `doc_ref`, `primary_resume`(이력서 종류 첫 번째 = 기존 `resume_document` 응답의 파생), `attach_document`/`detach_document`/`set_documents`/`replace_resume`. **모두 컬렉션만 조작** — `secondary` 관계가 연결 행을 관리하므로 직접 INSERT 하면 UNIQUE 에 걸린다.
- `routes/applications.py` — `_resolve_refs`(회사·트랙) / `_resolve_doc` · `_resolve_docs`(제출물) 분리. 생성·수정에서 `documents` 는 집합 전체 대체, `resume_document_*` 는 이력서 슬롯만 교체. `POST /{id}/documents`·`DELETE /{id}/documents/{doc_id}` 추가. `GET /stats` 에 **`by_document`**(제출물 버전별 total/applied/passed_docs/interview/offer).
- `notion_import.py` — '이력서 버전' 은 `documents=[doc]` / `replace_resume` 로.
- 프런트 — `types/application.ts`(`DocType`·`DOC_TYPE_LABELS`·`DocumentInput`·`Application.documents`·`Stats.by_document`), `ApplicationForm` 에 "추가 제출물" 반복 입력(제목+종류+빼기, 제출 시 `documents` 로 집합 전체 전송), `ApplicationDetail` 은 이력서 한 줄 대신 제출물 전체를 종류 라벨과 함께 표시.

**검증:** pytest **49 통과**(신규 `test_multiple_documents_and_win_rate_by_document`: 이력서+포폴 동시 생성 → 경험기술서 추가 → `by_document` 승률 분리 → 이력서만 교체해도 포폴·경험기술서 유지 → 연결 해제 후 문서는 존속 → 재해제 404 → `documents` 집합 대체). `alembic heads` = `e5f6a7b8c9d0`. 실행 중 서버에 httpx 로 생성·교체·통계 왕복 확인. tsc 통과, Playwright 로 폼 입력 → 상세에 "제출물: 이력서 v5 (이력서) · 포트폴리오 v3 (포트폴리오) · 경험기술서 v2 (경험기술서)" 확인, 페이지 에러 0.

**남긴 판단:**
- **전형 단계는 그대로.** AI 역량검사·직무적합성 검사 같은 새 관문은 `status` 가 String+CHECK 라 라벨 한 줄 + 마이그레이션 하나로 붙는다. 실제 수요를 보고 결정.
- **승률 분모 주의.** 자소서가 빠지면 지원 비용이 낮아져 건수가 늘고 통과율이 떨어진다. 실력 저하가 아니라 전략 변화이므로 `hiring_type`(공채·수시·상시)별로 갈라 보여줘야 오도하지 않는다. 컬럼은 이미 있고 통계 축 추가만 남았다.
- **버전 신호는 약해지고 타이밍 신호가 세진다.** 자소서는 회사마다 새로 쓰지만 이력서는 분기에 한 번 고친다. 다음 인사이트 축은 `discovered_at → applied_at` 리드타임과 `hiring_type` 이다.
- Postgres 실마이그레이션은 여전히 미검증(Docker 없음) — 배포 전 `alembic upgrade head` 1회 필요.

---

## M2.7 스크래핑 제거 — ✅ 완료 (2026-09-10, 법적 리스크 정리)

**계기:** 비영리 개인 프로젝트면 안전한지 물음. 아니다. 한국에서 채용공고 크롤링 분쟁의 주 근거인 **저작권법상 데이터베이스제작자 권리에는 영리 요건이 없다.** 부정경쟁방지법 성과 도용 조항만 "자신의 영업을 위하여" 요건이라 개인 사용이면 빠질 여지가 있고, 이용약관 위반과 정보통신망법 접근권한 쟁점은 영리와 무관하다. 채용공고 크롤링을 두고 잡코리아와 사람인이 다툰 사건이 이 도메인의 직접 선례다.

**코드가 리스크를 키우던 지점 3가지:**
1. 원티드 **비공개 내부 엔드포인트**(`/api/v4/jobs`) 직접 호출 + Referer 위조.
2. 사람인 **검색 결과 HTML 정규식 파싱**(`zf_user/search/recruit`). 공식 오픈 API 가 있는데 안 씀.
3. **User-Agent 4종 무작위 로테이션.** 단순 수집이 아니라 차단 회피로 읽히는 결정적 신호. 기능상 필요도 없었음.

여기에 저장소가 **공개 상태**라 그 코드가 그대로 읽혔다. 취업 포트폴리오로 쓰는 저장소에 채용 사이트 우회 코드가 있는 건 법적 리스크보다 먼저 오는 실질 리스크.

**조치:**
- `tools/search_jobs.py` 529→381줄. `_USER_AGENTS`·`_random_headers`·`_search_wanted`·HTML 파싱·`_strip_html`·`_xml_tag` **전부 삭제**.
- **사람인 공식 오픈 API**(`oapi.saramin.co.kr/job-search`)로 일원화. 이미 있으나 안 쓰이던 `settings.saramin_api_key` 를 드디어 사용.
- 고정 UA `JobMate/1.0 (+저장소 URL)` — 우리가 누구인지 밝힌다.
- 지역·경력은 **파라미터로 안 보내고 받은 결과에서 고른다.** 코드 체계를 문서로 확인하기 전까지 확실한 파라미터만 전송. 좁혀서 0건이면 원래 목록을 준다(`_prefer`) — 빈손이면 에이전트가 "없다"고 단정한다.
- 키가 없거나 API 가 실패하면 **공고를 지어내지 않는다.** 예전 fallback 은 가짜 공고 1건을 만들어 냈다. 이제 `source: "manual"` + 사람인·원티드·잡코리아 **검색 링크**만 준다(링크 자체는 문제없음). 도구 스키마 설명에 "manual 이면 지어내지 말고 링크를 안내하라"를 명시.
- README·`.env.example` 정정. README 의 옛 에이전트 이름(김서연·박준호·이하은·정민수)도 이 참에 갱신.

**검증:** pytest 60 통과. `test_search_jobs.py` 재작성 7건 — 키 없을 때 가짜 공고 대신 링크, 공식 엔드포인트·access-key·식별 UA 전송, `&gt;` 포함 지역 파싱, 결과 1건이 객체로 올 때, 지역 필터가 비면 폴백, API 예외·빈 결과 처리. 네트워크 미접촉. ruff 신규 오류 0.

**미검증:** 실제 API 키가 없어 **라이브 응답 1회 확인이 필요하다.** 파라미터·응답 필드명은 공식 가이드로 대조했다.

**문서 대조 (2026-09-10):** 사람인 오픈 API 가이드를 직접 확인해 다음을 고정했다.
- **이용신청은 열려 있다.** 준비 중 아님. 소속란에 학교명을 쓸 수 있어 개인·학생도 신청 가능하나 **이용목적 50자 이상 + 목적 심사**가 있다. "안 준다"는 인상은 이 심사 단계에서 온 것으로 보인다.
- **일 호출 500건 제한.** 캐시 TTL 6시간이 이미 있어 개인 사용에는 충분.
- **약관이 재판매·유료화·대가 수취를 금지한다.** 지금처럼 비영리면 오히려 적합하지만, **상업화하면 이 경로는 닫힌다.** 그때는 공공데이터포털 워크넷·고용24 채용정보 API 로 갈아타야 한다(`settings.public_data_api_key` 가 선언만 되고 안 쓰이는 상태로 이미 있다).
- **파라미터 확인:** `access-key`(필수), `keywords`, `count`(최대 110), `start`, `fields`, `loc_cd`, `job_cd`, `job_mid_cd`, `ind_cd`, `job_type`, `experience-level`, `published`, `sort`. 지역·직종 코드 테이블이 필요해 서버 필터 대신 결과 필터를 유지했다.
- **응답 확인 후 방어 코드 2건 추가:** `experience-level` 은 보통 `name`("경력 2~3년")이 오지만 없을 때를 대비해 `min`·`max` 로 만든다. `expiration-date` 는 `fields` 로 요청해야 오므로 `expiration-timestamp` 폴백을 둔다. 테스트 10건으로 고정.


**남은 판단:** 사용자가 붙여넣은 공고 URL 1회 조회는 성격이 다르다(대량 수집이 아니라 열람 대행). 공고 읽기 도구는 지금 방식보다 오히려 안전 — 다만 임의 URL 서버 조회는 SSRF 표면이 생기므로 채용 도메인 허용목록 필요.

---

## M2.8 인사이트 화면 — ✅ 완료 (2026-09-10)

**계기:** "공고 탐색을 굳이 여기서 할 필요가 있나." 맞는 직감이었다. 검색은 사람인을 못 이기고 하루 500건으로는 탐색 제품이 성립하지 않으며, 무엇보다 **공고 검색 결과는 내 데이터가 아니라 방이 반응할 신호를 하나도 만들지 않는다.** 반면 인사이트는 이미 다 만들어져 있는데 화면만 없었다.

**발견:** `GET /applications/stats` 가 상태별·시즌별·트랙별·제출물별·펀넬을 전부 계산해 내려주고 `applicationStore.fetchStats` 도 있는데 **호출하는 곳이 한 군데도 없었다.** 화면의 펀넬 숫자는 목록에서 그때그때 센 값이었고, M2.6 에서 넣은 `by_document` 는 소비자가 아예 없었다.

**구현:**
- 백엔드 `by_hiring_type` 추가(`HiringTypeStat`). 자소서가 빠진 수시는 지원 비용이 낮아 건수가 늘고 통과율이 떨어진다. 실력이 아니라 전략 변화인데 전체 평균만 보면 거꾸로 읽힌다. **분모를 갈라야 오도하지 않는다.**
- `components/tracker/InsightView.tsx` — 전체 흐름(펀넬 막대 4단, 지원 대비 비율) · 채용방식별 · 제출물별 · 트랙별. 계산은 전부 서버, 화면은 읽기만.
- **표본 경고:** 지원 5건 미만이면 비율을 강조하지 않고 흐리게 + `?` 표시(툴팁으로 건수 안내). 3건 중 1건을 33%라 부르면 거짓말에 가깝다.
- 트래커 6번째 탭 "인사이트". 탭 진입 시 `fetchStats` — 상태를 바꾸고 돌아오면 숫자가 낡는다.

**검증:** pytest 65 통과(신규 2건 — 채용방식별 분리, 미지정 라벨). tsc 통과. 지원 11건(공채 5·수시 6, 이력서 v3/v4·포폴 v2·경험기술서 v1)을 심어 데스크톱 패널·모바일 시트 확인. 공채 40% vs 수시 50% 로 갈리고 전체는 45%. 페이지 에러 0.

**보류한 결정:** 공고 게시판 건물. 지금 방에 간판이 서 있고 누르면 준비 중 안내가 뜬다. 링크 모음으로 바꾸거나 간판을 빼야 한다. `search_jobs` 는 키가 없으면 링크만 주므로 해가 없어 **사람인 키 신청을 서두를 이유는 사라졌다.**

## M3. 월드 신호 + NPC 선제 대사 + 트래커 툴 — ✅ 완료 (2026-09-10)

**한 줄:** 방이 데이터를 알고 먼저 말을 건다. 노션이 못 하는 유일한 부분이다.

**백엔드**
- `GET /api/world/state` — 지원 요약을 신호로 바꿔 내려준다(책상 점등·NPC 표정·말풍선). 계산은 `build_application_summary` 하나에서만 나온다(채팅 컨텍스트와 같은 진실).
- `services/npc_prompt_service.py` — **템플릿만, LLM 0회.** 마감·마감초과·탈락스트릭·축하·다음일정·무활동 6종. 에이전트당 하나, 최대 3개. 마감이 가까울수록 위로.
- `POST /prompts/{id}/accept` — 그 대사를 DM 에 agent 메시지로 남긴다. **여기서도 LLM 은 안 돈다.** 사용자가 답장할 때 history 로 읽혀 맥락이 이어진다. dismiss 24h, 축하 ack 7d(Redis).
- LangGraph: 상태에 `application_summary`, WS 경로와 `chat_service` 양쪽에서 로드. 네 노드가 `format_application_context` 로 각자 관점의 한 문단을 받는다.
- 플래너: `_prepend_step` 헬퍼 추출(재정렬 로직 단일화) + `_apply_tracker_override`. 마감 임박 → 탐색이, 탈락 스트릭 → 토닥이, 축하 → 꿀팁이 보조.
- 도구 9→11: `get_my_applications` · `update_application_status`. **M2.5 에서 실행기를 공용화해 둔 덕에 등록만으로 세션이 붙었다.** 탈락에 종료단계가 없으면 고치지 않고 되묻고, 여러 건이 걸리면 `ambiguous` 를 주고 아무것도 바꾸지 않는다.
- `Message` 의 JSON 컬럼에 sqlite variant — 운영 스키마는 그대로, Docker 없이 채팅 경로를 테스트할 수 있게 됨.

**프런트**
- `worldStore` 재작성 — 신호·말풍선을 서버에서 받는다. 방 진입·탭 복귀·패널에서 방으로 돌아올 때 갱신.
- `MallangRoom` 에 `bubbles` prop. **하드코딩 예시 문구 제거.** 말풍선을 누르면 accept → DM 이동 + 답장 초안이 채워진 상태로 시작. ✕ 로 닫으면 하루 조용.
- 도구 결과 카드 2종 추가(`ApplicationListCard`·`StatusChangeResult`). ambiguous 면 "안 바꿨다"고 보여준다.
- **공고 게시판을 실제로 쓸 수 있게 바꿈**(준비 중 안내 제거). 검색은 채용 사이트로 내보내고, 발견한 공고를 트래커에 담는 다리 역할만 한다. M2.7 의 판단("탐색은 축이 아니다")과 같은 선.

**검증:** pytest 104 통과(신규 4파일 51건). Playwright 로 실데이터 왕복 — 마감 D-1 책상 점등, 탐색이가 이력서 버전을 짚어 말 걸기, 탈락 3건에 토닥이 등장, 말풍선 → DM 이동 + 대사 저장 + 초안 채움, 공고 게시판 담기 폼. 페이지 에러 0.

**고친 것 (테스트·실행이 잡음)**
- 최종합격 직후 "요즘 쉬고 있구나" 가 같이 뜨던 규칙 → 축하·최근결과가 있으면 무활동 체크인을 막는다.
- 말풍선이 `.sprite { pointer-events: none }` 때문에 안 눌리던 문제.
- 방 오른쪽 친구의 말풍선이 방 밖으로 새던 문제 → 줄바꿈 + 가장자리 정렬.
- `dev_sqlite` 의 FakeRedis 에 `setex`·`mget` 이 없어 월드 API 가 500. agents·messages 테이블도 추가.

**남은 것:** DM 은 아직 지난 대화를 불러오지 않는다(원래 그랬다). 수락한 대사는 응답으로 받아 화면에 직접 올려 우회했다. 대화 이력 로딩은 별건.

### (원 계획)

### 3-1. `GET /api/world/state` — `routes/world.py`, `services/npc_prompt_service.py`
`build_application_summary` 재사용(chat.py와 단일 진실).
```json
{ "today": "...",
  "signals": { "urgent_deadlines": [...0<=d_day<=3], "overdue": [...], "next_event": {...}|null,
               "stage_counts": {}, "active_count": 7,
               "recent_outcomes": [...14일, source!=import, rejected|offer], "rejection_streak_14d": 3,
               "celebration": {"application_id","title"}|null },
  "buildings": [{"id":"tracker","lit":true,"badge":2,"celebrating":false}],
  "npcs": [{"agent_id":"jun_ho","mood":"normal|concerned|excited","wants_to_talk":true,"approach_player":false}],
  "npc_prompts": [{"id":"deadline:<app_id>:<date>","agent_id":"jun_ho","kind":"deadline","priority":90,
                   "text":"카카오 서류 마감 내일인데 이력서 v3로 낼 거야?","suggested_reply":"응, v3로 낼게. 체크리스트 좀 봐줘"}] }
```
`npc_prompts` 규칙(**템플릿만, LLM 0회**): `deadline`(jun_ho, d_day≤3, 우선순위 100−d_day×10) · `rejection_streak`(ha_eun ≥3/14d, 95, `approach_player=true`) · `celebration`(min_su+seo_yeon, 99) · `next_event`(seo_yeon, 24h 내 면접/코테 → "내일 {회사} 면접이네, 모의면접 한 번 돌려볼까?") · `idle_checkin`(ha_eun, 활성 0건 & 7일 무활동, 10). 최대 3개, 에이전트당 1개. Redis `npc_prompt:dismissed:{user_id}:{id}` TTL 24h.
- `POST /api/world/prompts/{id}/accept` → 유저 네임스페이스 `dm-{agent_id}` 방에 `save_agent_message`로 **NPC 대사를 agent 메시지로 INSERT**(LLM 없음) → 이후 유저 답장 시 history에 포함되어 맥락 인지. `POST .../dismiss`, `POST /api/world/celebrations/{app_id}/ack`(Redis 7d).

### 3-2. LangGraph 컨텍스트 주입
- `agents/state.py::JobMateState`에 `application_summary: dict | None`.
- `routes/chat.py` Phase 1 블록(line 124~133, `load_user_preferences` 옆)에서 `build_application_summary` 로드 → `graph.ainvoke({... "application_summary"})`. `chat_service.process_user_message`도 동일.
- `application_service.format_application_context(summary, agent_id)` — 에이전트별 관점(jun_ho/seo_yeon=마감·일정·이력서 버전, ha_eun=최근 결과·활성 수만·수치 나열 금지, min_su=시즌 funnel), 500자 상한. 각 `agents/nodes/*.py`의 `context +=` 블록에 1줄.

### 3-3. 플래너 오버라이드 — `agents/planner.py`
- `_apply_emotion_override`의 step_id 재정렬 로직을 `_prepend_step(steps, agent_id, action_hint, tool_hint)` 헬퍼로 추출.
- `_apply_tracker_override(steps, summary, intent)`: urgent_deadlines 있고 intent∈{general, job_search, resume_interview} → jun_ho prepend(`deadline_reminder`, `get_my_applications`) / rejection_streak≥3 → ha_eun prepend(감정 오버라이드와 중복 방지) / celebration → min_su assist append. fast-path·LLM-path 양쪽에서 `_apply_emotion_override` 직후 호출. `PLANNER_PROMPT`에 `지원 현황 요약: {tracker_line}` 1줄.

### 3-4. 툴 2개 + DB 세션 주입 버그 수정 — `tools/applications.py`, `agents/nodes/_tool_exec.py`
- `get_my_applications(user_id, status?, only_urgent?, query?, limit=10, *, db)` → `{items[], total, summary_line}`
- `update_application_status(user_id, application_id?|title_query?, status, end_stage?, note?, *, db)` — title ILIKE 다건이면 `{"ambiguous":[...]}` 반환(LLM이 되물음). `change_status()` 공용, `source="agent"`.
- `tools/schemas.py` 등록(status enum + 한글 라벨 병기), `tools/__init__.py::ALL_TOOLS`, `agents/profiles.py` tools(jun_ho 둘 다, 나머지 `get_my_applications`), `PLANNER_PROMPT` 도구 목록 갱신.
- **`_tool_exec.py::make_tool_executor(user_id)`**: `DB_AWARE_TOOLS = {search_jobs, save_job_preferences, get_my_applications, update_application_status}` → `async with async_session() as db: await fn(**args, user_id=user_id, db=db); await db.commit()`. 4개 노드의 로컬 `execute_tool`을 교체, `jun_ho.py::_DB_AWARE_TOOLS` 제거.
- `chat.py::TOOL_ACTION_MAP`에 두 툴 추가. FE `MessageBubble.renderToolResult`에 `get_my_applications`(`components/chat/ApplicationListCard.tsx`) / `update_application_status`(toast + `applicationStore.fetchAll()` + `worldStore.refreshSignals()`) 케이스.

### 3-5. 선제 인사 흐름 (비용 0)
`/village` 진입 및 `visibilitychange` → `refreshSignals()` → `NpcBubbleLayer`가 말풍선 → 클릭 → `accept` → `chatStore.addMessage("dm-jun_ho", msg)` + `setActiveRoom` + `navigate("/chat")` + `MessageInput` 초기값 `suggested_reply` → 유저가 전송할 때만 WS→LLM. 닫기 → `dismiss`.

### M3 검증
```
curl -b c.txt localhost:8000/api/world/state | jq '.buildings, .npc_prompts'   # D-1 지원 1건 → tracker.lit=true, jun_ho 프롬프트
curl -b c.txt -X POST localhost:8000/api/world/prompts/<id>/accept              # DM에 agent 메시지 1행, LLM 호출 로그 없음
pytest tests/test_agents/test_planner_override.py tests/test_services/test_npc_prompts.py
```
UI: 마을 로드 → 말풍선 → 클릭 → DM 열림·NPC 첫 대사·프리필 → 전송 시에만 `agent_typing`. 채팅 "카카오 서류 탈락했어" → `update_application_status` 호출·토스트·보드 갱신·ha_eun 반응(탈락 3건 seed).

---

## M4. 렌더러 통합 (M0 결정 후)
`VillageScene.tsx` 내부를 `renderers/{canvas2d|pixi|phaser}/`의 `IWorldRenderer` 구현으로 교체, `TouchControls`/`useKeyboardMovement` 연결, 근접 판정·문 도착 → `requestEnterBuilding`. `signals` → 건물 점등·NPC 접근·축하 연출. 제거: `officeStore.ts`, `types/office.ts`, `OfficeView.tsx`, `profiles.py::office_position`, `chat.py::office_state` 이벤트, 미선택 라이브러리.
**검증:** 렌더러 파일에서 `applicationStore`/`api` import 0건(grep), 모바일 탭 이동·조이스틱·건물 탭 진입, D-day≤3 점등, 탈락 스트릭 시 하은 접근, 최종합격 축하 + ack.

---

## 리스크 / 트레이드오프
- **String+CHECK vs ENUM**: 확장 용이성 선택. 잘못된 값은 DB CHECK + Pydantic 양쪽에서 차단.
- **게스트=실유저 행**: 유령 계정 누적 → `is_guest AND created_at < now()-30d` 정리는 후속. 코드 경로 단일화 이득이 더 큼.
- **선제 대사는 템플릿**: 자연스러움↓, 비용 0·결정적·테스트 가능. 클릭 후 첫 LLM 응답은 history의 NPC 대사로 맥락 유지.
- **openai 3.x / langgraph 1.x 고정**: `tool_choice="auto"`, `assistant_msg.model_dump()` 등 v1 API 의존 코드의 3.x 동작 확인이 M1 검증 항목.
- **모바일 칸반 DnD 미지원** — 탭→상태 변경 시트로 대체(의도된 결정).
- ~~**`search_jobs` 스크래핑 취약성**은 이 플랜 범위 밖~~ → **M2.7 에서 해소.** 스크래핑을 걷어내고 사람인 공식 오픈 API 로 일원화했다. 취약성이 아니라 법적 리스크가 이유였다.

## 진행 순서
M0(스파이크) ∥ M1 → M2 → M3 → (M0 결정) → M4. 각 마일스톤 커밋은 main 직접 푸시 규약 따름(유저 노출 변경은 푸시 전 확인).
