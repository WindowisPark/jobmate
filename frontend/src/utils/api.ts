import { toast } from "@/stores/toastStore";
import { API_BASE_URL } from "./constants";

const FETCH_TIMEOUT = 15_000; // 15 seconds

let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (isRefreshing && refreshPromise) return refreshPromise;

  isRefreshing = true;
  refreshPromise = fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    credentials: "include",
  })
    .then((r) => r.ok)
    .finally(() => {
      isRefreshing = false;
      refreshPromise = null;
    });

  return refreshPromise;
}

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      ...options,
      signal: controller.signal,
    });
  } catch (err: any) {
    if (err.name === "AbortError") {
      toast.error("요청 시간이 초과되었습니다");
      throw new Error("요청 시간이 초과되었습니다");
    }
    toast.error("서버에 연결할 수 없습니다");
    throw new Error("서버에 연결할 수 없습니다");
  } finally {
    clearTimeout(timer);
  }

  // 401이면 refresh 시도 후 재요청
  if (response.status === 401 && !path.includes("/auth/")) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      const retryResponse = await fetch(`${API_BASE_URL}${path}`, {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...options?.headers,
        },
        ...options,
      });
      if (retryResponse.ok) {
        return retryResponse.json() as Promise<T>;
      }
    }
    // refresh도 실패 → 로그인 페이지로
    window.location.href = "/login";
    throw new Error("인증이 만료되었습니다");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = body.detail || `API Error: ${response.status}`;
    toast.error(message);
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => fetchApi<T>(path),
  post: <T>(path: string, body?: unknown) =>
    fetchApi<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  patch: <T>(path: string, body: unknown) =>
    fetchApi<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => fetchApi<T>(path, { method: "DELETE" }),
};
