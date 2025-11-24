export function tokenizeMana(mana: string) {
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
