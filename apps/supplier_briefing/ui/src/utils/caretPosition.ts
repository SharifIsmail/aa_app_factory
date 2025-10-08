export type CaretPosition = { left: number; top: number };

function buildTextAreaMirror(textarea: HTMLTextAreaElement): HTMLDivElement {
  const mirror = document.createElement('div');
  const textareaStyle = window.getComputedStyle(textarea);

  mirror.style.position = 'absolute';
  mirror.style.visibility = 'hidden';
  mirror.style.whiteSpace = 'pre-wrap';
  mirror.style.wordWrap = 'break-word';
  mirror.style.overflow = 'hidden';
  mirror.style.top = '0px';
  mirror.style.left = '0px';
  mirror.style.width = `${textarea.clientWidth}px`;
  mirror.style.padding = textareaStyle.padding;
  mirror.style.border = textareaStyle.border;
  mirror.style.fontFamily = textareaStyle.fontFamily;
  mirror.style.fontSize = textareaStyle.fontSize;
  mirror.style.fontWeight = textareaStyle.fontWeight;
  mirror.style.lineHeight = textareaStyle.lineHeight;
  mirror.style.letterSpacing = textareaStyle.letterSpacing;
  mirror.style.boxSizing = textareaStyle.boxSizing as string;

  return mirror;
}

function clampLeftWithinContainer(
  left: number,
  containerWidth: number,
  dropdownWidth: number
): number {
  return Math.max(0, Math.min(left, containerWidth - dropdownWidth));
}

export function measureCaretRelativeToContainer(
  textarea: HTMLTextAreaElement,
  container: HTMLElement,
  caretIndex: number
): CaretPosition {
  const mirror = buildTextAreaMirror(textarea);

  const before = document.createTextNode(textarea.value.slice(0, caretIndex));
  const marker = document.createElement('span');
  marker.textContent = '.';
  const after = document.createTextNode(textarea.value.slice(caretIndex));
  mirror.appendChild(before);
  mirror.appendChild(marker);
  mirror.appendChild(after);

  container.appendChild(mirror);
  mirror.scrollTop = textarea.scrollTop;
  mirror.scrollLeft = textarea.scrollLeft;

  const markerRect = marker.getBoundingClientRect();
  const containerRect = container.getBoundingClientRect();

  const left = markerRect.left - containerRect.left;
  const top = markerRect.top - containerRect.top;

  container.removeChild(mirror);

  return { left, top };
}

export function computeDropdownPosition(options: {
  textarea: HTMLTextAreaElement;
  container: HTMLElement;
  caretIndex: number;
  dropdownWidth: number;
  verticalOffset: number;
}): CaretPosition {
  const { textarea, container, caretIndex, dropdownWidth, verticalOffset } = options;
  const { left, top } = measureCaretRelativeToContainer(textarea, container, caretIndex);
  const clampedLeft = clampLeftWithinContainer(left, container.clientWidth, dropdownWidth);
  return { left: clampedLeft, top: top + verticalOffset };
}
