import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";
import type {
  BugSummary,
  AnalysisResponse,
  Action,
  AIModelConfig,
} from "../types";
import { TriageStatus } from "../types";
import * as api from "../api/client";

interface AppState {
  bugs: BugSummary[];
  triageStatuses: Map<number, TriageStatus>;
  selectedBugId: number | null;
  analyses: Map<number, AnalysisResponse>;
  editedActions: Map<number, Action[]>;
  aiModel: AIModelConfig | null;
}

interface AppContextValue extends AppState {
  loadBugs: () => Promise<void>;
  refreshBugs: () => Promise<void>;
  selectBug: (id: number | null) => void;
  analyzeBug: (id: number) => Promise<void>;
  applyActions: (id: number, actions: Action[]) => Promise<void>;
  setAIModel: (model: string) => void;
  editActions: (bugId: number, actions: Action[]) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [bugs, setBugs] = useState<BugSummary[]>([]);
  const [triageStatuses, setTriageStatuses] = useState<Map<number, TriageStatus>>(
    new Map(),
  );
  const [selectedBugId, setSelectedBugId] = useState<number | null>(null);
  const [analyses, setAnalyses] = useState<Map<number, AnalysisResponse>>(
    new Map(),
  );
  const [editedActions, setEditedActions] = useState<Map<number, Action[]>>(
    new Map(),
  );
  const [aiModel, setAIModelState] = useState<AIModelConfig | null>(null);

  const loadBugs = useCallback(async () => {
    const data = await api.fetchBugs();
    setBugs(data);
    const statuses = new Map<number, TriageStatus>();
    data.forEach((bug) => statuses.set(bug.id, TriageStatus.NOT_STARTED));
    setTriageStatuses(statuses);
  }, []);

  const refreshBugs = useCallback(async () => {
    const data = await api.fetchBugs();
    setBugs(data);
  }, []);

  const selectBug = useCallback((id: number | null) => {
    setSelectedBugId(id);
  }, []);

  const analyzeBug = useCallback(async (id: number) => {
    setTriageStatuses((prev) => {
      const next = new Map(prev);
      next.set(id, TriageStatus.ANALYZING);
      return next;
    });
    try {
      const result = await api.analyzeBug(id);
      setAnalyses((prev) => {
        const next = new Map(prev);
        next.set(id, result);
        return next;
      });
      setTriageStatuses((prev) => {
        const next = new Map(prev);
        next.set(id, TriageStatus.READY);
        return next;
      });
    } catch (e) {
      setTriageStatuses((prev) => {
        const next = new Map(prev);
        next.set(id, TriageStatus.ERROR);
        return next;
      });
      throw e;
    }
  }, []);

  const applyActions = useCallback(async (id: number, actions: Action[]) => {
    try {
      await api.applyActions(id, actions);
      setTriageStatuses((prev) => {
        const next = new Map(prev);
        next.set(id, TriageStatus.APPLIED);
        return next;
      });
    } catch (e) {
      setTriageStatuses((prev) => {
        const next = new Map(prev);
        next.set(id, TriageStatus.ERROR);
        return next;
      });
      throw e;
    }
  }, []);

  const setAIModel = useCallback(async (model: string) => {
    await api.setAIModel(model);
    setAIModelState((prev) =>
      prev ? { ...prev, model } : null,
    );
  }, []);

  const editActions = useCallback((bugId: number, actions: Action[]) => {
    setEditedActions((prev) => {
      const next = new Map(prev);
      next.set(bugId, actions);
      return next;
    });
  }, []);

  useEffect(() => {
    api.getAIModel().then(setAIModelState).catch(() => {});
  }, []);

  const value: AppContextValue = {
    bugs,
    triageStatuses,
    selectedBugId,
    analyses,
    editedActions,
    aiModel,
    loadBugs,
    refreshBugs,
    selectBug,
    analyzeBug,
    applyActions,
    setAIModel,
    editActions,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppContext(): AppContextValue {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useAppContext must be used within an AppProvider");
  }
  return context;
}
