/**
 * Extracts meaningful text content from markdown for highlighting purposes.
 *
 * This function processes markdown text to extract clean, highlightable text chunks
 * by removing markdown syntax while preserving the actual content. It handles:
 * - Table structures (extracts cell content, ignores separators)
 * - Heading markers (removes #, ##, etc.)
 * - List markers (removes -, *, 1., etc.)
 * - Empty lines and markdown-only syntax
 *
 * @param markdown - Raw markdown text containing tables, headings, lists, etc.
 * @returns Array of clean text chunks suitable for highlighting
 *
 * @example
 * ```typescript
 * const markdown = `
 * # Main Title
 * ## Subtitle
 * | Cell 1 | Cell 2 |
 * | --- | --- |
 * | Data A | Data B |
 * - List item
 * `;
 * Returns: ["Main Title", "Subtitle", "Cell 1", "Cell 2", "Data A", "Data B", "List item"]
 * ```
 */
export const extractTextFromMarkdown = (markdown: string): string[] => {
  const lines = markdown
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => {
      // Skip empty lines, table separators, and pure markdown syntax
      if (!line || line.match(/^[|\-\s:]+$/)) return false;
      if (line.startsWith('---')) return false;
      if (line.match(/^\|[\s\-|]*\|$/)) return false; // Empty table rows
      return true;
    });

  const chunks = lines
    .map((line) => {
      if (line.includes('|')) {
        // Extract table cell content, filtering out empty cells and separators
        const tableCells = line
          .split('|')
          .map((cell) => cell.trim())
          .filter((cell) => cell && !cell.match(/^[-\s]*$/));
        return tableCells;
      }

      // Clean markdown syntax from headings and other block elements
      const cleanedLine = line
        .replace(/^#{1,6}\s+/, '') // Remove heading markers: "## title" → "title"
        .replace(/^\*{1,2}\s*/, '') // Remove list markers: "* item" → "item"
        .replace(/^-\s+/, '') // Remove dash markers: "- item" → "item"
        .replace(/^\d+\.\s+/, '') // Remove numbered lists: "1. item" → "item"
        .trim();

      return [cleanedLine];
    })
    .flat()
    .filter((line) => line.trim().length > 0);

  return chunks;
};

/**
 * Preprocesses law text by converting literal newline characters and normalizing spacing.
 *
 * This function handles common text preprocessing needed for legal documents:
 * - Converts literal `\n` strings to actual newline characters
 * - Normalizes multiple consecutive newlines to double newlines for proper paragraph spacing
 *
 * @param text - Raw text that may contain literal newline characters
 * @returns Processed text with proper newline formatting
 *
 * @example
 * ```typescript
 * const rawText = "Title\\n\\nParagraph 1\\n\\n\\n\\nParagraph 2";
 * const processed = preprocessMarkdownText(rawText);
 * // Returns: "Title\n\nParagraph 1\n\nParagraph 2"
 * ```
 */
export const preprocessMarkdownText = (text: string): string => {
  if (!text) return '';

  let processedText = text.replace(/\\n/g, '\n');

  processedText = processedText.replace(/\n\n+/g, '\n\n');

  return processedText;
};

/**
 * Wraps text content with a styled mark tag for highlighting.
 *
 * @param text - The text content to wrap with highlighting
 * @returns HTML string with the text wrapped in a styled mark tag
 *
 * @example
 * ```typescript
 * const highlighted = wrapWithMarkTag("European Commission");
 * // Returns: '<mark style="background-color: #ffeb3b; padding: 2px 4px; border-radius: 3px;">European Commission</mark>'
 * ```
 */
export const wrapWithMarkTag = (text: string): string => {
  return `<mark style="background-color: #ffeb3b; padding: 2px 4px; border-radius: 3px;">${text}</mark>`;
};

/**
 * Finds text chunks in sequential order within the provided text.
 *
 * This function looks for text chunks that appear in the exact order provided,
 * ensuring they form a logical sequence. It's designed for highlighting citation content
 * where chunks should appear consecutively (possibly separated by markdown formatting).
 *
 * @param text - The full text to search within
 * @param chunks - Array of text chunks to find in sequence
 * @returns Array of match objects with start position, end position, and matched text
 *
 * @example
 * ```typescript
 * const text = "European flag symbol Official Journal of the European Union EN L series";
 * const chunks = ["European flag", "Official Journal", "EN L series"];
 *
 * const matches = findSequentialMatches(text, chunks);
 * // Returns: [
 * //   { start: 0, end: 13, text: "European flag" },
 * //   { start: 21, end: 37, text: "Official Journal" },
 * //   { start: 65, end: 77, text: "EN L series" }
 * // ]
 * ```
 */
export const findSequentialMatches = (
  text: string,
  chunks: string[]
): Array<{ start: number; end: number; text: string }> => {
  if (chunks.length === 0) return [];

  const matches: Array<{ start: number; end: number; text: string }> = [];
  let searchStartPosition = 0;

  // Try to find each chunk in order
  for (const chunk of chunks) {
    const index = text.toLowerCase().indexOf(chunk.toLowerCase(), searchStartPosition);

    if (index === -1) {
      // If we can't find this chunk after the previous one, no sequential match exists
      return [];
    }

    matches.push({
      start: index,
      end: index + chunk.length,
      text: text.slice(index, index + chunk.length), // Preserve original casing
    });

    // Next search should start after this match
    searchStartPosition = index + chunk.length;
  }

  return matches;
};
