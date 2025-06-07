<script lang="ts">
	import { getCompanyName, getLogoForModel } from '$lib/utils/helper-functions';
	import { WEBUI_BASE_URL } from '$lib/constants';
	import { models } from '$lib/stores';
	import { getContext } from 'svelte';

	export let selectedModel

	const i18n = getContext('i18n');

	function getModelProfileImage(model) {
		if (!model) return "/static/favicon.png";
		const modelInfo = $models.find(m => m.id === model.id);
		const companyName = getCompanyName(modelInfo)
		const profileImage = modelInfo?.info?.meta?.profile_image_url === "/static/favicon.png" ? getLogoForModel(companyName) : modelInfo?.info?.meta?.profile_image_url

		if (profileImage) {
			return profileImage;
		}

		return $i18n.language === 'dg-DG'
			? '/doge.png'
			: `${WEBUI_BASE_URL}/static/favicon.png`;
	}

</script>


<img
	crossorigin="anonymous"
	alt="model profile logo for {selectedModel?.name ?? ''}"
	src={getModelProfileImage(selectedModel)}
	{...$$restProps}
/>