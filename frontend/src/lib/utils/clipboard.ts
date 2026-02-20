/**
 * Shared clipboard utility for robust copy-to-clipboard across HTTP/HTTPS contexts.
 */

/**
 * Copy text to clipboard. Uses execCommand as primary method (synchronous, works on HTTP),
 * falls back to Clipboard API if that fails.
 * @returns true if copy succeeded, false otherwise
 */
export async function copyToClipboard(text: string): Promise<boolean> {
	if (!text) return false;

	// Primary: synchronous execCommand (most reliable across HTTP/HTTPS)
	try {
		const textarea = document.createElement('textarea');
		textarea.value = text;
		textarea.style.position = 'fixed';
		textarea.style.left = '-9999px';
		textarea.style.top = '-9999px';
		textarea.style.opacity = '0';
		document.body.appendChild(textarea);
		textarea.focus();
		textarea.select();
		const success = document.execCommand('copy');
		document.body.removeChild(textarea);
		if (success) return true;
	} catch (err) {
		// Fall through to clipboard API
	}

	// Fallback: async Clipboard API
	try {
		await navigator.clipboard.writeText(text);
		return true;
	} catch (err) {
		console.error('Failed to copy text:', err);
		return false;
	}
}

/**
 * Format original + translated text into a combined string for "Copy Both".
 */
export function formatBothTexts(original: string, translated: string): string {
	let content = `ORIGINAL TEXT:\n${original}`;
	if (translated && translated.trim()) {
		content += `\n\nTRANSLATED TEXT:\n${translated}`;
	}
	return content;
}
