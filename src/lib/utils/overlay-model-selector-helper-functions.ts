import type { Model } from '$lib/stores';

export interface ChatbotItem {
	label: string;
	value: string;
	model: Model;
	icon?: string;
	featured?: boolean;
	[key: string]: any;
}

/**
 * Determines if the chatbot overlay should be shown
 */
export function shouldShowChatbotOverlay(): boolean {
	return localStorage.getItem('chatbotOverlay.dontShowAgain') !== 'true';
}

/**
 * Processes models and returns items formatted for the overlay
 */
export function prepareOverlayItems(models: Model[]): ChatbotItem[] {
	return models.map(model => ({
		label: model.name || model.id,
		value: model.id,
		model,
		featured: isFeatured(model),
		icon: getModelIcon(model),
		description: getDescription(model),
		tags: getTagsExcludingFeatured(model)
	}));
}

/**
 * Returns all tags on a model except the "featured" tag (case‐insensitive).
 */
function getTagsExcludingFeatured(model: Model): {name: string}[] {
  const tags = model.info?.meta?.tags ?? [];
  return tags.filter(tag => tag.name.toLowerCase() !== 'featured');
}


/**
 * Returns true if the given model has a "featured" tag (case‐insensitive).
 */
function isFeatured(model: Model): boolean {
  const tags = model.info?.meta?.tags;
  if (!Array.isArray(tags)) return false;
	if (Array.isArray(tags) && tags.length === 0) return false;
  return tags.some(tag => tag.name.toLowerCase() === 'featured');
}

/**
 * Safely extracts the description from a model's metadata,
 * returning an empty string if none is set.
 */
function getDescription(model: Model): string {
  const desc = model.info?.meta?.description;
  return typeof desc === 'string' && desc.trim().length > 0
    ? desc
    : '';
}



/**
 * Gets an appropriate icon for a model
 */
function getModelIcon(model: Model): string {
	const name = model.name?.toLowerCase() || model.id.toLowerCase();

	if (name.includes('gpt')) return '⚡';
	if (name.includes('claude')) return '🎭';
	if (name.includes('gemini')) return '🔍';
	if (name.includes('llama')) return '📘';
	if (name.includes('mistral')) return '🌪️';
	if (name.includes('deepseek')) return '🔬';
	if (name.includes('ollama')) return '🦙';

	return '🤖';
}

/**
 * Resets the "don't show again" preference
 */
export function resetOverlayPreference(): void {
	localStorage.removeItem('chatbotOverlay.dontShowAgain');
}