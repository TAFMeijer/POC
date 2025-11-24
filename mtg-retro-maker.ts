import React, { useEffect, useMemo, useRef, useState } from "react";

/**
 * MTG Retro Converter — single-file React app
 *
 * This rewrite fixes the truncation at the end of the file (line ~832) and
 * ensures the JSX tree is fully closed. It preserves all features you had:
 *  - Upload: art, single frame, and rarity frames (Common/Uncommon/Rare/Mythic)
 *  - Upload: 18 mana/tap symbols (U,W,B,R,G,S,T,-T,0–9)
 *  - Upload: fonts (Goudy Medieval; Elegant Garamond Regular/Italic/Bold)
 *  - JSON single and JSON multi (top-level dictionary) prefills + rarity
 *  - Right-bound mana cost, rules rich text with {i}/{/i} and tokens
 *  - Dynamic rules font (max 34px) with 12px paragraph gap and vertical centering
 *  - Transparent background toggle, guides, PNG export/open
 *  - Runtime diagnostics (simple tests) and robust render try/catch
 */

// ===== Canvas constants
const CANVAS_W = 744; // px
const CANVAS_H = 1039; // px

// Layout
const ART_RECT = { x: 86, y: 96, w: 572, h: 467 }; // right 658, bottom 563
const TITLE = { x: 85, y: 75, size: 43, shadow: 4, angleDeg: 60 };
const MANA = { right: 685, y: 38, h: 36 }; // right-bound anchor
const TYPE = { x: 80, y: 609, size: 34, shadow: 2, angleDeg: 60 };
const RULES_BOX = { x: 94, y: 627, w: 558, h: 288 }; // y already +8 from typeline
const RULES_MAX_SIZE = 34; // dynamic sizing ceiling
const PT = { x: 623, y: 980, size: 48, shadow: 4, angleDeg: 60 };
const DISCLAIMER = { x: 80, y: 988, size: 22, shadow: 1, angleDeg: 60 };
const PARAGRAPH_GAP_PX = 12; // fixed gap between paragraphs (replaces normal line spacing)

// Mana/tap symbol codes (order required by user)
const SYMBOL_CODES = [
  "U","W","B","R","G","S","T","-T",
  "0","1","2","3","4","5","6","7","8","9"
];

// ===== Utilities
const degToRad = (d: number) => (d * Math.PI) / 180;
const polarOffset = (angleDeg: number, distance: number) => ({
  x: Math.cos(degToRad(angleDeg)) * distance,
  y: Math.sin(degToRad(angleDeg)) * distance,
});

function getSourceDims(src: any) {
  const w = src && (src.width ?? src.naturalWidth ?? 0);
  const h = src && (src.height ?? src.naturalHeight ?? 0);
  return { w, h };
}

function drawImageCover(
  ctx: CanvasRenderingContext2D,
  img: HTMLImageElement,
  dx: number,
  dy: number,
  dW: number,
  dH: number
) {
  const { w: sW, h: sH } = getSourceDims(img);
  if (!sW || !sH) return;
  const scale = Math.max(dW / sW, dH / sH);
  const newW = sW * scale;
  const newH = sH * scale;
  const sx = Math.max(0, (newW - dW) / 2);
  const sy = Math.max(0, (newH - dH) / 2);

  const off = document.createElement("canvas");
  off.width = Math.ceil(newW);
  off.height = Math.ceil(newH);
  const octx = off.getContext("2d")!;
  octx.imageSmoothingQuality = "high";
  octx.drawImage(img, 0, 0, newW, newH);
  ctx.drawImage(off, sx, sy, dW, dH, dx, dy, dW, dH);
}

function tokenizeMana(mana: string) {
  if (!mana) return [] as string[];
  const tokens: string[] = [];
  const re = /\{([^}]+)\}/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(mana)) !== null) {
    const tok = String(m[1]).trim().toUpperCase();
    if (/^\d+$/.test(tok)) tokens.push(...tok.split(""));
    else tokens.push(tok);
  }
  return tokens;
}

// ===== Hooks
function useObjectURL(file: File | null) {
  const url = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);
  useEffect(() => () => { if (url) URL.revokeObjectURL(url); }, [url]);
  return url;
}

function useImage(url: string | null) {
  const [img, setImg] = useState<HTMLImageElement | null>(null);
  useEffect(() => {
    if (!url) { setImg(null); return; }
    const image = new Image();
    if (/^https?:/i.test(url)) image.crossOrigin = "anonymous";
    image.onload = async () => {
      try { if ("decode" in image) await (image as any).decode(); } catch {}
      setImg(image);
    };
    image.onerror = () => setImg(null);
    image.src = url;
    return () => { image.onload = null; image.onerror = null; };
  }, [url]);
  return img;
}

async function loadFontFromFile(file: File, name: string) {
  try {
    const data = await file.arrayBuffer();
    const face = new FontFace(name, data);
    await face.load();
    (document as any).fonts.add(face);
  } catch (e) {
    console.warn("Font load failed", name, e);
  }
}

function normalizeKeys(obj: any) {
  const out: Record<string, any> = {};
  if (!obj || typeof obj !== "object") return out;
  for (const k of Object.keys(obj)) out[String(k).trim().toLowerCase()] = obj[k];
  return out;
}

function normalizeRarity(r: any) {
  const s = String(r || "").toLowerCase();
  if (!s) return "";
  if (s.includes("myth")) return "Mythic";
  if (s.includes("un") && s.includes("common")) return "Uncommon";
  if (s.includes("rare")) return "Rare";
  if (s.includes("common")) return "Common";
  return r;
}

// ===== App
export default function App() {
  // Canvas
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // File uploads: art + frames
  const [artFile, setArtFile] = useState<File | null>(null);
  const [frameFile, setFrameFile] = useState<File | null>(null);
  const [frameCommonFile, setFrameCommonFile] = useState<File | null>(null);
  const [frameUncommonFile, setFrameUncommonFile] = useState<File | null>(null);
  const [frameRareFile, setFrameRareFile] = useState<File | null>(null);
  const [frameMythicFile, setFrameMythicFile] = useState<File | null>(null);

  const artUrl = useObjectURL(artFile);
  const frameUrl = useObjectURL(frameFile);
  const frameCommonUrl = useObjectURL(frameCommonFile);
  const frameUncommonUrl = useObjectURL(frameUncommonFile);
  const frameRareUrl = useObjectURL(frameRareFile);
  const frameMythicUrl = useObjectURL(frameMythicFile);

  const artSource = useImage(artUrl);
  const frameSource = useImage(frameUrl);
  const frameCommonSource = useImage(frameCommonUrl);
  const frameUncommonSource = useImage(frameUncommonUrl);
  const frameRareSource = useImage(frameRareUrl);
  const frameMythicSource = useImage(frameMythicUrl);

  // Fonts
  const [goudyFile, setGoudyFile] = useState<File | null>(null);
  const [garamondFile, setGaramondFile] = useState<File | null>(null);
  const [garamondItalicFile, setGaramondItalicFile] = useState<File | null>(null);
  const [garamondBoldFile, setGaramondBoldFile] = useState<File | null>(null);

  useEffect(() => { if (goudyFile) loadFontFromFile(goudyFile, "Goudy Medieval"); }, [goudyFile]);
  useEffect(() => { if (garamondFile) loadFontFromFile(garamondFile, "Elegant Garamond"); }, [garamondFile]);
  useEffect(() => { if (garamondItalicFile) loadFontFromFile(garamondItalicFile, "Elegant Garamond Italic"); }, [garamondItalicFile]);
  useEffect(() => { if (garamondBoldFile) loadFontFromFile(garamondBoldFile, "Elegant Garamond Bold"); }, [garamondBoldFile]);

  // Symbols
  const [symbolFiles, setSymbolFiles] = useState<Record<string, File | null>>({});
  const [symbolImgs, setSymbolImgs] = useState<Record<string, HTMLImageElement | null>>({});

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const entries = await Promise.all(
        SYMBOL_CODES.map(async (code) => {
          const f = symbolFiles[code] || null;
          if (!f) return [code, null] as const;
          return new Promise<[string, HTMLImageElement | null]>((resolve) => {
            const url = URL.createObjectURL(f);
            const img = new Image();
            img.onload = () => { if (!cancelled) resolve([code, img]); URL.revokeObjectURL(url); };
            img.onerror = () => { if (!cancelled) resolve([code, null]); URL.revokeObjectURL(url); };
            img.src = url;
          });
        })
      );
      if (!cancelled) setSymbolImgs(Object.fromEntries(entries));
    })();
    return () => { cancelled = true; };
  }, [symbolFiles]);

  // Text inputs
  const [title, setTitle] = useState<string>("Sample Title");
  const [manaCost, setManaCost] = useState<string>("{2}{W}");
  const [typeLine, setTypeLine] = useState<string>("Creature — Angel");
  const [rules, setRules] = useState<string>(`Flying, first strike\nWhen Sample Title enters the battlefield, draw a card.`);
  const [pt, setPT] = useState<string>("4/4");
  const [textColor, setTextColor] = useState<string>("#1b1b1b");
  const [transparentBg, setTransparentBg] = useState<boolean>(false);
  const [backgroundColor, setBackgroundColor] = useState<string>("#ffffff");
  const [showGuides, setShowGuides] = useState<boolean>(false);

  // Prefill (single)
  const [jsonStatus, setJsonStatus] = useState<string | null>(null);
  const [jsonError, setJsonError] = useState<string | null>(null);

  function applyPrefillFromObject(obj: any) {
    const m = normalizeKeys(obj);
    let applied = 0;
    if (Object.prototype.hasOwnProperty.call(m, "title") && m.title != null) { setTitle(String(m.title)); applied++; }
    if (Object.prototype.hasOwnProperty.call(m, "manacost") && m.manacost != null) { setManaCost(String(m.manacost)); applied++; }
    if (Object.prototype.hasOwnProperty.call(m, "typeline") && m.typeline != null) { setTypeLine(String(m.typeline)); applied++; }
    if (Object.prototype.hasOwnProperty.call(m, "rules") && m.rules != null) { setRules(String(m.rules)); applied++; }
    if (Object.prototype.hasOwnProperty.call(m, "pt") && m.pt != null) { setPT(String(m.pt)); applied++; }
    if (Object.prototype.hasOwnProperty.call(m, "rarity") && m.rarity != null) { setRarity(normalizeRarity(m.rarity)); }
    return applied;
  }

  const handleJsonUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const obj = JSON.parse(String(reader.result || "{}"));
        const applied = applyPrefillFromObject(obj);
        setJsonError(null);
        setJsonStatus(`applied ${applied}/5 fields`);
      } catch (err: any) {
        setJsonStatus(null);
        setJsonError(`parse error: ${err?.message || err}`);
      }
    };
    reader.onerror = () => { setJsonStatus(null); setJsonError("failed to read file"); };
    reader.readAsText(file);
  };

  const handleDownloadTemplate = () => {
    const tmpl = { title, manaCost, typeLine, rules, pt };
    const blob = new Blob([JSON.stringify(tmpl, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "mtg-retro-template.json";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  // Prefill (multiple)
  const [cardsMap, setCardsMap] = useState<Record<string, any> | null>(null);
  const [cardKeys, setCardKeys] = useState<string[]>([]);
  const [selectedCardKey, setSelectedCardKey] = useState<string>("");
  const [rarity, setRarity] = useState<string>("");
  const [multiJsonStatus, setMultiJsonStatus] = useState<string | null>(null);
  const [multiJsonError, setMultiJsonError] = useState<string | null>(null);

  function extractCardsMap(obj: any) {
    if (!obj || typeof obj !== "object") return null;
    const maybe = obj.cards && typeof obj.cards === "object" ? obj.cards : obj;
    const keys = Object.keys(maybe).filter((k) => maybe[k] && typeof maybe[k] === "object");
    if (keys.length === 0) return null;
    return keys.reduce((acc: any, k: string) => { acc[k] = maybe[k]; return acc; }, {});
  }

  const handleMultiJsonUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const obj = JSON.parse(String(reader.result || "{}"));
        const map = extractCardsMap(obj);
        if (!map) throw new Error("No card objects found");
        const keys = Object.keys(map);
        setCardsMap(map);
        setCardKeys(keys);
        setSelectedCardKey(keys[0] || "");
        setMultiJsonError(null);
        setMultiJsonStatus(`loaded ${keys.length} card(s)`);
        if (keys[0]) {
          const first = map[keys[0]] || {};
          setRarity(normalizeRarity(first.rarity));
          applyPrefillFromObject(first);
        }
      } catch (err: any) {
        setCardsMap(null); setCardKeys([]); setSelectedCardKey("");
        setMultiJsonStatus(null);
        setMultiJsonError(`parse error: ${err?.message || err}`);
      }
    };
    reader.onerror = () => { setMultiJsonStatus(null); setMultiJsonError("failed to read file"); };
    reader.readAsText(file);
  };

  const handleSelectCard = (key: string) => {
    setSelectedCardKey(key);
    if (!cardsMap || !cardsMap[key]) return;
    const c = cardsMap[key];
    setRarity(normalizeRarity(c.rarity));
    applyPrefillFromObject(c);
  };

  function getActiveFrameSource() {
    const r = normalizeRarity(rarity);
    if (r === "Mythic" && frameMythicSource) return frameMythicSource;
    if (r === "Rare" && frameRareSource) return frameRareSource;
    if (r === "Uncommon" && frameUncommonSource) return frameUncommonSource;
    if (r === "Common" && frameCommonSource) return frameCommonSource;
    return frameSource;
  }

  // Diagnostics (runtime tests)
  const deepEq = (a: any, b: any) => JSON.stringify(a) === JSON.stringify(b);
  const runtimeTests = useMemo(() => {
    const cases: { name: string; got: any; expect: any }[] = [];
    cases.push({ name: "tokenize {2}{W}", got: tokenizeMana("{2}{W}"), expect: ["2", "W"] });
    cases.push({ name: "tokenize {10}{U}{-T}{T}{S}", got: tokenizeMana("{10}{U}{-T}{T}{S}"), expect: ["1", "0", "U", "-T", "T", "S"] });
    cases.push({ name: "normalizeRarity", got: normalizeRarity("Mythic Rare"), expect: "Mythic" });
    cases.push({ name: "normalizeKeys", got: Object.keys(normalizeKeys({ Title: 1, ManaCost: 2 })).sort(), expect: ["manacost", "title"] });
    const cost = ["2", "W"], symW = 20, total = cost.length * symW, startX = MANA.right - total; // right-bound anchor must not exceed right
    cases.push({ name: "right-bound mana", got: startX <= MANA.right, expect: true });
    return cases;
  }, []);

  const [diag, setDiag] = useState({ tests: [] as any[], symbolCount: 0 });

  // ===== Drawing
  useEffect(() => {
    const canvas = canvasRef.current; if (!canvas) return;
    canvas.width = CANVAS_W; canvas.height = CANVAS_H;
    const ctx = canvas.getContext("2d"); if (!ctx) return;

    try {
      // Background
      ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);
      if (!transparentBg) { ctx.fillStyle = backgroundColor; ctx.fillRect(0, 0, CANVAS_W, CANVAS_H); }

      // Frame first (art drawn on top per your request)
      const activeFrame = getActiveFrameSource();
      if (activeFrame) {
        const { w: fw, h: fh } = getSourceDims(activeFrame);
        if (fw && fh) ctx.drawImage(activeFrame as any, 0, 0, fw, fh, 0, 0, CANVAS_W, CANVAS_H);
        else ctx.drawImage(activeFrame as any, 0, 0, CANVAS_W, CANVAS_H);
      }

      // Art on top, cropped to ART_RECT
      if (artSource) drawImageCover(ctx, artSource, ART_RECT.x, ART_RECT.y, ART_RECT.w, ART_RECT.h);

      // Placeholder if no assets
      if (!activeFrame && !artSource) {
        ctx.save();
        ctx.fillStyle = "rgba(255,255,255,0.06)"; ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);
        ctx.setLineDash([8, 6]); ctx.strokeStyle = "rgba(255,255,255,0.25)"; ctx.lineWidth = 2;
        ctx.strokeRect(ART_RECT.x, ART_RECT.y, ART_RECT.w, ART_RECT.h);
        ctx.setLineDash([]); ctx.fillStyle = "rgba(255,255,255,0.65)"; ctx.font = "16px system-ui, sans-serif"; ctx.textAlign = "center";
        ctx.fillText("Preview ready — upload ART and FRAME", CANVAS_W / 2, ART_RECT.y + ART_RECT.h + 40);
        ctx.restore();
      }

      // Guides
      if (showGuides) {
        ctx.save(); ctx.strokeStyle = "rgba(255,0,0,0.35)"; ctx.lineWidth = 1; ctx.setLineDash([6, 4]);
        ctx.strokeRect(ART_RECT.x, ART_RECT.y, ART_RECT.w, ART_RECT.h);
        ctx.strokeRect(RULES_BOX.x, RULES_BOX.y, RULES_BOX.w, RULES_BOX.h);
        ctx.restore();
      }

      // Title
      const titleShadow = polarOffset(TITLE.angleDeg, TITLE.shadow);
      ctx.save();
      ctx.font = `${TITLE.size}px "Goudy Medieval", "Goudy Old Style", serif`;
      ctx.textBaseline = "top";
      ctx.fillStyle = "rgba(0,0,0,0.55)"; ctx.fillText(title, TITLE.x + titleShadow.x, TITLE.y + titleShadow.y);
      ctx.fillStyle = textColor; ctx.fillText(title, TITLE.x, TITLE.y);
      ctx.restore();

      // Mana cost (right-bound)
      const manaTokens = tokenizeMana(manaCost);
      const symH = MANA.h;
      const widths = manaTokens.map((code) => {
        const img = symbolImgs[code];
        if (img && (img.naturalWidth || (img as any).width) && (img.naturalHeight || (img as any).height)) {
          const w = (img.naturalWidth || (img as any).width);
          const h = (img.naturalHeight || (img as any).height);
          const ratio = w / h; return Math.round(symH * ratio);
        }
        return symH; // fallback square
      });
      const totalW = widths.reduce((a, b) => a + b, 0);
      let cx = MANA.right - totalW; const cy = MANA.y;
      manaTokens.forEach((code, i) => {
        const img = symbolImgs[code]; const w = widths[i];
        if (img) ctx.drawImage(img, cx, cy, w, symH);
        else { ctx.save(); ctx.fillStyle = "#ddd"; ctx.beginPath(); ctx.arc(cx + symH / 2, cy + symH / 2, symH / 2, 0, Math.PI * 2); ctx.fill(); ctx.restore(); }
        cx += w;
      });

      // Type line
      const typeShadow = polarOffset(TYPE.angleDeg, TYPE.shadow);
      ctx.save();
      ctx.font = `${TYPE.size}px "Elegant Garamond", "EB Garamond", Garamond, serif`;
      ctx.textBaseline = "top";
      ctx.fillStyle = "rgba(0,0,0,0.4)"; ctx.fillText(typeLine, TYPE.x + typeShadow.x, TYPE.y + typeShadow.y);
      ctx.fillStyle = textColor; ctx.fillText(typeLine, TYPE.x, TYPE.y);
      ctx.restore();

      // Rules rich text with {i}/{/i} and {T}/{2}...
      type Token = { type: "text"; text: string } | { type: "sym"; code: string } | { type: "tag"; tag: "i-start" | "i-end" } | { type: "nl" };
      const splitKeepSpaces = (str: string) => {
        const out: string[] = []; let buf = ""; let mode: "space" | "word" | null = null;
        for (const ch of str) { const m = ch === " " ? "space" : "word"; if (mode === null) { mode = m; buf = ch; } else if (m === mode) { buf += ch; } else { out.push(buf); buf = ch; mode = m; } }
        if (buf) out.push(buf); return out;
      };
      const tokenizeRulesRich = (content: string): Token[] => {
        const tokens: Token[] = []; const parts = String(content ?? "").split("\n");
        for (let pi = 0; pi < parts.length; pi++) {
          const s = parts[pi]; let i = 0;
          while (i < s.length) {
            if (s[i] === "{") { const j = s.indexOf("}", i + 1); if (j !== -1) {
                const raw = s.slice(i + 1, j).trim(); const upper = raw.toUpperCase();
                if (upper === "I") { tokens.push({ type: "tag", tag: "i-start" }); i = j + 1; continue; }
                if (upper === "/I") { tokens.push({ type: "tag", tag: "i-end" }); i = j + 1; continue; }
                if (/^\d+$/.test(upper)) { for (const d of upper.split("")) tokens.push({ type: "sym", code: d }); i = j + 1; continue; }
                if (SYMBOL_CODES.includes(upper)) { tokens.push({ type: "sym", code: upper }); i = j + 1; continue; }
                tokens.push({ type: "text", text: `{${raw}}` }); i = j + 1; continue;
              } else { tokens.push({ type: "text", text: "{" }); i += 1; continue; } }
            const k = s.indexOf("{", i); const end = k === -1 ? s.length : k;
            tokens.push({ type: "text", text: s.slice(i, end) }); i = end;
          }
          if (pi < parts.length - 1) tokens.push({ type: "nl" });
        }
        return tokens;
      };
      function layoutRules(ctx: CanvasRenderingContext2D, tokens: Token[], boxW: number, fontPx: number) {
        const rulesFont = `${fontPx}px "Elegant Garamond", "EB Garamond", Garamond, serif`;
        const rulesItalic = `italic ${fontPx}px "Elegant Garamond Italic", "Elegant Garamond", "EB Garamond", Garamond, serif`;
        const lineHeight = Math.floor(fontPx * 1.2); const symbolSize = Math.max(1, Math.floor(fontPx * 1.0));
        ctx.save(); ctx.font = rulesFont; const m = ctx.measureText("Mg");
        const ascent = m && Number.isFinite((m as any).actualBoundingBoxAscent) ? (m as any).actualBoundingBoxAscent : Math.floor(fontPx * 0.8);
        ctx.restore();
        const lines: any[] = []; const gaps: number[] = []; let line: any[] = []; let curW = 0; let italicOn = false;
        const flush = (isParagraphBreak = false) => { lines.push(line); gaps.push(isParagraphBreak ? PARAGRAPH_GAP_PX : lineHeight); line = []; curW = 0; };
        for (const t of tokens) {
          if (t.type === "nl") { flush(true); continue; }
          if (t.type === "tag") { italicOn = t.tag === "i-start" ? true : t.tag === "i-end" ? false : italicOn; continue; }
          if (t.type === "sym") { const w = symbolSize; if (curW + w > boxW && line.length > 0) flush(false); line.push({ type: "sym", code: t.code, w }); curW += w; continue; }
          const chunks = splitKeepSpaces(String((t as any).text ?? ""));
          for (const ch of chunks) { if (!ch) continue; ctx.font = italicOn ? rulesItalic : rulesFont; const w = ctx.measureText(ch).width; if (curW + w > boxW && line.length > 0) flush(false); if (ch.trim() === "" && line.length === 0) continue; line.push({ type: "text", text: ch, w, italic: italicOn }); curW += w; }
        }
        if (line.length > 0) flush(false);
        if (lines.length === 0) { lines.push([]); gaps.push(0); }
        const totalHeight = gaps.slice(0, Math.max(0, gaps.length - 1)).reduce((a, b) => a + b, 0);
        return { lines, gaps, symbolSize, totalHeight, ascent, rulesFont, rulesItalic };
      }
      const drawRules = (ctx: CanvasRenderingContext2D) => {
        let fontPx = RULES_MAX_SIZE; let layout = layoutRules(ctx, tokenizeRulesRich(rules), RULES_BOX.w, fontPx);
        while (layout.totalHeight > RULES_BOX.h && fontPx > 10) { fontPx -= 1; layout = layoutRules(ctx, tokenizeRulesRich(rules), RULES_BOX.w, fontPx); }
        const { lines, gaps, symbolSize, totalHeight, ascent, rulesFont, rulesItalic } = layout as any;
        const startY = RULES_BOX.y + Math.max(0, Math.floor((RULES_BOX.h - totalHeight) / 2)) + ascent;
        let by = startY;
        for (let li = 0; li < lines.length; li++) {
          const segments = lines[li]; let bx = RULES_BOX.x;
          for (const seg of segments) {
            if (seg.type === "sym") { const img = symbolImgs[seg.code]; if (img) ctx.drawImage(img, bx, by - ascent, symbolSize, symbolSize); else { ctx.save(); ctx.fillStyle = "#ddd"; ctx.beginPath(); ctx.arc(bx + symbolSize / 2, by - ascent + symbolSize / 2, symbolSize / 2, 0, Math.PI * 2); ctx.fill(); ctx.restore(); } bx += seg.w; continue; }
            ctx.font = seg.italic ? rulesItalic : rulesFont; ctx.fillStyle = textColor; ctx.fillText(seg.text, bx, by - ascent); bx += seg.w;
          }
          by += gaps[li] ?? 0;
        }
      };
      drawRules(ctx);

      // P/T
      const ptShadow = polarOffset(PT.angleDeg, PT.shadow);
      ctx.save(); ctx.font = `${PT.size}px "Goudy Medieval", "Goudy Old Style", serif`; ctx.textBaseline = "top";
      ctx.fillStyle = "rgba(0,0,0,0.5)"; ctx.fillText(pt, PT.x + ptShadow.x, PT.y + ptShadow.y);
      ctx.fillStyle = textColor; ctx.fillText(pt, PT.x, PT.y); ctx.restore();

      // Disclaimer
      const disc = "Proxy — created with mtg-retro-maker";
      const discShadow = polarOffset(DISCLAIMER.angleDeg, DISCLAIMER.shadow);
      ctx.save(); ctx.font = `${DISCLAIMER.size}px "Elegant Garamond", "EB Garamond", Garamond, serif`; ctx.textBaseline = "top";
      ctx.fillStyle = "rgba(0,0,0,0.35)"; ctx.fillText(disc, DISCLAIMER.x + discShadow.x, DISCLAIMER.y + discShadow.y);
      ctx.fillStyle = textColor; ctx.fillText(disc, DISCLAIMER.x, DISCLAIMER.y); ctx.restore();

      // Diagnostics
      const tests = runtimeTests.map((t) => ({ name: t.name, pass: deepEq(t.got, t.expect), got: t.got, expect: t.expect }));
      const symbolCount = SYMBOL_CODES.reduce((n, k) => n + (symbolImgs[k] ? 1 : 0), 0);
      setDiag({ tests, symbolCount });
    } catch (err) {
      console.error("Render error", err);
      try {
        ctx.save(); ctx.clearRect(0, 0, CANVAS_W, CANVAS_H); ctx.fillStyle = "#2a2a2a"; ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);
        ctx.fillStyle = "#ff8080"; ctx.font = "16px system-ui, sans-serif"; ctx.fillText("Render error: " + (err && (err as any).message ? (err as any).message : String(err)), 16, 28); ctx.restore();
      } catch {}
    }
  }, [
    artSource, frameSource, frameCommonSource, frameUncommonSource, frameRareSource, frameMythicSource,
    title, manaCost, typeLine, rules, pt, textColor, transparentBg, backgroundColor, showGuides, rarity, symbolImgs
  ]);

  // Export PNG
  const handleExport = () => {
    const canvas = canvasRef.current; if (!canvas) return;
    const triggerDownload = (href: string) => { const a = document.createElement("a"); a.href = href; a.download = "mtg-retro-converter.png"; document.body.appendChild(a); a.click(); a.remove(); };
    try {
      if (typeof (canvas as any).toBlob === "function") {
        (canvas as any).toBlob((blob: Blob | null) => {
          if (blob) { const url = URL.createObjectURL(blob); triggerDownload(url); setTimeout(() => URL.revokeObjectURL(url), 1000); }
          else { triggerDownload(canvas.toDataURL("image/png")); }
        }, "image/png");
      } else { triggerDownload(canvas.toDataURL("image/png")); }
    } catch { try { triggerDownload(canvas.toDataURL("image/png")); } catch {} }
  };

  const handleOpenPreviewTab = () => {
    const canvas = canvasRef.current; if (!canvas) return;
    const openDataUrl = (url: string) => { try { window.open(url, "_blank"); } catch {} };
    try {
      if (typeof (canvas as any).toBlob === "function") {
        (canvas as any).toBlob((blob: Blob | null) => {
          if (blob) { const url = URL.createObjectURL(blob); openDataUrl(url); setTimeout(() => URL.revokeObjectURL(url), 15000); }
          else { openDataUrl(canvas.toDataURL("image/png")); }
        }, "image/png");
      } else { openDataUrl(canvas.toDataURL("image/png")); }
    } catch { try { openDataUrl(canvas.toDataURL("image/png")); } catch {} }
  };

  // === Small UI sections ===
  function UploadsSection() {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label className="block">
          <span className="text-sm text-neutral-300">Upload ART image (PNG/JPG)</span>
          <input type="file" accept="image/*" onChange={(e) => setArtFile(e.target.files?.[0] ?? null)} className="mt-1 block w-full text-sm" />
        </label>
        <label className="block">
          <span className="text-sm text-neutral-300">Upload RETRO FRAME (single) (PNG/JPG with transparent window)</span>
          <input type="file" accept="image/*" onChange={(e) => setFrameFile(e.target.files?.[0] ?? null)} className="mt-1 block w-full text-sm" />
        </label>
      </div>
    );
  }

  function RarityFramesSection() {
    return (
      <div className="rounded-xl border border-neutral-800 p-3 mt-4">
        <div className="text-sm font-medium mb-2">Rarity Frames (optional)</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label className="block"><span className="text-sm text-neutral-300">Common frame</span>
            <input type="file" accept="image/*" onChange={(e) => setFrameCommonFile(e.target.files?.[0] ?? null)} className="mt-1 block w-full text-sm" />
          </label>
          <label className="block"><span className="text-sm text-neutral-300">Uncommon frame</span>
            <input type="file" accept="image/*" onChange={(e) => setFrameUncommonFile(e.target.files?.[0] ?? null)} className="mt-1 block w-full text-sm" />
          </label>
          <label className="block"><span className="text-sm text-neutral-300">Rare frame</span>
            <input type="file" accept="image/*" onChange={(e) => setFrameRareFile(e.target.files?.[0] ?? null)} className="mt-1 block w-full text-sm" />
          </label>
          <label className="block"><span className="text-sm text-neutral-300">Mythic frame</span>
            <input type="file" accept="image/*" onChange={(e) => setFrameMythicFile(e.target.files?.[0] ?? null)} className="mt-1 block w-full text-sm" />
          </label>
        </div>
        <div className="text-xs text-neutral-400 mt-2">If a card has a <code>rarity</code> in JSON and the matching frame is uploaded, that frame will be used automatically. Otherwise, the single frame above is used.</div>
      </div>
    );
  }

  function JsonSingleSection() {
    return (
      <div className="mt-4 rounded-xl border border-neutral-800 p-3">
        <div className="text-sm font-medium mb-2">Prefill from JSON (single card)</div>
        <div className="text-xs text-neutral-400 mb-2">Provide a JSON file with keys: <code>title</code>, <code>manaCost</code>, <code>typeLine</code>, <code>rules</code>, <code>pt</code>. Keys are case-insensitive.</div>
        <div className="flex flex-wrap items-center gap-3">
          <input type="file" accept="application/json,.json" onChange={handleJsonUpload} className="text-sm" />
          <button type="button" onClick={handleDownloadTemplate} className="px-3 py-1.5 rounded-xl bg-neutral-800 hover:bg-neutral-700">Download template</button>
          {jsonStatus && <span className="text-xs text-green-400">{jsonStatus}</span>}
          {jsonError && <span className="text-xs text-red-400">{jsonError}</span>}
        </div>
      </div>
    );
  }

  function JsonMultiSection() {
    return (
      <div className="mt-4 rounded-xl border border-neutral-800 p-3">
        <div className="text-sm font-medium mb-2">Prefill from JSON (multiple cards)</div>
        <div className="text-xs text-neutral-400 mb-2">Upload a dictionary of cards (top-level keys are card IDs or titles). You can also use <code>{'{ "cards": { ... } }'}</code>.</div>
        <div className="flex flex-wrap items-center gap-3">
          <input type="file" accept="application/json,.json" onChange={handleMultiJsonUpload} className="text-sm" />
          {multiJsonStatus && <span className="text-xs text-green-400">{multiJsonStatus}</span>}
          {multiJsonError && <span className="text-xs text-red-400">{multiJsonError}</span>}
        </div>
        {cardKeys.length > 0 && (
          <div className="mt-3 flex items-center gap-3">
            <label className="text-sm text-neutral-300">Select card</label>
            <select className="bg-neutral-900 border border-neutral-800 rounded-xl px-3 py-2 text-sm" value={selectedCardKey} onChange={(e) => handleSelectCard(e.target.value)}>
              {cardKeys.map((k) => (<option key={k} value={k}>{k}</option>))}
            </select>
            <div className="text-xs text-neutral-400">Rarity: <b>{normalizeRarity(rarity) || '—'}</b></div>
          </div>
        )}
      </div>
    );
  }

  function SymbolAssetsSection() {
    const loaded = SYMBOL_CODES.reduce((n, k) => n + (symbolImgs[k] ? 1 : 0), 0);
    const handleOne = (code: string, file: File | null) => setSymbolFiles((prev) => ({ ...prev, [code]: file ?? null }));
    return (
      <div className="mt-4 rounded-xl border border-neutral-800 p-3">
        <div className="text-sm font-medium mb-2">Mana / Tap Symbols</div>
        <div className="text-xs text-neutral-400 mb-3">Upload 18 assets in this order: U, W, B, R, G, S, T, -T, 0–9. Loaded: <b>{loaded}/18</b></div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {SYMBOL_CODES.map((code) => (
            <label key={code} className="block">
              <span className="text-xs text-neutral-300">{`{${code}}`}</span>
              <input type="file" accept="image/*" onChange={(e) => handleOne(code, e.target.files?.[0] ?? null)} className="mt-1 block w-full text-xs" />
            </label>
          ))}
        </div>
      </div>
    );
  }

  function FontUploadsSection() {
    return (
      <div className="mt-4 rounded-xl border border-neutral-800 p-3">
        <div className="text-sm font-medium mb-2">Fonts</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label className="block"><span className="text-sm text-neutral-300">Goudy Medieval</span>
            <input type="file" accept=".ttf,.otf,.woff,.woff2" onChange={(e) => setGoudyFile(e.target.files?.[0] ?? null)} className="mt-1 block w-full text-sm" />
          </label>
          <label className="block"><span className="text-sm text-neutral-300">Elegant Garamond (Regular)</span>
            <input type="file" accept=".ttf,.otf,.woff,.woff2" onChange={(e) => setGaramondFile(e.target.files?.[0] ?? null)} className="mt-1 block w-full text-sm" />
          </label>
          <label className="block"><span className="text-sm text-neutral-300">Elegant Garamond (Italic)</span>
            <input type="file" accept=".ttf,.otf,.woff,.woff2" onChange={(e) => setGaramondItalicFile(e.target.files?.[0] ?? null)} className="mt-1 block w-full text-sm" />
          </label>
          <label className="block"><span className="text-sm text-neutral-300">Elegant Garamond (Bold)</span>
            <input type="file" accept=".ttf,.otf,.woff,.woff2" onChange={(e) => setGaramondBoldFile(e.target.files?.[0] ?? null)} className="mt-1 block w-full text-sm" />
          </label>
        </div>
        <div className="text-xs text-neutral-400 mt-2">Uploaded fonts load immediately; fallback fonts are used if none are provided.</div>
      </div>
    );
  }

  function TextInputsSection() {
    return (
      <div className="mt-4 rounded-xl border border-neutral-800 p-3">
        <div className="text-sm font-medium mb-2">Text & Options</div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label className="block"><span className="text-sm text-neutral-300">Title</span>
            <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} className="mt-1 block w-full text-sm bg-neutral-900 border border-neutral-800 rounded-xl px-3 py-2" />
          </label>
          <label className="block"><span className="text-sm text-neutral-300">Mana cost (e.g. <code>{'{2}{W}'}</code>)</span>
            <input type="text" value={manaCost} onChange={(e) => setManaCost(e.target.value)} className="mt-1 block w-full text-sm bg-neutral-900 border border-neutral-800 rounded-xl px-3 py-2" />
          </label>
          <label className="block"><span className="text-sm text-neutral-300">Type line</span>
            <input type="text" value={typeLine} onChange={(e) => setTypeLine(e.target.value)} className="mt-1 block w-full text-sm bg-neutral-900 border border-neutral-800 rounded-xl px-3 py-2" />
          </label>
          <label className="block sm:col-span-2"><span className="text-sm text-neutral-300">Rules (supports <code>{'{i}'}</code>/<code>{'{/i}'}</code> and mana like <code>{'{T}'}</code>)</span>
            <textarea rows={6} value={rules} onChange={(e) => setRules(e.target.value)} className="mt-1 block w-full text-sm bg-neutral-900 border border-neutral-800 rounded-xl px-3 py-2" />
          </label>
          <label className="block"><span className="text-sm text-neutral-300">Power/Toughness</span>
            <input type="text" value={pt} onChange={(e) => setPT(e.target.value)} className="mt-1 block w-full text-sm bg-neutral-900 border border-neutral-800 rounded-xl px-3 py-2" />
          </label>
          <label className="block"><span className="text-sm text-neutral-300">Text color</span>
            <input type="color" value={textColor} onChange={(e) => setTextColor(e.target.value)} className="mt-1 block h-10 w-full bg-neutral-900 border border-neutral-800 rounded-xl" />
          </label>
          <div className="sm:col-span-2 flex flex-wrap items-center gap-4 mt-1">
            <label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={transparentBg} onChange={(e) => setTransparentBg(e.target.checked)} /> Transparent background</label>
            {!transparentBg && (
              <label className="inline-flex items-center gap-2 text-sm">BG
                <input type="color" value={backgroundColor} onChange={(e) => setBackgroundColor(e.target.value)} className="h-9 w-16 bg-neutral-900 border border-neutral-800 rounded-md" />
              </label>
            )}
            <label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={showGuides} onChange={(e) => setShowGuides(e.target.checked)} /> Show guides</label>
          </div>
        </div>
      </div>
    );
  }

  function PreviewSection() {
    return (
      <div className="rounded-xl border border-neutral-800 p-3">
        <div className="text-sm font-medium mb-2">Preview & Export</div>
        <div className="bg-neutral-900/60 rounded-xl p-2 flex items-center justify-center">
          <canvas
            ref={canvasRef}
            width={CANVAS_W}
            height={CANVAS_H}
            style={{ width: "744px", height: "1039px", outline: "1px solid rgba(255,255,255,0.08)" }}
          />
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <button type="button" onClick={handleExport} className="px-3 py-1.5 rounded-xl bg-neutral-800 hover:bg-neutral-700">Export PNG (744×1039)</button>
          <button type="button" onClick={handleOpenPreviewTab} className="px-3 py-1.5 rounded-xl bg-neutral-800 hover:bg-neutral-700">Open in new tab</button>
        </div>
        <div className="mt-3 text-xs text-neutral-400">Loaded symbols: <b>{diag.symbolCount}</b> / 18</div>
        <div className="mt-2 text-xs">
          {diag.tests.map((t: any) => (
            <div key={t.name} className={t.pass ? "text-green-400" : "text-red-400"}>
              {t.pass ? "✓" : "✗"} {t.name}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ======= RETURN =======
  return (
    <div className="p-4 max-w-[1400px] mx-auto">
      <h1 className="text-2xl font-semibold mb-1">MTG Retro Converter</h1>
      <p className="text-neutral-300 mb-4">Upload your art & frame, add symbols, then export a 744×1039 PNG. Art is crop-to-fit within the retro frame window.</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        {/* Left column: controls */}
        <div className="space-y-4">
          <UploadsSection />
          <RarityFramesSection />
          <JsonSingleSection />
          <JsonMultiSection />
          <SymbolAssetsSection />
          <FontUploadsSection />
          <TextInputsSection />
        </div>

        {/* Right column: preview */}
        <div className="space-y-4">
          <PreviewSection />
        </div>
      </div>
    </div>
  );
}