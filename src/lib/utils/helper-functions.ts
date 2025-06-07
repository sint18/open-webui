// Helper function to extract company name from the model
export const getCompanyName = (model: any) => {
	if (model.owned_by === 'openai') {
		return 'OpenAI';
	} else if (model.owned_by === 'ollama') {
		// For Ollama models, use the family or parent_model to determine company
		if (model.ollama?.details?.family) {
			const family = model.ollama.details.family.toLowerCase();
			if (family === 'llama') return 'Meta';
			if (family === 'mistral' || family === 'mixtral') return 'Mistral';
			if (family === 'falcon') return 'TII';
			if (family === 'vicuna') return 'LMSYS';
			if (family === 'qwen') return 'Alibaba';
			if (family === 'phi') return 'Microsoft';
			// Add more family mappings as needed
		}
		return 'Ollama'; // Default for ollama models
	} else if (model.owned_by === 'arena') {
		return 'Arena';
	} else if (model.direct) {
		// For direct connections, try to extract company from name or source
		if (model.source?.includes('anthropic')) return 'Anthropic';
		if (model.source?.includes('google')) return 'Google';
		if (model.source?.includes('groq')) return 'Groq';
		if (model.source?.includes('cohere')) return 'Cohere';
		if (model.name.toLowerCase().includes('claude')) return 'Anthropic';
		if (model.name.toLowerCase().includes('gemini')) return 'Google';
		if (model.name.toLowerCase().includes('command')) return 'Cohere';
		// Add more model name patterns as needed
	}

	// If no specific company is identified, use the owned_by field
	return model.owned_by.charAt(0).toUpperCase() + model.owned_by.slice(1);
};

const modelLogoMap: Record<string, string> = {
	"openai": "/assets/chatgpt.png",
	"google": "/assets/gemini.png",
	"mistral": "/assets/mistral.png",
	"deepseek": "/assets/deepseek.png",
	"ollama": "/assets/ollama.png",
	"cohere": "/assets/cohere.png",
	"anthropic": "/assets/claude.png",
	"meta": "/assets/llama.png",
	"vicuna": "/assets/vicuna.png",
	"alibaba": "/assets/qwen.png",
	"microsoft": "/assets/phi.png",
	"falcon": "/assets/falcon.png",
};

export function getLogoForModel(company: string) {
	return modelLogoMap[company.toLowerCase()] || "/assets/favicon.png";
}


// Format model name to be more readable (remove dashes, capitalize properly)
export const formatModelName = (modelName: any) => {
	// Extract the base name without company prefix if it exists
	let baseName = modelName;
	if (modelName.includes(':')) {
		baseName = modelName.split(':').pop().trim();
	}

	// Handle common model name patterns
	if (baseName.toLowerCase().startsWith('gpt-')) {
		// Convert gpt-4-turbo to GPT 4 Turbo
		// Convert gpt-4o to GPT 4o
		return baseName
			.replace(/^gpt-/i, 'GPT ')
			.replace(/-([a-z])/g, (_, letter) => ' ' + letter.toLowerCase())
			.replace(/-(\d)/g, ' $1');
	}

	if (baseName.toLowerCase().startsWith('llama')) {
		// Convert llama3-70b to Llama 3 70B
		return baseName
			.replace(/llama(\d+)/i, 'Llama $1')
			.replace(/-(\d+)b/i, ' $1B');
	}

	if (baseName.toLowerCase().includes('mistral')) {
		// Convert mistral-7b-instruct to Mistral 7B Instruct
		return baseName
			.replace(/mistral/i, 'Mistral')
			.replace(/-(\d+)b/i, ' $1B')
			.replace(/-([a-z])/gi, (_, letter) => ' ' + letter.charAt(0).toUpperCase() + letter.slice(1));
	}

	if (baseName.toLowerCase().includes('mixtral')) {
		// Convert mixtral-8x7b to Mixtral 8x7B
		return baseName
			.replace(/mixtral/i, 'Mixtral')
			.replace(/-(\d+x\d+)b/i, ' $1B')
			.replace(/-([a-z])/gi, (_, letter) => ' ' + letter.charAt(0).toUpperCase() + letter.slice(1));
	}

	if (baseName.toLowerCase().includes('claude')) {
		// Convert claude-3-opus to Claude 3 Opus
		return baseName
			.replace(/claude/i, 'Claude')
			.replace(/-(\d+)/g, ' $1')
			.replace(/-([a-z])/gi, (_, letter) => ' ' + letter.charAt(0).toUpperCase() + letter.slice(1));
	}

	if (baseName.toLowerCase().includes('gemini')) {
		// Convert gemini-pro to Gemini Pro
		return baseName
			.replace(/gemini/i, 'Gemini')
			.replace(/-([a-z])/gi, (_, letter) => ' ' + letter.charAt(0).toUpperCase() + letter.slice(1));
	}

	if (baseName.toLowerCase().includes('codellama')) {
		// Convert codellama-34b to CodeLlama 34B
		return baseName
			.replace(/codellama/i, 'CodeLlama')
			.replace(/-(\d+)b/i, ' $1B');
	}

	if (baseName.toLowerCase().includes('falcon')) {
		// Convert falcon-40b to Falcon 40B
		return baseName
			.replace(/falcon/i, 'Falcon')
			.replace(/-(\d+)b/i, ' $1B');
	}

	// General formatting for other models
	return baseName
		.replace(/-(\d+)/g, ' $1')  // Replace dash followed by numbers with space and numbers
		.replace(/-([a-z])/gi, (_, letter) => ' ' + letter.charAt(0).toUpperCase() + letter.slice(1)) // Replace dash followed by letters with space and capitalized letter
		.replace(/^([a-z])/i, (_, letter) => letter.toLowerCase()); // Capitalize first letter
};