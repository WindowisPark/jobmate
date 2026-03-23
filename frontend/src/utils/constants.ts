export const API_BASE_URL = "/api";
export const WS_BASE_URL = "ws://localhost:8000/ws";

export const OFFICE_TILE_SIZE = 48;
export const OFFICE_COLS = 12;
export const OFFICE_ROWS = 8;

export const TOOL_TO_OFFICE_ACTION: Record<string, Record<string, string>> = {
  search_jobs: { agent: "jun_ho", action: "searching" },
  resume_feedback: { agent: "seo_yeon", action: "reading" },
  mock_interview: { agent: "seo_yeon", action: "talking" },
  breathing_exercise: { agent: "ha_eun", action: "meditating" },
  schedule_routine: { agent: "ha_eun", action: "typing" },
  get_motivation_content: { agent: "min_su", action: "searching" },
  analyze_market: { agent: "jun_ho", action: "reading" },
  industry_insight: { agent: "min_su", action: "thinking" },
};
