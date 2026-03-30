from app.tools.search_jobs import search_jobs, save_job_preferences
from app.tools.resume_feedback import resume_feedback
from app.tools.mock_interview import mock_interview
from app.tools.breathing import breathing_exercise
from app.tools.schedule import schedule_routine
from app.tools.motivation import get_motivation_content
from app.tools.market import analyze_market
from app.tools.insight import industry_insight

ALL_TOOLS = {
    "search_jobs": search_jobs,
    "save_job_preferences": save_job_preferences,
    "resume_feedback": resume_feedback,
    "mock_interview": mock_interview,
    "breathing_exercise": breathing_exercise,
    "schedule_routine": schedule_routine,
    "get_motivation_content": get_motivation_content,
    "analyze_market": analyze_market,
    "industry_insight": industry_insight,
}

__all__ = ["ALL_TOOLS"]
