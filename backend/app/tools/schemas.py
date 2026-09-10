from app.models.application import END_STAGE_LABELS, STATUS_LABELS

STATUS_KEYS = list(STATUS_LABELS)
END_STAGE_KEYS = list(END_STAGE_LABELS)

"""OpenAI Function Calling 스키마 정의 — 8개 Tool."""

TOOL_SCHEMAS: dict[str, dict] = {
    "search_jobs": {
        "type": "function",
        "function": {
            "name": "search_jobs",
            "description": (
                "사람인 공식 오픈 API 로 채용공고를 검색합니다. "
                "사용자가 채용공고·일자리·취업 정보를 원할 때 사용합니다. "
                "응답의 source 가 'manual' 이면 공고를 받지 못한 것이므로, "
                "공고를 지어내지 말고 search_links 를 그대로 안내하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "검색 키워드 (예: ['백엔드', 'Python'])",
                    },
                    "location": {
                        "type": "string",
                        "description": "근무 지역 (예: '서울', '경기')",
                    },
                    "career_level": {
                        "type": "string",
                        "enum": ["신입", "경력 1-3년", "경력 3-5년", "무관"],
                        "description": "경력 수준",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "결과 수 (기본 5)",
                    },
                },
                "required": ["keywords"],
            },
        },
    },
    "resume_feedback": {
        "type": "function",
        "function": {
            "name": "resume_feedback",
            "description": "이력서 또는 자소서에 대한 상세 피드백을 제공합니다. 사용자가 이력서/자소서를 보여주거나 첨삭을 요청할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "이력서 또는 자소서 내용",
                    },
                    "doc_type": {
                        "type": "string",
                        "enum": ["resume", "cover_letter"],
                        "description": "문서 유형 (이력서 또는 자소서)",
                    },
                },
                "required": ["content"],
            },
        },
    },
    "mock_interview": {
        "type": "function",
        "function": {
            "name": "mock_interview",
            "description": "모의 면접 질문을 생성하고 면접 준비를 도와줍니다. 사용자가 면접 준비를 원할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_title": {
                        "type": "string",
                        "description": "지원 직무 (예: '백엔드 개발자', '마케팅')",
                    },
                    "company_type": {
                        "type": "string",
                        "description": "회사 유형 (예: '스타트업', '대기업')",
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard"],
                        "description": "난이도",
                    },
                },
                "required": ["job_title"],
            },
        },
    },
    "breathing_exercise": {
        "type": "function",
        "function": {
            "name": "breathing_exercise",
            "description": "호흡 운동 가이드를 제공합니다. 사용자가 불안하거나 스트레스를 받을 때, 또는 호흡 운동을 요청할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "technique": {
                        "type": "string",
                        "enum": ["4-7-8", "box"],
                        "description": "호흡법 종류",
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "운동 시간 (분)",
                    },
                },
            },
        },
    },
    "schedule_routine": {
        "type": "function",
        "function": {
            "name": "schedule_routine",
            "description": "취준 루틴이나 일정을 등록합니다. 사용자가 루틴 설정, 일정 관리, 리마인더를 원할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "루틴/일정 제목",
                    },
                    "description": {
                        "type": "string",
                        "description": "상세 설명",
                    },
                    "recurrence": {
                        "type": "string",
                        "enum": ["daily", "weekdays", "weekly"],
                        "description": "반복 주기",
                    },
                    "time": {
                        "type": "string",
                        "description": "시간 (예: '09:00')",
                    },
                },
                "required": ["title"],
            },
        },
    },
    "get_motivation_content": {
        "type": "function",
        "function": {
            "name": "get_motivation_content",
            "description": "동기부여 콘텐츠(영상, 명언)를 추천합니다. 사용자가 힘들어하거나 동기부여가 필요할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "enum": ["depressed", "anxious", "frustrated", "tired", "hopeful"],
                        "description": "현재 기분",
                    },
                    "content_type": {
                        "type": "string",
                        "enum": ["video", "quote", "mixed"],
                        "description": "콘텐츠 유형",
                    },
                },
            },
        },
    },
    "analyze_market": {
        "type": "function",
        "function": {
            "name": "analyze_market",
            "description": "직군별 채용 시장 트렌드를 분석합니다. 사용자가 취업 시장, 트렌드, 전망에 대해 물을 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_field": {
                        "type": "string",
                        "description": "직군 (예: '백엔드 개발', '데이터 분석', '마케팅')",
                    },
                    "region": {
                        "type": "string",
                        "description": "지역 (예: '서울', '판교')",
                    },
                },
                "required": ["job_field"],
            },
        },
    },
    "get_my_applications": {
        "type": "function",
        "function": {
            "name": "get_my_applications",
            "description": (
                "사용자가 기록해 둔 지원 현황을 조회합니다. "
                "'내 지원 어떻게 돼가', '마감 임박한 거 뭐 있어' 처럼 "
                "본인의 지원 상황을 물을 때 사용합니다. "
                "추측하지 말고 이 도구로 확인한 내용만 말하세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": STATUS_KEYS,
                        "description": (
                            "상태로 좁히기. applied=지원완료, doc_passed=서류통과, "
                            "interview=면접, offer=최종합격, rejected=탈락"
                        ),
                    },
                    "only_urgent": {
                        "type": "boolean",
                        "description": "마감 3일 이내 진행 중인 건만",
                    },
                    "query": {"type": "string", "description": "회사명·포지션 검색어"},
                    "limit": {"type": "integer", "description": "최대 건수 (기본 10)"},
                },
                "required": [],
            },
        },
    },
    "update_application_status": {
        "type": "function",
        "function": {
            "name": "update_application_status",
            "description": (
                "지원 상태를 바꿉니다. '카카오 서류 탈락했어', '네이버 면접 잡혔어' 처럼 "
                "결과나 진행을 알릴 때 사용합니다. "
                "탈락·포기는 어느 단계에서 끝났는지(end_stage)가 반드시 필요합니다. "
                "결과에 ambiguous 가 오면 고르지 말고 사용자에게 되물으세요."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": STATUS_KEYS,
                        "description": "바꿀 상태",
                    },
                    "title_query": {
                        "type": "string",
                        "description": "어느 지원인지 회사명 등으로 지목 (예: '카카오')",
                    },
                    "application_id": {"type": "string", "description": "지원 id 를 아는 경우"},
                    "end_stage": {
                        "type": "string",
                        "enum": END_STAGE_KEYS,
                        "description": (
                            "탈락·포기일 때 필수. 어디까지 갔는지. "
                            "document=서류, coding_test=코테, written_test=필기, "
                            "assignment=과제, interview=면접, final=최종"
                        ),
                    },
                    "note": {"type": "string", "description": "한 줄 메모"},
                },
                "required": ["status"],
            },
        },
    },
    "industry_insight": {
        "type": "function",
        "function": {
            "name": "industry_insight",
            "description": "업계 현실과 실무 인사이트를 제공합니다. 사용자가 업계 문화, 실무, 커리어 현실에 대해 물을 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "업종 (예: 'IT', '금융', '마케팅')",
                    },
                    "topic": {
                        "type": "string",
                        "description": "구체적 주제 (예: '연봉', '워라밸', '성장')",
                    },
                },
                "required": ["industry"],
            },
        },
    },
    "save_job_preferences": {
        "type": "function",
        "function": {
            "name": "save_job_preferences",
            "description": "사용자의 직무 선호도를 저장합니다. 대화 중 사용자가 관심 직무, 희망 근무지, 경력 수준 등을 언급하면 자동으로 저장합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_field": {
                        "type": "string",
                        "description": "관심 직무 (예: '백엔드 개발', '데이터 분석', '마케팅')",
                    },
                    "location": {
                        "type": "string",
                        "description": "희망 근무지 (예: '서울', '경기', '판교')",
                    },
                    "career_level": {
                        "type": "string",
                        "enum": ["신입", "경력 1-3년", "경력 3-5년", "무관"],
                        "description": "경력 수준",
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "관심 키워드 (예: ['Python', 'FastAPI', '스타트업'])",
                    },
                    "salary_min": {
                        "type": "integer",
                        "description": "희망 최소 연봉 (만원 단위)",
                    },
                    "company_size": {
                        "type": "string",
                        "enum": ["스타트업", "중소기업", "중견기업", "대기업", "무관"],
                        "description": "희망 회사 규모",
                    },
                },
            },
        },
    },
}


def get_tools_for_agent(tool_names: list[str]) -> list[dict]:
    """에이전트가 사용할 Tool 스키마만 필터링하여 반환."""
    return [TOOL_SCHEMAS[name] for name in tool_names if name in TOOL_SCHEMAS]
