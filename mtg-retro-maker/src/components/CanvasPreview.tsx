import { useRef } from "react";
import { CANVAS_W, CANVAS_H } from "../constants/layout";
import { useCanvasDrawer } from "../hooks/useCanvasDrawer";

interface CanvasPreviewProps {
    artSource: HTMLImageElement | null;
    frameSource: HTMLImageElement | null;
    frameCommonSource: HTMLImageElement | null;
    frameUncommonSource: HTMLImageElement | null;
    frameRareSource: HTMLImageElement | null;
    frameMythicSource: HTMLImageElement | null;
    symbolImgs: Record<string, HTMLImageElement | null>;
    raritySymbols: {
        common: HTMLImageElement | null;
        uncommon: HTMLImageElement | null;
        rare: HTMLImageElement | null;
        mythic: HTMLImageElement | null;
    };
    title: string;
    manaCost: string;
    typeLine: string;
    rules: string;
    pt: string;
    rarity: string;
    diag: { tests: any[]; symbolCount: number };
    setDiag: (diag: { tests: any[]; symbolCount: number }) => void;
    fontVersion: number;
}

export function CanvasPreview(props: CanvasPreviewProps) {
    const canvasRef = useRef<HTMLCanvasElement | null>(null);

    useCanvasDrawer({ ...props, canvasRef });

    const handleExport = () => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const triggerDownload = (href: string) => {
            const a = document.createElement("a");
            a.href = href;
            a.download = "mtg-retro-converter.png";
            document.body.appendChild(a);
            a.click();
            a.remove();
        };
        try {
            if (typeof (canvas as any).toBlob === "function") {
                (canvas as any).toBlob((blob: Blob | null) => {
                    if (blob) {
                        const url = URL.createObjectURL(blob);
                        triggerDownload(url);
                        setTimeout(() => URL.revokeObjectURL(url), 1000);
                    } else {
                        triggerDownload(canvas.toDataURL("image/png"));
                    }
                }, "image/png");
            } else {
                triggerDownload(canvas.toDataURL("image/png"));
            }
        } catch {
            try {
                triggerDownload(canvas.toDataURL("image/png"));
            } catch { }
        }
    };

    const handleOpenPreviewTab = () => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const openDataUrl = (url: string) => {
            try {
                window.open(url, "_blank");
            } catch { }
        };
        try {
            if (typeof (canvas as any).toBlob === "function") {
                (canvas as any).toBlob((blob: Blob | null) => {
                    if (blob) {
                        const url = URL.createObjectURL(blob);
                        openDataUrl(url);
                        setTimeout(() => URL.revokeObjectURL(url), 15000);
                    } else {
                        openDataUrl(canvas.toDataURL("image/png"));
                    }
                }, "image/png");
            } else {
                openDataUrl(canvas.toDataURL("image/png"));
            }
        } catch {
            try {
                openDataUrl(canvas.toDataURL("image/png"));
            } catch { }
        }
    };

    return (
        <div className="rounded-xl border border-neutral-800 p-3">
            <div className="text-sm font-medium mb-2">Preview & Export</div>
            <div className="bg-neutral-900/60 rounded-xl p-2 flex items-center justify-center">
                <canvas
                    ref={canvasRef}
                    width={CANVAS_W}
                    height={CANVAS_H}
                    style={{
                        width: "744px",
                        height: "1039px",
                        outline: "1px solid rgba(255,255,255,0.08)",
                    }}
                />
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-3">
                <button
                    type="button"
                    onClick={handleExport}
                    className="px-3 py-1.5 rounded-xl bg-neutral-800 hover:bg-neutral-700"
                >
                    Export PNG (744×1039)
                </button>
                <button
                    type="button"
                    onClick={handleOpenPreviewTab}
                    className="px-3 py-1.5 rounded-xl bg-neutral-800 hover:bg-neutral-700"
                >
                    Open in new tab
                </button>
            </div>
            <div className="mt-3 text-xs text-neutral-400">
                Loaded symbols: <b>{props.diag.symbolCount}</b> / 18
            </div>
            <div className="mt-2 text-xs">
                {props.diag.tests.map((t: any) => (
                    <div
                        key={t.name}
                        className={t.pass ? "text-green-400" : "text-red-400"}
                    >
                        {t.pass ? "✓" : "✗"} {t.name}
                    </div>
                ))}
            </div>
        </div>
    );
}
