export function bestColumnMatches(columns: string[], query: string, limit: number = 5): string[] {
  const trimmed = query.trim();
  if (trimmed.length === 0) return [];

  const words = trimmed.split(/\s+/);
  const maxWords = Math.min(10, words.length);

  // Build candidate phrases using the last N words (1..10), keeping only those with >= 5 chars
  const phrases: { text: string; numWords: number }[] = [];
  for (let n = 1; n <= maxWords; n++) {
    const text = words.slice(-n).join(' ').toLowerCase();
    if (text.length >= 5) {
      phrases.push({ text, numWords: n });
    }
  }

  if (phrases.length === 0) return [];

  // Scoring heuristic:
  // - Evaluate each column against all candidate phrases and take the best score
  // - startsWith gets higher base than includes
  // - More words matched increases the score
  // - Penalize by distance (position and extra unmatched length)
  const scored = columns.map((col) => {
    const c = col.toLowerCase();
    let bestScore = -Infinity;
    for (const { text, numWords } of phrases) {
      const starts = c.startsWith(text);
      const idx = c.indexOf(text);
      if (starts) {
        const score = 200 + numWords * 20 - (c.length - text.length);
        if (score > bestScore) bestScore = score;
      } else if (idx >= 0) {
        const score = 100 + numWords * 20 - idx - (c.length - text.length);
        if (score > bestScore) bestScore = score;
      }
    }
    return { col, score: bestScore };
  });

  return scored
    .filter((s) => s.score !== -Infinity)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
    .map((s) => s.col);
}
