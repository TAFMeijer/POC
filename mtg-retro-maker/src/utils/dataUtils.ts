export function normalizeKeys(obj: any) {
    const out: Record<string, any> = {};
    if (!obj || typeof obj !== "object") return out;
    for (const k of Object.keys(obj)) out[String(k).trim().toLowerCase()] = obj[k];
    return out;
}

export function normalizeRarity(r: any) {
    const s = String(r || "").toLowerCase();
    if (!s) return "";
    if (s.includes("myth")) return "Mythic";
    if (s.includes("un") && s.includes("common")) return "Uncommon";
    if (s.includes("rare")) return "Rare";
    if (s.includes("common")) return "Common";
    return r;
}
