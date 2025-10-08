export type SuggestionInsertionResult = {
  newText: string;
  newCaretIndex: number;
};

/**
 * Computes how to insert or replace text when a suggestion is chosen.
 */
export function computeSuggestionInsertion(
  currentText: string,
  suggestion: string,
  caretIndex: number
): SuggestionInsertionResult {
  const safeCaret = Math.max(0, Math.min(caretIndex, currentText.length));
  const prefix = currentText.slice(0, safeCaret);
  const suffix = currentText.slice(safeCaret);

  const suggestionLower = suggestion.toLowerCase();
  const wordMatches = [...prefix.matchAll(/\S+/g)];

  let replaceStart = -1;
  let matchedLength = -1;

  if (wordMatches.length > 0) {
    const maxWords = Math.min(10, wordMatches.length);
    for (let n = 1; n <= maxWords; n++) {
      const startIndex = wordMatches[wordMatches.length - n].index ?? 0;
      const rawTail = prefix.slice(startIndex);
      const normalizedTail = rawTail.replace(/\s+/g, ' ').trim();
      if (normalizedTail.length >= 5 && suggestionLower.includes(normalizedTail.toLowerCase())) {
        if (normalizedTail.length > matchedLength) {
          replaceStart = startIndex;
          matchedLength = normalizedTail.length;
        }
      }
    }
  }

  if (replaceStart >= 0) {
    let replaceEnd = safeCaret;
    while (replaceEnd < currentText.length && /\S/.test(currentText[replaceEnd])) {
      replaceEnd++;
    }

    const beforeText = currentText.slice(0, replaceStart);
    const afterText = currentText.slice(replaceEnd);
    const newText = beforeText + suggestion + afterText;
    const newCaretIndex = beforeText.length + suggestion.length;
    return { newText, newCaretIndex };
  }

  const newText = prefix + suggestion + suffix;
  const newCaretIndex = prefix.length + suggestion.length;
  return { newText, newCaretIndex };
}
