import { useEffect, useMemo } from "react";
import {
    CANVAS_W,
    CANVAS_H,
    ART_RECT,
    TITLE,
    MANA,
    TYPE,
    RULES_BOX,
    RULES_MAX_SIZE,
    PT,
    DISCLAIMER,
    PARAGRAPH_GAP_PX,
    SYMBOL_CODES,
    RARITY_SYMBOL,
} from "../constants/layout";
import {
    polarOffset,
    getSourceDims,
    drawImageCover,
} from "../utils/canvasUtils";
import { tokenizeMana } from "../utils/manaUtils";
import type { Token } from "../utils/types";

interface CanvasDrawerProps {
    canvasRef: React.RefObject<HTMLCanvasElement | null>;
    artSource: HTMLImageElement | null;
    frameSource: HTMLImageElement | null;
    frameCommonSource: HTMLImageElement | null;
    frameUncommonSource: HTMLImageElement | null;
    frameRareSource: HTMLImageElement | null;
    frameMythicSource: HTMLImageElement | null;
    symbolImgs: Record<string, HTMLImageElement | null>;
    title: string;
    manaCost: string;
    typeLine: string;
    rules: string;
    pt: string;
    rarity: string;
    raritySymbols: {
        common: HTMLImageElement | null;
        uncommon: HTMLImageElement | null;
        rare: HTMLImageElement | null;
        mythic: HTMLImageElement | null;
    };
    setDiag: (diag: { tests: any[]; symbolCount: number }) => void;
    fontVersion: number;
}

export function useCanvasDrawer({
    canvasRef,
    artSource,
    frameSource,
    frameCommonSource,
    frameUncommonSource,
    frameRareSource,
    frameMythicSource,
    symbolImgs,
    title,
    manaCost,
    typeLine,
    rules,
    pt,
    rarity,
    raritySymbols,
    setDiag,
    fontVersion,
}: CanvasDrawerProps) {
    // Diagnostics (runtime tests)
    const deepEq = (a: any, b: any) => JSON.stringify(a) === JSON.stringify(b);
    const runtimeTests = useMemo(() => {
        const cases: { name: string; got: any; expect: any }[] = [];
        cases.push({
            name: "tokenize {2}{W}",
            got: tokenizeMana("{2}{W}"),
            expect: ["2", "W"],
        });
        cases.push({
            name: "tokenize {10}{U}{-T}{T}{S}",
            got: tokenizeMana("{10}{U}{-T}{T}{S}"),
            expect: ["1", "0", "U", "-T", "T", "S"],
        });
        // normalizeRarity and normalizeKeys are now in utils, tested there implicitly or we can import them to test
        const cost = ["2", "W"],
            symW = 20,
            total = cost.length * symW,
            startX = MANA.right - total;
        cases.push({
            name: "right-bound mana",
            got: startX <= MANA.right,
            expect: true,
        });
        return cases;
    }, []);

    function normalizeRarity(r: any) {
        const s = String(r || "").toLowerCase();
        if (!s) return "";
        if (s.includes("myth")) return "Mythic";
        if (s.includes("un") && s.includes("common")) return "Uncommon";
        if (s.includes("rare")) return "Rare";
        if (s.includes("common")) return "Common";
        return r;
    }

    function getActiveFrameSource() {
        const r = normalizeRarity(rarity);
        if (r === "Mythic" && frameMythicSource) return frameMythicSource;
        if (r === "Rare" && frameRareSource) return frameRareSource;
        if (r === "Uncommon" && frameUncommonSource) return frameUncommonSource;
        if (r === "Common" && frameCommonSource) return frameCommonSource;
        return frameSource;
    }

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        canvas.width = CANVAS_W;
        canvas.height = CANVAS_H;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        try {
            // Background
            ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);
            // Transparent background enforced

            // Frame first (art drawn on top per your request)
            const activeFrame = getActiveFrameSource();
            if (activeFrame) {
                const { w: fw, h: fh } = getSourceDims(activeFrame);
                if (fw && fh)
                    ctx.drawImage(
                        activeFrame as any,
                        0,
                        0,
                        fw,
                        fh,
                        0,
                        0,
                        CANVAS_W,
                        CANVAS_H
                    );
                else ctx.drawImage(activeFrame as any, 0, 0, CANVAS_W, CANVAS_H);
            }

            // Art on top, cropped to ART_RECT
            if (artSource)
                drawImageCover(
                    ctx,
                    artSource,
                    ART_RECT.x,
                    ART_RECT.y,
                    ART_RECT.w,
                    ART_RECT.h
                );

            // Rarity Symbol
            const normRarity = normalizeRarity(rarity);
            let rarityIcon = raritySymbols.common;
            if (normRarity === "Mythic") rarityIcon = raritySymbols.mythic;
            else if (normRarity === "Rare") rarityIcon = raritySymbols.rare;
            else if (normRarity === "Uncommon") rarityIcon = raritySymbols.uncommon;
            else if (normRarity === "Common") rarityIcon = raritySymbols.common;

            if (rarityIcon) {
                ctx.drawImage(
                    rarityIcon,
                    RARITY_SYMBOL.x,
                    RARITY_SYMBOL.y,
                    RARITY_SYMBOL.w,
                    RARITY_SYMBOL.h
                );
            }

            // Placeholder if no assets
            if (!activeFrame && !artSource) {
                ctx.save();
                ctx.fillStyle = "rgba(255,255,255,0.06)";
                ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);
                ctx.setLineDash([8, 6]);
                ctx.strokeStyle = "rgba(255,255,255,0.25)";
                ctx.lineWidth = 2;
                ctx.strokeRect(ART_RECT.x, ART_RECT.y, ART_RECT.w, ART_RECT.h);
                ctx.setLineDash([]);
                ctx.fillStyle = "rgba(255,255,255,0.65)";
                ctx.font = "16px system-ui, sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(
                    "Preview ready — upload ART and FRAME",
                    CANVAS_W / 2,
                    ART_RECT.y + ART_RECT.h + 40
                );
                ctx.restore();
            }



            // Title
            const titleShadow = polarOffset(TITLE.angleDeg, TITLE.shadow);

            // 1. Draw Shadow
            ctx.save();
            ctx.font = `${TITLE.size}px "Goudy Medieval", "Goudy Old Style", serif`;
            ctx.textBaseline = "top";
            ctx.shadowColor = "rgba(0,0,0,0.5)";
            ctx.shadowBlur = 2;
            ctx.fillStyle = "rgba(0,0,0,0.5)";
            ctx.fillText(
                title,
                TITLE.x + titleShadow.x,
                TITLE.y + titleShadow.y
            );
            ctx.restore();

            // 2. Draw Main Text (Thinned)
            // We draw to an offscreen canvas and erode the edges with destination-out stroke
            const tempCanvas = document.createElement("canvas");
            tempCanvas.width = CANVAS_W;
            tempCanvas.height = CANVAS_H;
            const tCtx = tempCanvas.getContext("2d");
            if (tCtx) {
                tCtx.font = `${TITLE.size}px "Goudy Medieval", "Goudy Old Style", serif`;
                tCtx.textBaseline = "top";
                tCtx.fillStyle = "rgba(255,255,255,0.9)";
                tCtx.fillText(title, TITLE.x, TITLE.y);

                // Erode edges to make text thinner
                tCtx.globalCompositeOperation = "destination-out";
                tCtx.lineWidth = 0.5;
                tCtx.strokeStyle = "black";
                tCtx.strokeText(title, TITLE.x, TITLE.y);

                ctx.drawImage(tempCanvas, 0, 0);
            }

            // Mana cost (right-bound)
            const manaTokens = tokenizeMana(manaCost);
            const symH = MANA.h;
            const widths = manaTokens.map((code) => {
                const img = symbolImgs[code];
                if (
                    img &&
                    (img.naturalWidth || (img as any).width) &&
                    (img.naturalHeight || (img as any).height)
                ) {
                    const w = img.naturalWidth || (img as any).width;
                    const h = img.naturalHeight || (img as any).height;
                    const ratio = w / h;
                    return Math.round(symH * ratio);
                }
                return symH; // fallback square
            });
            const totalW = widths.reduce((a, b) => a + b, 0);
            let cx = MANA.right - totalW;
            const cy = MANA.y;
            manaTokens.forEach((code, i) => {
                const img = symbolImgs[code];
                const w = widths[i];
                if (img) ctx.drawImage(img, cx, cy, w, symH);
                else {
                    ctx.save();
                    ctx.fillStyle = "#ddd";
                    ctx.beginPath();
                    ctx.arc(cx + symH / 2, cy + symH / 2, symH / 2, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.restore();
                }
                cx += w;
            });

            // Type line
            const typeShadow = polarOffset(TYPE.angleDeg, TYPE.shadow);
            ctx.save();
            ctx.font = `${TYPE.size}px "Elegant Garamond", "EB Garamond", Garamond, serif`;
            ctx.textBaseline = "top";
            ctx.fillStyle = "rgba(0,0,0,0.4)";
            ctx.fillText(typeLine, TYPE.x + typeShadow.x, TYPE.y + typeShadow.y);
            ctx.fillStyle = "#E9E7E3";
            ctx.fillText(typeLine, TYPE.x, TYPE.y);
            ctx.restore();

            // Rules rich text
            const splitKeepSpaces = (str: string) => {
                const out: string[] = [];
                let buf = "";
                let mode: "space" | "word" | null = null;
                for (const ch of str) {
                    const m = ch === " " ? "space" : "word";
                    if (mode === null) {
                        mode = m;
                        buf = ch;
                    } else if (m === mode) {
                        buf += ch;
                    } else {
                        out.push(buf);
                        buf = ch;
                        mode = m;
                    }
                }
                if (buf) out.push(buf);
                return out;
            };
            const tokenizeRulesRich = (content: string): Token[] => {
                const tokens: Token[] = [];
                const parts = String(content ?? "").split("\n");
                for (let pi = 0; pi < parts.length; pi++) {
                    const s = parts[pi];
                    let i = 0;
                    while (i < s.length) {
                        if (s[i] === "{") {
                            const j = s.indexOf("}", i + 1);
                            if (j !== -1) {
                                const raw = s.slice(i + 1, j).trim();
                                const upper = raw.toUpperCase();
                                if (upper === "I") {
                                    tokens.push({ type: "tag", tag: "i-start" });
                                    i = j + 1;
                                    continue;
                                }
                                if (upper === "/I") {
                                    tokens.push({ type: "tag", tag: "i-end" });
                                    i = j + 1;
                                    continue;
                                }
                                if (/^\d+$/.test(upper)) {
                                    for (const d of upper.split(""))
                                        tokens.push({ type: "sym", code: d });
                                    i = j + 1;
                                    continue;
                                }
                                if (SYMBOL_CODES.includes(upper)) {
                                    tokens.push({ type: "sym", code: upper });
                                    i = j + 1;
                                    continue;
                                }
                                tokens.push({ type: "text", text: `{${raw}}` });
                                i = j + 1;
                                continue;
                            } else {
                                tokens.push({ type: "text", text: "{" });
                                i += 1;
                                continue;
                            }
                        }
                        const k = s.indexOf("{", i);
                        const end = k === -1 ? s.length : k;
                        tokens.push({ type: "text", text: s.slice(i, end) });
                        i = end;
                    }
                    if (pi < parts.length - 1) tokens.push({ type: "nl" });
                }
                return tokens;
            };
            function layoutRules(
                ctx: CanvasRenderingContext2D,
                tokens: Token[],
                boxW: number,
                fontPx: number
            ) {
                const rulesFont = `${fontPx}px "Elegant Garamond", "EB Garamond", Garamond, serif`;
                const rulesItalic = `italic ${fontPx}px "Elegant Garamond Italic", "Elegant Garamond", "EB Garamond", Garamond, serif`;
                const lineHeight = Math.floor(fontPx * 1.2);
                const symbolSize = Math.max(1, Math.floor(fontPx * 1.0));
                ctx.save();
                ctx.font = rulesFont;
                const m = ctx.measureText("Mg");
                const ascent =
                    m && Number.isFinite(m.actualBoundingBoxAscent)
                        ? m.actualBoundingBoxAscent
                        : Math.floor(fontPx * 0.8);
                ctx.restore();
                const lines: any[] = [];
                const gaps: number[] = [];
                let line: any[] = [];
                let curW = 0;
                let italicOn = false;
                const flush = (isParagraphBreak = false) => {
                    lines.push(line);
                    gaps.push(isParagraphBreak ? PARAGRAPH_GAP_PX : lineHeight);
                    line = [];
                    curW = 0;
                };
                for (const t of tokens) {
                    if (t.type === "nl") {
                        flush(true);
                        continue;
                    }
                    if (t.type === "tag") {
                        italicOn =
                            t.tag === "i-start" ? true : t.tag === "i-end" ? false : italicOn;
                        continue;
                    }
                    if (t.type === "sym") {
                        const w = symbolSize;
                        if (curW + w > boxW && line.length > 0) flush(false);
                        line.push({ type: "sym", code: t.code, w });
                        curW += w;
                        continue;
                    }
                    const chunks = splitKeepSpaces(String((t as any).text ?? ""));
                    for (const ch of chunks) {
                        if (!ch) continue;
                        ctx.font = italicOn ? rulesItalic : rulesFont;
                        const w = ctx.measureText(ch).width;
                        if (curW + w > boxW && line.length > 0) flush(false);
                        if (ch.trim() === "" && line.length === 0) continue;
                        line.push({ type: "text", text: ch, w, italic: italicOn });
                        curW += w;
                    }
                }
                if (line.length > 0) flush(false);
                if (lines.length === 0) {
                    lines.push([]);
                    gaps.push(0);
                }
                const totalHeight = gaps
                    .slice(0, Math.max(0, gaps.length - 1))
                    .reduce((a, b) => a + b, 0);
                return {
                    lines,
                    gaps,
                    symbolSize,
                    totalHeight,
                    ascent,
                    rulesFont,
                    rulesItalic,
                };
            }
            const drawRules = (ctx: CanvasRenderingContext2D) => {
                let fontPx = RULES_MAX_SIZE;
                let layout = layoutRules(
                    ctx,
                    tokenizeRulesRich(rules),
                    RULES_BOX.w,
                    fontPx
                );
                while (layout.totalHeight > RULES_BOX.h && fontPx > 10) {
                    fontPx -= 1;
                    layout = layoutRules(
                        ctx,
                        tokenizeRulesRich(rules),
                        RULES_BOX.w,
                        fontPx
                    );
                }
                const {
                    lines,
                    gaps,
                    symbolSize,
                    totalHeight,
                    ascent,
                    rulesFont,
                    rulesItalic,
                } = layout as any;
                const startY =
                    RULES_BOX.y +
                    Math.max(0, Math.floor((RULES_BOX.h - totalHeight) / 2)) +
                    ascent;
                let by = startY;
                for (let li = 0; li < lines.length; li++) {
                    const segments = lines[li];
                    let bx = RULES_BOX.x;
                    for (const seg of segments) {
                        if (seg.type === "sym") {
                            const img = symbolImgs[seg.code];
                            // Align symbol relative to baseline 'by'
                            // symbolSize is roughly fontPx. 0.85 offset places it nicely on the line.
                            const symY = by - (symbolSize * 0.85);
                            if (img)
                                ctx.drawImage(
                                    img,
                                    bx,
                                    symY,
                                    symbolSize,
                                    symbolSize
                                );
                            else {
                                ctx.save();
                                ctx.fillStyle = "#ddd";
                                ctx.beginPath();
                                ctx.arc(
                                    bx + symbolSize / 2,
                                    symY + symbolSize / 2,
                                    symbolSize / 2,
                                    0,
                                    Math.PI * 2
                                );
                                ctx.fill();
                                ctx.restore();
                            }
                            bx += seg.w;
                            continue;
                        }
                        ctx.font = seg.italic ? rulesItalic : rulesFont;
                        ctx.fillStyle = "#000000";
                        ctx.fillText(seg.text, bx, by);
                        bx += seg.w;
                    }
                    by += gaps[li] ?? 0;
                }
            };
            drawRules(ctx);

            // P/T
            const ptShadow = polarOffset(PT.angleDeg, PT.shadow);
            ctx.save();
            ctx.font = `${PT.size}px "Elegant Garamond", "EB Garamond", Garamond, serif`;
            ctx.textBaseline = "top";
            ctx.fillStyle = "rgba(0,0,0,0.5)";
            ctx.fillText(pt, PT.x + ptShadow.x, PT.y + ptShadow.y);
            ctx.fillStyle = "#E9E7E3";
            ctx.fillText(pt, PT.x, PT.y);
            ctx.restore();

            // Disclaimer
            const disc = "mtg-retro-maker - NOT FOR SALE";
            const discShadow = polarOffset(DISCLAIMER.angleDeg, DISCLAIMER.shadow);
            ctx.save();
            ctx.font = `${DISCLAIMER.size}px "Elegant Garamond", "EB Garamond", Garamond, serif`;
            ctx.textBaseline = "top";
            //ctx.fillStyle = "rgba(255, 255, 255, 0.5)";//White for Artifact
            ctx.fillStyle = "rgba(0,0,0,0.5)";//Black for White
            ctx.fillText(
                disc,
                DISCLAIMER.x + discShadow.x,
                DISCLAIMER.y + discShadow.y
            );
            ctx.fillText(disc, DISCLAIMER.x, DISCLAIMER.y);
            ctx.restore();

            // Diagnostics
            const tests = runtimeTests.map((t) => ({
                name: t.name,
                pass: deepEq(t.got, t.expect),
                got: t.got,
                expect: t.expect,
            }));
            const symbolCount = SYMBOL_CODES.reduce(
                (n, k) => n + (symbolImgs[k] ? 1 : 0),
                0
            );
            setDiag({ tests, symbolCount });
        } catch (err) {
            console.error("Render error", err);
            try {
                ctx.save();
                ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);
                ctx.fillStyle = "#2a2a2a";
                ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);
                ctx.fillStyle = "#ff8080";
                ctx.font = "16px system-ui, sans-serif";
                ctx.fillText(
                    "Render error: " +
                    (err && (err as any).message
                        ? (err as any).message
                        : String(err)),
                    16,
                    28
                );
                ctx.restore();
            } catch { }
        }
    }, [
        artSource,
        frameSource,
        frameCommonSource,
        frameUncommonSource,
        frameRareSource,
        frameMythicSource,
        title,
        manaCost,
        typeLine,
        rules,
        pt,

        rarity,
        raritySymbols,
        symbolImgs,
        runtimeTests,
        setDiag,
        fontVersion,
    ]);
}
