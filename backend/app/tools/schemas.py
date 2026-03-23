"""OpenAI Function Calling 스키마 정의 — 8개 Tool."""

TOOL_SCHEMAS: dict[str, dict] = {
    "search_jobs": {
        "type": "function",
        "function": {
            "name": "search_jobs",
            "description": "사람인/공공데이터포털에서 채용공고를 검색합니다. 사용자가 채용공고, 일자리, 취업 정보를 원할 때 사용합니다.",
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
}


def get_tools_for_agent(tool_names: list[str]) -> list[dict]:
    """에이전트가 사용할 Tool 스키마만 필터링하여 반환."""
    return [TOOL_SCHEMAS[name] for name in tool_names if name in TOOL_SCHEMAS]
