import { request } from "../request";

export interface AuditEntry {
  id: string;
  timestamp: number;
  actor: string;
  action: string;
  target: string;
  summary: string;
  result: string;
  detail: Record<string, unknown> | null;
}

export interface AuditListResponse {
  entries: AuditEntry[];
  total: number;
  limit: number;
  offset: number;
}

export const auditApi = {
  listAuditEntries: (params?: {
    action?: string;
    actor?: string;
    limit?: number;
    offset?: number;
  }): Promise<AuditListResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.action) searchParams.set("action", params.action);
    if (params?.actor) searchParams.set("actor", params.actor);
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.offset) searchParams.set("offset", String(params.offset));
    const qs = searchParams.toString();
    return request<AuditListResponse>(`/audit${qs ? `?${qs}` : ""}`);
  },

  listAuditActions: (): Promise<{ actions: string[] }> =>
    request<{ actions: string[] }>("/audit/actions"),
};
