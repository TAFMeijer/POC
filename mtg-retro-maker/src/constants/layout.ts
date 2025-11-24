export const CANVAS_W = 744; // px
export const CANVAS_H = 1039; // px

// Layout
export const ART_RECT = { x: 86, y: 96, w: 572, h: 468 };
export const TITLE = { x: 85, y: 46, size: 43, shadow: 4, angleDeg: 60 };
export const MANA = { right: 685, y: 45, h: 36 }; // right-bound anchor
export const TYPE = { x: 80, y: 583, size: 34, shadow: 2, angleDeg: 60 };
export const RULES_BOX = { x: 90, y: 630, w: 565, h: 270 };
export const RULES_MAX_SIZE = 32; // dynamic sizing ceiling
export const PT = { x: 628, y: 943, size: 48, shadow: 4, angleDeg: 60 };
export const DISCLAIMER = { x: 80, y: 975, size: 20, shadow: 1, angleDeg: 60 };
export const PARAGRAPH_GAP_PX = 26; // fixed gap between paragraphs

// Mana/tap symbol codes (order required by user)
export const SYMBOL_CODES = [
  "U", "W", "B", "R", "G", "S", "T", "-T",
  "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"
];
