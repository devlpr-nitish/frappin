<template>
	<button
		type="button"
		class="frappin-copy-button"
		:aria-label="copied ? 'Copied' : `Copy ${value}`"
		:title="copied ? 'Copied' : 'Copy'"
		@click="$emit('copy', value)"
	>
		<svg viewBox="0 0 24 24" aria-hidden="true">
			<path v-if="copied" d="m6 12 4 4 8-8" />
			<template v-else>
				<rect x="8" y="8" width="11" height="12" rx="2" />
				<path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h2" />
			</template>
		</svg>
	</button>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	value: { type: String, required: true },
	copiedValue: { type: String, default: "" },
});

defineEmits(["copy"]);

const copied = computed(() => props.copiedValue === props.value);
</script>
