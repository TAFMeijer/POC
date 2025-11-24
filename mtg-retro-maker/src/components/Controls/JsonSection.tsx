import { useState, type ChangeEvent } from "react";

interface JsonMultiSectionProps {
    applyPrefillFromObject: (obj: any) => number;
}

export function JsonMultiSection({ applyPrefillFromObject }: JsonMultiSectionProps) {
    const [jsonStatus, setJsonStatus] = useState<string | null>(null);
    const [jsonError, setJsonError] = useState<string | null>(null);

    const handleMultiJsonUpload = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (evt) => {
            try {
                const text = (evt.target?.result as string) || "";
                const parsed = JSON.parse(text);

                // Validate structure: should be an object where values are cards
                if (typeof parsed !== "object" || parsed === null) {
                    throw new Error("JSON must be an object");
                }
                const count = applyPrefillFromObject(parsed);
                setJsonStatus(`Loaded ${count} cards successfully.`);
                setJsonError(null);
            } catch (err) {
                console.error(err);
                setJsonStatus(null);
                setJsonError("Invalid JSON file.");
            }
        };
        reader.readAsText(file);
    };

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-300">Upload Card Data</h3>
            <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
                <label className="block text-sm font-medium text-gray-400 mb-2">
                    Select JSON File
                </label>
                <input
                    type="file"
                    accept=".json"
                    onChange={handleMultiJsonUpload}
                    className="block w-full text-sm text-gray-400
                        file:mr-4 file:py-2 file:px-4
                        file:rounded-full file:border-0
                        file:text-sm file:font-semibold
                        file:bg-purple-600 file:text-white
                        hover:file:bg-purple-700
                        cursor-pointer"
                />
                {jsonStatus && (
                    <p className="mt-2 text-sm text-green-400">{jsonStatus}</p>
                )}
                {jsonError && (
                    <p className="mt-2 text-sm text-red-400">{jsonError}</p>
                )}
            </div>
        </div>
    );
}
