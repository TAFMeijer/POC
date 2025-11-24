import { useEffect, useState } from "react";
import { SYMBOL_CODES } from "../constants/layout";

export interface StaticAssets {
    frames: {
        common: HTMLImageElement | null;
        uncommon: HTMLImageElement | null;
        rare: HTMLImageElement | null;
        mythic: HTMLImageElement | null;
    };
    symbols: Record<string, HTMLImageElement | null>;
    fontsLoaded: boolean;
    loading: boolean;
}

const ASSET_BASE = "/assets";

// Helper to load an image
const loadImage = (src: string): Promise<HTMLImageElement | null> => {
    return new Promise((resolve) => {
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.onload = () => resolve(img);
        img.onerror = () => {
            console.warn(`Failed to load image: ${src}`);
            resolve(null);
        };
        img.src = src;
    });
};

// Helper to load a font
const loadFont = async (name: string, src: string) => {
    try {
        const font = new FontFace(name, `url(${src})`);
        await font.load();
        (document as any).fonts.add(font);
        return true;
    } catch (e) {
        console.warn(`Failed to load font ${name} from ${src}`, e);
        return false;
    }
};

export function useStaticAssets() {
    const [assets, setAssets] = useState<StaticAssets>({
        frames: { common: null, uncommon: null, rare: null, mythic: null },
        symbols: {},
        fontsLoaded: false,
        loading: true,
    });

    useEffect(() => {
        let mounted = true;

        const loadAll = async () => {
            // 1. Load Fonts
            const fonts = [
                loadFont("Goudy Medieval", `${ASSET_BASE}/GoudyMedievalAlternate.ttf`),
                loadFont("Elegant Garamond", `${ASSET_BASE}/ElegantGaramondRegular.otf`),
                loadFont("Elegant Garamond Italic", `${ASSET_BASE}/ElegantGaramondItalics.otf`),
                loadFont("Elegant Garamond Bold", `${ASSET_BASE}/ElegantGaramondBold.otf`),
            ];
            await Promise.all(fonts);

            if (!mounted) return;

            // 2. Load Frames
            const [common, uncommon, rare, mythic] = await Promise.all([
                loadImage(`${ASSET_BASE}/White-retro-frame-common.png`),
                loadImage(`${ASSET_BASE}/White-retro-frame-uncommon.png`),
                loadImage(`${ASSET_BASE}/White-retro-frame-rare.png`),
                loadImage(`${ASSET_BASE}/White-retro-frame-mythic.png`),
            ]);

            if (!mounted) return;

            // 3. Load Symbols
            const symbolPromises = SYMBOL_CODES.map(async (code) => {
                // Map code to filename
                let filename = `{${code}}.png`;
                // Handle special cases if any (e.g. {T} is svg, {W} is jpg based on file list)
                if (code === "T") filename = "{T}.svg";
                if (code === "W") filename = "{W}.jpg";

                const img = await loadImage(`${ASSET_BASE}/${filename}`);
                return [code, img] as const;
            });

            const loadedSymbols = await Promise.all(symbolPromises);
            const symbolMap: Record<string, HTMLImageElement | null> = {};
            loadedSymbols.forEach(([code, img]) => {
                if (img) symbolMap[code] = img;
            });

            if (!mounted) return;

            setAssets({
                frames: { common, uncommon, rare, mythic },
                symbols: symbolMap,
                fontsLoaded: true,
                loading: false,
            });
        };

        loadAll();

        return () => {
            mounted = false;
        };
    }, []);

    return assets;
}
