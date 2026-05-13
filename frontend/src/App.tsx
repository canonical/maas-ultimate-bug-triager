import { Component, type ReactNode, type ErrorInfo } from "react";
import ModelSelector from "./components/ModelSelector";
import BugList from "./components/BugList";
import BugTriageView from "./components/BugTriageView";
import ToastContainer from "./components/Toast";
import { ToastProvider } from "./hooks/useToast";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, _info: ErrorInfo) {
    console.error("ErrorBoundary caught:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen items-center justify-center bg-gray-900">
          <div className="flex flex-col items-center gap-4 rounded-lg border border-gray-700 bg-gray-800 p-8">
            <h2 className="text-xl font-bold text-red-400">
              Something went wrong
            </h2>
            <p className="max-w-md text-center text-sm text-gray-400">
              {this.state.error?.message ?? "An unexpected error occurred."}
            </p>
            <button
              className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-500"
              onClick={() => window.location.reload()}
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  return (
    <ToastProvider>
      <ErrorBoundary>
        <div className="flex h-screen flex-col bg-gray-900 text-white">
          <header className="flex items-center justify-between border-b border-gray-700 px-6 py-3">
            <h1 className="text-xl font-bold">MAAS Bug Triager</h1>
            <ModelSelector />
          </header>
          <main className="flex flex-1 flex-col overflow-hidden lg:flex-row">
            <div className="h-1/2 overflow-y-auto border-b border-gray-700 p-4 lg:h-auto lg:w-2/5 lg:border-b-0 lg:border-r">
              <BugList />
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              <BugTriageView />
            </div>
          </main>
          <ToastContainer />
        </div>
      </ErrorBoundary>
    </ToastProvider>
  );
}
