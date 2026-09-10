// 지원 트래커 타입 — backend/app/models/application.py 의 라벨 dict 를 미러한다. 키가 바뀌면 양쪽을 함께 고칠 것.

export type ApplicationStatus =
  | "discovered" | "reviewing" | "applied" | "doc_passed" | "coding_test" | "assignment" | "interview"
  | "offer" | "rejected" | "withdrawn" | "no_response" | "not_applied";

export const STATUS_LABELS: Record<ApplicationStatus, string> = {
  discovered: "발견", reviewing: "검토중", applied: "지원완료", doc_passed: "서류통과",
  coding_test: "코테·필기", assignment: "과제", interview: "면접", offer: "최종합격",
  rejected: "탈락", withdrawn: "포기", no_response: "무응답", not_applied: "미지원",
};

/** 🔥 진행중 보드 컬럼 순서 */
export const ACTIVE_STATUSES: readonly ApplicationStatus[] = [
  "discovered", "reviewing", "applied", "doc_passed", "coding_test", "assignment", "interview",
];
export const CLOSED_STATUSES: readonly ApplicationStatus[] = ["offer", "rejected", "withdrawn", "no_response", "not_applied"];
export const CLOSED_WITH_STAGE: readonly ApplicationStatus[] = ["rejected", "withdrawn"];

export const STATUS_COLORS: Record<ApplicationStatus, string> = {
  discovered: "#8a94a6", reviewing: "#8a94a6", applied: "#5b9bd5", doc_passed: "#6dae8a",
  coding_test: "#e5c07b", assignment: "#e5c07b", interview: "#f2a66d", offer: "#e06c75",
  rejected: "#6b7280", withdrawn: "#8b6f5a", no_response: "#c98fb8", not_applied: "#6b7280",
};

export type EndStage = "document" | "coding_test" | "written_test" | "assignment" | "interview" | "final";
export const END_STAGE_LABELS: Record<EndStage, string> = {
  document: "서류", coding_test: "코테", written_test: "필기", assignment: "과제", interview: "면접", final: "최종",
};

export type EmploymentType = "full_time" | "contract" | "intern_conversion" | "intern_experience" | "bootcamp";
export const EMPLOYMENT_LABELS: Record<EmploymentType, string> = {
  full_time: "정규직", contract: "계약직", intern_conversion: "채용연계형 인턴",
  intern_experience: "체험형 인턴", bootcamp: "부트캠프/교육",
};

export type HiringType = "open_recruitment" | "rolling" | "always_open";
export const HIRING_LABELS: Record<HiringType, string> = { open_recruitment: "공채", rolling: "수시", always_open: "상시" };

export interface CompanyRef { id: string; name: string }
export interface Company extends CompanyRef {
  industry: string | null; size: string | null; website: string | null; memo: string | null; application_count: number;
}
export interface Track { id: string; name: string; color: string | null; sort_order: number }
export type DocType = "resume" | "cover_letter" | "portfolio" | "experience" | "other";
/** 자소서를 빼고 이력서·포트폴리오·경험기술서를 함께 받는 전형이 늘어 종류를 넓혔다 */
export const DOC_TYPE_LABELS: Record<DocType, string> = {
  resume: "이력서", cover_letter: "자기소개서", portfolio: "포트폴리오",
  experience: "경험기술서", other: "기타",
};
export interface DocumentRef { id: string; title: string; doc_type: DocType; doc_type_label?: string | null }
export interface DocumentItem extends DocumentRef { created_at: string; updated_at: string }
/** 지원에 붙일 제출물 — id 나 title 중 하나 */
export interface DocumentInput { id?: string; title?: string; doc_type?: DocType }

export interface Application {
  id: string;
  title: string;
  position: string;
  posting_url: string | null;
  status: ApplicationStatus;
  status_label: string;
  end_stage: EndStage | null;
  end_stage_label: string | null;
  employment_type: EmploymentType | null;
  employment_label: string | null;
  hiring_type: HiringType | null;
  hiring_label: string | null;
  discovered_at: string | null;   // YYYY-MM-DD
  applied_at: string | null;
  deadline_at: string | null;
  next_event_at: string | null;   // ISO datetime
  next_action: string | null;
  retrospective: string | null;
  created_at: string;
  updated_at: string;
  d_day: number | null;
  season: string | null;
  is_active: boolean;
  is_applied: boolean;
  passed_docs: boolean;
  reached_interview: boolean;
  company: CompanyRef;
  track: Track | null;
  documents: DocumentRef[];
  resume_document: DocumentRef | null;   // documents 중 이력서 종류의 첫 번째(파생)
}

export interface HistoryEntry {
  id: string; from_status: ApplicationStatus | null; to_status: ApplicationStatus;
  changed_at: string; note: string | null; source: "user" | "agent" | "import";
}
export interface ApplicationDetail extends Application { history: HistoryEntry[] }

export interface ApplicationInput {
  company_id?: string; company_name?: string;
  track_id?: string; track_name?: string; clear_track?: boolean;
  resume_document_id?: string; resume_document_title?: string; clear_resume_document?: boolean;
  documents?: DocumentInput[]; clear_documents?: boolean;   // documents 를 주면 제출물 집합 전체를 대체
  position?: string; title?: string; posting_url?: string | null;
  status?: ApplicationStatus; end_stage?: EndStage | null;
  employment_type?: EmploymentType | null; hiring_type?: HiringType | null;
  discovered_at?: string | null; applied_at?: string | null; deadline_at?: string | null;
  next_event_at?: string | null; next_action?: string | null; retrospective?: string | null;
}

export interface Stats {
  by_status: Partial<Record<ApplicationStatus, number>>;
  by_season: { season: string; total: number; applied: number; passed_docs: number; interview: number; offer: number }[];
  by_track: { track_id: string | null; track_name: string; total: number; applied: number; passed_docs: number; interview: number; offer: number }[];
  by_document: { document_id: string; title: string; doc_type: DocType; doc_type_label: string; total: number; applied: number; passed_docs: number; interview: number; offer: number }[];
  funnel: { applied: number; passed_docs: number; interview: number; offer: number };
  active_count: number;
  total: number;
}

export interface ImportReport {
  dry_run: boolean; total_rows: number; created: number; updated: number; skipped: number;
  errors: { row: number; field: string | null; reason: string; raw: string | null }[];
  preview: Record<string, unknown>[];
}

/** 프런트에서도 D-day 를 다시 계산한다 — 자정을 넘기면 서버 값이 낡는다 */
export function dDay(deadline: string | null): number | null {
  if (!deadline) return null;
  const [y, m, d] = deadline.split("-").map(Number);
  if (!y || !m || !d) return null;
  const today = new Date();
  const a = Date.UTC(y, m - 1, d);
  const b = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
  return Math.round((a - b) / 86400000);
}

export function ddayLabel(n: number | null): string {
  if (n === null) return "";
  if (n === 0) return "D-Day";
  return n > 0 ? `D-${n}` : `D+${-n}`;
}
