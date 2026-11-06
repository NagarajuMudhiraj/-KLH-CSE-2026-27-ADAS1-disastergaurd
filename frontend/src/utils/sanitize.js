import DOMPurify from 'dompurify';

/**
 * Escapes unsafe characters in strings before interpolation into raw HTML strings.
 * Converts &, <, >, ", ' to their safe HTML entity representations.
 */
export function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Sanitizes rich HTML string using modern patched DOMPurify.
 */
export function sanitizeHtml(html) {
  return DOMPurify.sanitize(html);
}
