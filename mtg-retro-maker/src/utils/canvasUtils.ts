export const degToRad = (d: number) => (d * Math.PI) / 180;

export const polarOffset = (angleDeg: number, distance: number) => ({
    x: Math.cos(degToRad(angleDeg)) * distance,
    y: Math.sin(degToRad(angleDeg)) * distance,
});

export function getSourceDims(src: any) {
    const w = src && (src.width ?? src.naturalWidth ?? 0);
    const h = src && (src.height ?? src.naturalHeight ?? 0);
    return { w, h };
}

export function drawImageCover(
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
