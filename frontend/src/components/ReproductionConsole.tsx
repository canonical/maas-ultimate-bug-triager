import { useEffect, useRef, useState } from "react";

export interface ReproductionConsoleProps {
  /** Lines of output to display */
  lines: string[];
  /** Whether the stream is still active */
  streaming: boolean;
  /** Whether an error occurred */
  error: string | null;
  /** Callback to dismiss the console */
  onDismiss: () => void;
}

export default function ReproductionConsole({
  lines,
  streaming,
  error,
  onDismiss,
}: ReproductionConsoleProps) {
  const scrollRef = useRef<HTMLPreElement>(null);

  // Auto-scroll to bottom as new lines arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [lines]);

  return (
    <div className="rounded border border-gray-700 bg-gray-950">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-gray-700 px-3 py-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-300">
            Reproduction Console
          </span>
          {streaming && (
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
            </span>
          )}
          {!streaming && !error && lines.length > 0 && (
            <span className="text-xs text-gray-500">completed</span>
          )}
        </div>
        <button
          className="rounded px-2 py-1 text-xs text-gray-400 hover:bg-gray-800 hover:text-white"
          onClick={onDismiss}
        >
          Dismiss
        </button>
      </div>

      {/* Console output */}
      <pre
        ref={scrollRef}
        className="max-h-80 overflow-y-auto p-3 font-mono text-xs leading-5 text-gray-300"
      >
        {lines.length === 0 && streaming && (
          <span className="text-gray-500">Starting reproduction...</span>
        )}
        {lines.map((line, i) => (
          <span key={i}>
            {line}
            {"\n"}
          </span>
        ))}
        {error && (
          <span className="text-red-400">
            {"\n"}Error: {error}
          </span>
        )}
      </pre>
    </div>
  );
}
