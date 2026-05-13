import axios from "axios";
import type {
  BugSummary,
  BugDetail,
  AnalysisResponse,
  Action,
  ApplyActionsResponse,
  AIModelConfig,
} from "../types";

const api = axios.create({
  baseURL: "/api",
});

export async function fetchBugs(): Promise<BugSummary[]> {
  const response = await api.get<BugSummary[]>("/bugs");
  return response.data;
}

export async function fetchBugDetail(bugId: number): Promise<BugDetail> {
  const response = await api.get<BugDetail>(`/bugs/${bugId}`);
  return response.data;
}

export async function analyzeBug(bugId: number): Promise<AnalysisResponse> {
  const response = await api.post<AnalysisResponse>(`/bugs/${bugId}/analyze`);
  return response.data;
}

export async function applyActions(
  bugId: number,
  actions: Action[],
): Promise<ApplyActionsResponse> {
  const response = await api.post<ApplyActionsResponse>(
    `/bugs/${bugId}/actions`,
    { actions },
  );
  return response.data;
}

export async function getAIModel(): Promise<AIModelConfig> {
  const response = await api.get<AIModelConfig>("/config/ai-model");
  return response.data;
}

export async function setAIModel(model: string): Promise<void> {
  await api.put("/config/ai-model", { model });
}

/**
 * Stream bug reproduction logs via Server-Sent Events.
 * Returns an EventSource that the caller is responsible for closing.
 */
export function streamReproduction(
  bugId: number,
  maasIp: string,
  onMessage: (text: string) => void,
  onError: (error: Event) => void,
  onComplete: () => void,
): EventSource {
  const es = new EventSource(`/api/bugs/${bugId}/reproduce?maas_ip=${encodeURIComponent(maasIp)}`);
  es.onmessage = (event) => {
    onMessage(event.data);
  };
  es.onerror = (event) => {
    if (es.readyState === EventSource.CLOSED) {
      onComplete();
    } else {
      onError(event);
    }
    es.close();
  };
  return es;
}
