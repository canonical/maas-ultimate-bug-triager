export interface BugSummary {
  id: number;
  title: string;
  status: string;
  importance: string;
  owner: string;
  date_created: string;
  tags: string[];
}

export interface Comment {
  author: string;
  date: string;
  content: string;
}

export interface Attachment {
  id: number;
  title: string;
  content_type: string;
  size: number;
}

export interface BugDetail extends BugSummary {
  description: string;
  comments: Comment[];
  attachments: Attachment[];
}

export enum ActionType {
  ADD_COMMENT = "ADD_COMMENT",
  SET_STATUS = "SET_STATUS",
  SET_IMPORTANCE = "SET_IMPORTANCE",
  ADD_TAG = "ADD_TAG",
  REMOVE_TAG = "REMOVE_TAG",
}

export interface AddCommentAction {
  type: ActionType.ADD_COMMENT;
  content: string;
}

export interface SetStatusAction {
  type: ActionType.SET_STATUS;
  status: string;
}

export interface SetImportanceAction {
  type: ActionType.SET_IMPORTANCE;
  importance: string;
}

export interface AddTagAction {
  type: ActionType.ADD_TAG;
  tag: string;
}

export interface RemoveTagAction {
  type: ActionType.REMOVE_TAG;
  tag: string;
}

export type Action =
  | AddCommentAction
  | SetStatusAction
  | SetImportanceAction
  | AddTagAction
  | RemoveTagAction;

export interface AnalysisResponse {
  bug_id: number;
  reasoning: string;
  suggested_actions: Action[];
}

export interface ActionsRequest {
  actions: Action[];
}

export interface ApplyActionsResponse {
  bug_id: number;
  applied: number;
  errors: string[];
}

export interface AIModelConfig {
  model: string;
  available_models: string[];
}

export enum TriageStatus {
  NOT_STARTED = "NOT_STARTED",
  ANALYZING = "ANALYZING",
  READY = "READY",
  APPLIED = "APPLIED",
  ERROR = "ERROR",
}
