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
