from app.tools.applications import get_my_applications, update_application_status
from app.tools.breathing import breathing_exercise
from app.tools.insight import industry_insight
from app.tools.market import analyze_market
from app.tools.mock_interview import mock_interview
from app.tools.motivation import get_motivation_content
from app.tools.resume_feedback import resume_feedback
from app.tools.schedule import schedule_routine
from app.tools.search_jobs import save_job_preferences, search_jobs

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
    "get_my_applications": get_my_applications,
    "update_application_status": update_application_status,
}

__all__ = ["ALL_TOOLS"]
