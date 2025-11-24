export type Token =
    | { type: "text"; text: string; italic?: boolean; w?: number }
    | { type: "sym"; code: string; w?: number }
    | { type: "tag"; tag: "i-start" | "i-end" }
    | { type: "nl" };
