// 지원 트래커 스토어 — 목록은 한 번에 받아(≤200) 5개 뷰를 클라이언트에서 그룹핑한다.
import { create } from "zustand";
import { api } from "@/utils/api";
import { toast } from "@/stores/toastStore";
import {
  ACTIVE_STATUSES, dDay,
  type Application, type ApplicationDetail, type ApplicationInput, type ApplicationStatus,
  type Company, type DocumentItem, type EndStage, type ImportReport, type Stats, type Track,
} from "@/types/application";

export type TrackerView = "board" | "calendar" | "season" | "track" | "table";

interface ApplicationState {
  items: Application[];
  byId: Record<string, Application>;
  companies: Company[];
  tracks: Track[];
  documents: DocumentItem[];
  stats: Stats | null;
  view: TrackerView;
  loading: boolean;
  loaded: boolean;
  error: string | null;

  setView: (v: TrackerView) => void;
  fetchAll: () => Promise<void>;
  fetchRefs: () => Promise<void>;
  fetchStats: () => Promise<void>;
  fetchDetail: (id: string) => Promise<ApplicationDetail>;
  create: (input: ApplicationInput) => Promise<Application>;
  update: (id: string, patch: ApplicationInput) => Promise<Application>;
  changeStatus: (id: string, status: ApplicationStatus, endStage?: EndStage | null, note?: string) => Promise<{ celebration: boolean }>;
  remove: (id: string) => Promise<void>;
  importCsv: (file: File, opts: { dryRun: boolean; onDuplicate: "skip" | "update" }) => Promise<ImportReport>;
}

const index = (items: Application[]) => Object.fromEntries(items.map((a) => [a.id, a]));

export const useApplicationStore = create<ApplicationState>((set, get) => ({
  items: [],
  byId: {},
  companies: [],
  tracks: [],
  documents: [],
  stats: null,
  view: "board",
  loading: false,
  loaded: false,
  error: null,

  setView: (view) => set({ view }),

  fetchAll: async () => {
    set({ loading: true, error: null });
    try {
      const res = await api.get<{ items: Application[]; total: number }>("/applications?limit=200&sort=deadline_at");
      set({ items: res.items, byId: index(res.items), loading: false, loaded: true });
    } catch (e: any) {
      set({ loading: false, error: e.message ?? "불러오기 실패" });
    }
  },

  fetchRefs: async () => {
    const [companies, tracks, documents] = await Promise.all([
      api.get<Company[]>("/companies"), api.get<Track[]>("/tracks"), api.get<DocumentItem[]>("/documents"),
    ]);
    set({ companies, tracks, documents });
  },

  fetchStats: async () => set({ stats: await api.get<Stats>("/applications/stats") }),

  fetchDetail: (id) => api.get<ApplicationDetail>(`/applications/${id}`),

  create: async (input) => {
    const created = await api.post<Application>("/applications", input);
    set((s) => {
      const items = [...s.items, created];
      return { items, byId: index(items) };
    });
    void get().fetchRefs();
    return created;
  },

  update: async (id, patch) => {
    const updated = await api.patch<Application>(`/applications/${id}`, patch);
    set((s) => {
      const items = s.items.map((a) => (a.id === id ? updated : a));
      return { items, byId: index(items) };
    });
    return updated;
  },

  changeStatus: async (id, status, endStage, note) => {
    // 낙관적 업데이트 → 실패 시 롤백
    const prev = get().byId[id];
    if (prev) {
      const optimistic: Application = { ...prev, status, is_active: ACTIVE_STATUSES.includes(status) };
      set((s) => {
        const items = s.items.map((a) => (a.id === id ? optimistic : a));
        return { items, byId: index(items) };
      });
    }
    try {
      const res = await api.patch<{ application: Application; celebration: boolean }>(`/applications/${id}/status`, {
        status, end_stage: endStage ?? null, note: note || null,
      });
      set((s) => {
        const items = s.items.map((a) => (a.id === id ? res.application : a));
        return { items, byId: index(items) };
      });
      return { celebration: res.celebration };
    } catch (e) {
      if (prev) {
        set((s) => {
          const items = s.items.map((a) => (a.id === id ? prev : a));
          return { items, byId: index(items) };
        });
      }
      throw e;
    }
  },

  remove: async (id) => {
    await api.delete(`/applications/${id}`);
    set((s) => {
      const items = s.items.filter((a) => a.id !== id);
      return { items, byId: index(items) };
    });
    toast.success("지원 내역을 지웠어요");
  },

  importCsv: async (file, { dryRun, onDuplicate }) => {
    const fd = new FormData();
    fd.append("file", file);
    const report = await api.upload<ImportReport>(
      `/applications/import/notion-csv?dry_run=${dryRun}&on_duplicate=${onDuplicate}`, fd,
    );
    if (!dryRun) await Promise.all([get().fetchAll(), get().fetchRefs()]);
    return report;
  },
}));

// ---------------------------------------------------------------- 셀렉터(순수)
const byDeadline = (a: Application, b: Application) => {
  if (!a.deadline_at && !b.deadline_at) return 0;
  if (!a.deadline_at) return 1;
  if (!b.deadline_at) return -1;
  return a.deadline_at.localeCompare(b.deadline_at);
};

export function selectBoardColumns(items: Application[]): { status: ApplicationStatus; items: Application[] }[] {
  return ACTIVE_STATUSES.map((status) => ({
    status, items: items.filter((a) => a.status === status).sort(byDeadline),
  }));
}

export interface CalendarEvent { date: string; kind: "deadline" | "event"; app: Application }
export function selectCalendarEvents(items: Application[]): Record<string, CalendarEvent[]> {
  const out: Record<string, CalendarEvent[]> = {};
  const push = (date: string, ev: CalendarEvent) => ((out[date] ??= []).push(ev));
  for (const a of items) {
    if (a.deadline_at) push(a.deadline_at, { date: a.deadline_at, kind: "deadline", app: a });
    if (a.next_event_at) {
      const d = a.next_event_at.slice(0, 10);
      push(d, { date: d, kind: "event", app: a });
    }
  }
  return out;
}

export interface GroupStat { key: string; label: string; items: Application[]; applied: number; passed_docs: number; interview: number; offer: number }
function funnel(items: Application[]) {
  return {
    applied: items.filter((a) => a.is_applied).length,
    passed_docs: items.filter((a) => a.passed_docs).length,
    interview: items.filter((a) => a.reached_interview).length,
    offer: items.filter((a) => a.status === "offer").length,
  };
}
export function groupBySeason(items: Application[]): GroupStat[] {
  const groups = new Map<string, Application[]>();
  for (const a of items) (groups.get(a.season ?? "미정") ?? groups.set(a.season ?? "미정", []).get(a.season ?? "미정"))!.push(a);
  return [...groups.entries()]
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([key, list]) => ({ key, label: key, items: list.sort(byDeadline).reverse(), ...funnel(list) }));
}
export function groupByTrack(items: Application[]): GroupStat[] {
  const groups = new Map<string, { label: string; items: Application[] }>();
  for (const a of items) {
    const key = a.track?.id ?? "none";
    const g = groups.get(key) ?? { label: a.track?.name ?? "트랙 없음", items: [] };
    g.items.push(a);
    groups.set(key, g);
  }
  return [...groups.entries()]
    .sort(([, a], [, b]) => b.items.length - a.items.length)
    .map(([key, g]) => ({ key, label: g.label, items: g.items.sort(byDeadline).reverse(), ...funnel(g.items) }));
}

/** 방이 반응할 신호 — 마감 3일 이내 진행 건이 있으면 책상 점등 */
export function selectUrgent(items: Application[]): Application[] {
  return items.filter((a) => {
    if (!a.is_active) return false;
    const d = dDay(a.deadline_at);
    return d !== null && d >= 0 && d <= 3;
  });
}
