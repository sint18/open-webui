// Helper function to extract company name from the model
// utils/getCompanyName.ts
export const getCompanyName = (model: {
	id?: string;
	name?: string;
	owned_by?: string;
	source?: string;
	ollama?: { details?: { family?: string } };
}) => {
	const id = (model.id ?? '').toLowerCase();
	const name = (model.name ?? '').toLowerCase();

	/* ---------- 1. Easy string-contains matches on id / name ---------- */

	if (id.includes('gpt') || name.includes('gpt')) return 'OpenAI';
	if (id.includes('claude') || name.includes('claude')) return 'Anthropic';
	if (id.includes('gemini') || name.includes('gemini')) return 'Google';
	if (id.includes('command') || name.includes('command')) return 'Cohere';
	if (id.includes('groq') || name.includes('groq')) return 'Groq';

	/* ---------- 2. Ollama family mapping (works for both local + LiteLLM) ---------- */
	const family = model.ollama?.details?.family?.toLowerCase();
	if (family) {
		if (family === 'llama') return 'Meta';
		if (family === 'mistral' || family === 'mixtral') return 'Mistral';
		if (family === 'falcon') return 'TII';
		if (family === 'vicuna') return 'LMSYS';
		if (family === 'qwen') return 'Alibaba';
		if (family === 'phi') return 'Microsoft';
	}

	/* ---------- 3. Source string (still works for LiteLLM virtual key) ---------- */
	const src = model.source?.toLowerCase() ?? '';
	if (src.includes('anthropic')) return 'Anthropic';
	if (src.includes('gemini')) return 'Google';
	if (src.includes('groq')) return 'Groq';
	if (src.includes('cohere')) return 'Cohere';

	/* ---------- 4. Legacy fallback ---------- */
	if (typeof model.owned_by === 'string' && model.owned_by.length) {
		return model.owned_by.charAt(0).toUpperCase() + model.owned_by.slice(1);
	}

	/* ---------- 5. Give up gracefully ---------- */
	return 'Unknown';
};

const modelLogoMap: Record<string, string> = {
	openai: '/assets/chatgpt.png',
	google: '/assets/gemini.png',
	mistral: '/assets/mistral.png',
	deepseek: '/assets/deepseek.png',
	ollama: '/assets/ollama.png',
	cohere: '/assets/cohere.png',
	anthropic: '/assets/claude.png',
	meta: '/assets/llama.png',
	vicuna: '/assets/vicuna.png',
	alibaba: '/assets/qwen.png',
	microsoft: '/assets/phi.png',
	falcon: '/assets/falcon.png'
};

export function getLogoForModel(company: string) {
	return modelLogoMap[company.toLowerCase()] || '/assets/favicon.png';
}

// Format model name to be more readable (remove dashes, capitalize properly)

export const formatModelName = (modelName: string): string => {
	if (!modelName) return '';

	/* ---------- 1.  Strip provider prefix (e.g. "Google: …") ---------- */
	let base = modelName.includes(':') ? modelName.split(':').pop()!.trim() : modelName.trim();

	/* ---------- 2.  Remove duplicate word before a “/” ---------------- */
	base = base.replace(/^([a-z0-9]+)\/\1(?=[-/\s]|$)/i, '$1');

	/* ---------- 3.  Cut “Preview …” and trailing separators ----------- */
	base = base
		.replace(/\bpreview.*$/i, '') // drop “Preview-…”
		.replace(/[-_/]+$/, '') // ➊ strip any leftover - / _
		.trim();

	/* ---------- 4.  Normalise separators ----------------------------- */
	base = base.replace(/\//g, ' ').replace(/\s+/g, ' ').trim();
	const lower = base.toLowerCase();

	/* ---------- 5.  Friendly names ----------------------------------- */
	if (lower.startsWith('gpt-')) {
		return base
			.replace(/^gpt-/i, 'GPT ')
			.replace(/-([a-z])/g, (_, l) => ' ' + l.toLowerCase())
			.replace(/-(\d)/g, ' $1')
			.trim();
	}

	if (lower.startsWith('gemini')) {
		const pretty = base
			.replace(/gemini/i, 'Gemini')
			.replace(/-(\d+(\.\d+)?)/g, ' $1')
			.replace(/-([a-z])/gi, (_, l) => ' ' + l.toUpperCase())
			.trim();

		return pretty.replace(/[-\s]+$/, ''); // ➋ final clean-up
	}

	// Llama → “Llama 3 70B”
	if (lower.startsWith('llama')) {
		return base
			.replace(/llama(\d+)/i, 'Llama $1')
			.replace(/-(\d+)b/i, ' $1B')
			.trim();
	}

	// Mistral → “Mistral 7B Instruct”
	if (lower.includes('mistral')) {
		return base
			.replace(/mistral/i, 'Mistral')
			.replace(/-(\d+)b/i, ' $1B')
			.replace(/-([a-z])/gi, (_, l) => ' ' + l.charAt(0).toUpperCase() + l.slice(1))
			.trim();
	}

	// Mixtral → “Mixtral 8×7B”
	if (lower.includes('mixtral')) {
		return base
			.replace(/mixtral/i, 'Mixtral')
			.replace(/-(\d+x\d+)b/i, ' $1B')
			.replace(/-([a-z])/gi, (_, l) => ' ' + l.charAt(0).toUpperCase() + l.slice(1))
			.trim();
	}

	// Claude → “Claude 3 Opus”
	if (lower.includes('claude')) {
		return base
			.replace(/claude/i, 'Claude')
			.replace(/-(\d+)/g, ' $1')
			.replace(/-([a-z])/gi, (_, l) => ' ' + l.charAt(0).toUpperCase() + l.slice(1))
			.trim();
	}

	// CodeLlama, Falcon, … (unchanged from your original)
	if (lower.includes('codellama')) {
		return base.replace(/codellama/i, 'CodeLlama').replace(/-(\d+)b/i, ' $1B');
	}
	if (lower.includes('falcon')) {
		return base.replace(/falcon/i, 'Falcon').replace(/-(\d+)b/i, ' $1B');
	}

	/* ---------- 6.  Generic fallback --------------------------------- */
	return base
		.replace(/-(\d+)/g, ' $1')
		.replace(/-([a-z])/gi, (_, l) => ' ' + l.charAt(0).toUpperCase() + l.slice(1))
		.replace(/\b\w/g, (c) => c.toUpperCase())
		.replace(/[-\s]+$/, '') // ➋ catch-all clean
		.trim();
};
