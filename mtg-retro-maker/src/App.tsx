import { useState } from "react";
import { JsonMultiSection } from "./components/Controls/JsonSection";
import { CanvasPreview } from "./components/CanvasPreview";
import { useStaticAssets } from "./hooks/useStaticAssets";
import { normalizeRarity } from "./utils/dataUtils";

function App() {
  // Load static assets on mount
  const { frames, symbols, raritySymbols, fontsLoaded, loading } = useStaticAssets();

  // State
  const [cards, setCards] = useState<Record<string, any>>({});
  const [selectedCardId, setSelectedCardId] = useState<string>("");

  // Derived state for current card
  const currentCard = cards[selectedCardId] || {};
  const color = currentCard.color || "";
  const title = currentCard.title || "";
  const manaCost = currentCard.manaCost || "";
  const typeLine = currentCard.typeLine || "";
  const rarity = currentCard.rarity || "Common";
  const rules = currentCard.rules || "";
  const pt = currentCard.pt || "";

  const [diag, setDiag] = useState<{ tests: any[]; symbolCount: number }>({
    tests: [],
    symbolCount: 0,
  });

  // Art Upload
  const [artImage, setArtImage] = useState<HTMLImageElement | null>(null);

  const handleArtUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        const img = new Image();
        img.onload = () => setArtImage(img);
        img.src = evt.target?.result as string;
      };
      reader.readAsDataURL(file);
    }
  };

  // Select frame based on rarity or color
  const getFrame = () => {
    // 1. Color-based frame selection
    if (color) {
      const c = color.toLowerCase();
      if (c === "white" && frames.white) return frames.white;
      if (c === "artifact" && frames.artifact) return frames.artifact;
      if (c === "land" && frames.land) return frames.land;
    }

    // 2. Fallback to Rarity-based selection (legacy behavior)
    const r = normalizeRarity(rarity);
    if (r === "Mythic") return frames.mythic;
    if (r === "Rare") return frames.rare;
    if (r === "Uncommon") return frames.uncommon;
    return frames.common;
  };

  const activeFrame = getFrame();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900 text-white">
        <div className="text-xl">Loading assets...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8 font-sans">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Controls */}
        <div className="lg:col-span-4 space-y-8">
          <div className="bg-gray-800 p-6 rounded-xl shadow-lg border border-gray-700">
            <h1 className="text-2xl font-bold mb-6 text-purple-400">
              MTG Retro Maker
            </h1>

            {/* JSON Upload & Card Selection */}
            <JsonMultiSection
              applyPrefillFromObject={(obj) => {
                setCards(obj);
                const keys = Object.keys(obj);
                if (keys.length > 0) setSelectedCardId(keys[0]);
                return keys.length;
              }}
            />

            {/* Card Selector */}
            {Object.keys(cards).length > 0 && (
              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Select Card
                </label>
                <select
                  className="w-full bg-gray-900 border border-gray-600 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-purple-500 outline-none"
                  value={selectedCardId}
                  onChange={(e) => setSelectedCardId(e.target.value)}
                >
                  {Object.keys(cards).map((key) => (
                    <option key={key} value={key}>
                      {key}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Art Upload */}
            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Upload Art
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={handleArtUpload}
                className="block w-full text-sm text-gray-400
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-full file:border-0
                  file:text-sm file:font-semibold
                  file:bg-purple-600 file:text-white
                  hover:file:bg-purple-700
                  cursor-pointer"
              />
            </div>

            {/* Global Options removed per request */}
          </div>
        </div>

        {/* Right Preview */}
        <div className="lg:col-span-8">
          <CanvasPreview
            artSource={artImage}
            frameSource={activeFrame}
            frameCommonSource={frames.common}
            frameUncommonSource={frames.uncommon}
            frameRareSource={frames.rare}
            frameMythicSource={frames.mythic}

            symbolImgs={symbols}
            raritySymbols={raritySymbols}
            title={title}
            manaCost={manaCost}
            typeLine={typeLine}
            rules={rules}
            pt={pt}
            rarity={rarity}
            diag={diag}
            setDiag={setDiag}
            fontVersion={fontsLoaded ? 1 : 0}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
