<template>
	<div class="frappin-item-actions">
		<button
			type="button"
			class="frappin-item-action frappin-item-action--delete"
			:class="{ 'is-active': item.pinned }"
			:aria-label="item.pinned ? 'Remove permanent pin' : 'Make permanent and pin'"
			:title="item.pinned ? 'Remove permanent pin' : 'Make permanent and pin'"
			@click="$emit('pin', item)"
		>
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="m15 4 5 5-3 2-4 5-2-2-5 5-1-1 5-5-2-2 5-4Z" />
			</svg>
		</button>
		<button
			type="button"
			class="frappin-item-action"
			aria-label="Edit item"
			title="Edit"
			@click="$emit('edit', item)"
		>
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
			</svg>
		</button>
		<button
			type="button"
			class="frappin-item-action"
			aria-label="Delete item"
			title="Delete"
			@click="$emit('delete', item)"
		>
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<path d="M4 7h16M9 7V4h6v3M7 7l1 13h8l1-13M10 11v5M14 11v5" />
			</svg>
		</button>
		<CopyButton :value="item.value" :copied-value="copiedValue" @copy="$emit('copy', $event)" />
	</div>
</template>

<script setup>
import CopyButton from "./CopyButton.vue";

defineProps({
	item: { type: Object, required: true },
	copiedValue: { type: String, default: "" },
});

defineEmits(["copy", "pin", "edit", "delete"]);
</script>
