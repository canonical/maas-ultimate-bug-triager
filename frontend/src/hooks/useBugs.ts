import { useState, useEffect, useCallback } from "react";
import { useAppContext } from "../context/AppContext";
import { TriageStatus } from "../types";
import type { Action } from "../types";

export function useBugs() {
  const {
    bugs,
    triageStatuses,
    loadBugs: contextLoadBugs,
    refreshBugs: contextRefreshBugs,
    analyzeBug: contextAnalyzeBug,
    applyActions: contextApplyActions,
  } = useAppContext();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBugs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await contextLoadBugs();
    } catch {
      setError("Failed to load bugs");
    } finally {
      setLoading(false);
    }
  }, [contextLoadBugs]);

  const analyzeBug = useCallback(
    async (id: number) => {
      try {
        await contextAnalyzeBug(id);
      } catch {
        // Error already reflected in triage status
      }
    },
    [contextAnalyzeBug],
  );

  const analyzeAll = useCallback(async () => {
    const notStarted = bugs.filter(
      (b) =>
        triageStatuses.get(b.id) === TriageStatus.NOT_STARTED ||
        !triageStatuses.has(b.id),
    );
    for (const bug of notStarted) {
      try {
        await contextAnalyzeBug(bug.id);
      } catch {
        // Continue with remaining bugs
      }
    }
  }, [bugs, triageStatuses, contextAnalyzeBug]);

  const applyActions = useCallback(
    async (id: number, actions: Action[]) => {
      await contextApplyActions(id, actions);
      await contextRefreshBugs();
    },
    [contextApplyActions, contextRefreshBugs],
  );

  useEffect(() => {
    loadBugs();
  }, [loadBugs]);

  return {
    bugs,
    triageStatuses,
    loading,
    error,
    loadBugs,
    analyzeBug,
    analyzeAll,
    applyActions,
  };
}
