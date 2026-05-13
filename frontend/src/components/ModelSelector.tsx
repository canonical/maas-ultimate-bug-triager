import { useAppContext } from "../context/AppContext";

export default function ModelSelector() {
  const { aiModel, setAIModel } = useAppContext();

  if (!aiModel) {
    return (
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-400">Model:</label>
        <span className="text-sm text-gray-500">Loading...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <label className="text-sm text-gray-400" htmlFor="model-select">
        Model:
      </label>
      <select
        id="model-select"
        value={aiModel.model}
        onChange={(e) => setAIModel(e.target.value)}
        className="rounded border border-gray-600 bg-gray-800 px-2 py-1 text-sm text-white"
      >
        {aiModel.available_models.map((model) => (
          <option key={model} value={model}>
            {model}
          </option>
        ))}
      </select>
    </div>
  );
}
