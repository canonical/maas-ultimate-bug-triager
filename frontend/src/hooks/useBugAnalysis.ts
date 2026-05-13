import { useState, useEffect, useCallback, useRef } from "react";
import { useAppContext } from "../context/AppContext";
import * as api from "../api/client";
import type { BugDetail, AnalysisResponse, Action } from "../types";

export function useBugAnalysis(bugId: number | null) {
  const {
    analyses,
    editedActions,
    editActions,
    analyzeBug: contextAnalyzeBug,
    applyActions: contextApplyActions,
    refreshBugs,
  } = useAppContext();

  const [bugDetail, setBugDetail] = useState<BugDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analysesRef = useRef(analyses);
  analysesRef.current = analyses;

  const analysis: AnalysisResponse | null = bugId
    ? analyses.get(bugId) ?? null
    : null;

  const currentEditedActions: Action[] = bugId
    ? editedActions.get(bugId) ?? []
    : [];

  useEffect(() => {
    if (bugId === null) {
      setBugDetail(null);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        const detail = await api.fetchBugDetail(bugId);
        if (cancelled) return;
        setBugDetail(detail);
      } catch {
        if (!cancelled) {
          setError("Failed to load bug details");
        }
        return;
      }

      if (!analysesRef.current.has(bugId)) {
        try {
          await contextAnalyzeBug(bugId);
        } catch {
          if (!cancelled) {
            setError("Failed to analyze bug");
          }
        }
      }

      if (!cancelled) {
        setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [bugId, contextAnalyzeBug]);

  useEffect(() => {
    if (analysis && bugId && !editedActions.has(bugId)) {
      editActions(bugId, [...analysis.suggested_actions]);
    }
  }, [analysis, bugId, editedActions, editActions]);

  const editAction = useCallback(
    (index: number, updatedAction: Action) => {
      if (bugId === null) return;
      const updated = [...currentEditedActions];
      updated[index] = updatedAction;
      editActions(bugId, updated);
    },
    [bugId, currentEditedActions, editActions],
  );

  const removeAction = useCallback(
    (index: number) => {
      if (bugId === null) return;
      const updated = currentEditedActions.filter((_, i) => i !== index);
      editActions(bugId, updated);
    },
    [bugId, currentEditedActions, editActions],
  );

  const addAction = useCallback(
    (action: Action) => {
      if (bugId === null) return;
      editActions(bugId, [...currentEditedActions, action]);
    },
    [bugId, currentEditedActions, editActions],
  );

  const applyActions = useCallback(async () => {
    if (bugId === null) return;
    await contextApplyActions(bugId, currentEditedActions);
    try {
      await refreshBugs();
    } catch {
      // Ignore refresh failure after successful apply
    }
  }, [bugId, currentEditedActions, contextApplyActions, refreshBugs]);

  return {
    bugDetail,
    analysis,
    editedActions: currentEditedActions,
    loading,
    error,
    editAction,
    removeAction,
    addAction,
    applyActions,
  };
}
