<template>
	<div ref="actionsRoot" class="frappin-item-actions">
		<CopyButton :value="item.value" :copied-value="copiedValue" @copy="$emit('copy', $event)" />
		<button
			v-if="item.is_owner || item.can_edit || item.can_delete || item.can_share"
			type="button"
			class="frappin-item-action"
			aria-label="More item actions"
			title="More actions"
			:aria-expanded="menuOpen"
			@click.stop="menuOpen = !menuOpen"
			@keydown.esc="menuOpen = false"
		>
			<svg viewBox="0 0 24 24" aria-hidden="true">
				<circle cx="5" cy="12" r="1" />
				<circle cx="12" cy="12" r="1" />
				<circle cx="19" cy="12" r="1" />
			</svg>
		</button>

		<div v-if="menuOpen" class="frappin-item-menu" role="menu" @click.stop>
			<button
				v-if="item.is_owner"
				type="button"
				role="menuitem"
				:class="{ 'is-active': item.pinned }"
				@click="choose('pin')"
			>
				<svg viewBox="0 0 24 24" aria-hidden="true">
					<path d="m15 4 5 5-3 2-4 5-2-2-5 5-1-1 5-5-2-2 5-4Z" />
				</svg>
				<span>{{ item.pinned ? "Unpin item" : "Pin item" }}</span>
			</button>
			<button
				v-if="item.is_owner"
				type="button"
				role="menuitem"
				:class="{ 'is-active': item.permanent }"
				@click="choose('permanent')"
			>
				<svg viewBox="0 0 24 24" aria-hidden="true">
					<path d="M12 3 19 6v5c0 4.6-2.8 8-7 10-4.2-2-7-5.4-7-10V6Z" />
					<path v-if="item.permanent" d="m9 12 2 2 4-4" />
				</svg>
				<span>{{ item.permanent ? "Remove permanent" : "Make permanent" }}</span>
			</button>
			<button v-if="item.can_edit" type="button" role="menuitem" @click="choose('edit')">
				<svg viewBox="0 0 24 24" aria-hidden="true">
					<path d="M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
				</svg>
				<span>Edit</span>
			</button>
			<button v-if="item.can_share" type="button" role="menuitem" @click="choose('share')">
				<svg viewBox="0 0 24 24" aria-hidden="true">
					<circle cx="18" cy="5" r="3" />
					<circle cx="6" cy="12" r="3" />
					<circle cx="18" cy="19" r="3" />
					<path d="m8.6 10.5 6.8-4M8.6 13.5l6.8 4" />
				</svg>
				<span>Share</span>
			</button>
			<button
				v-if="item.can_delete"
				type="button"
				class="frappin-item-menu__delete"
				role="menuitem"
				@click="choose('delete')"
			>
				<svg viewBox="0 0 24 24" aria-hidden="true">
					<path d="M4 7h16M9 7V4h6v3M7 7l1 13h8l1-13M10 11v5M14 11v5" />
				</svg>
				<span>Delete</span>
			</button>
		</div>
	</div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from "vue";
import CopyButton from "./CopyButton.vue";

const props = defineProps({
	item: { type: Object, required: true },
	copiedValue: { type: String, default: "" },
});

const emit = defineEmits(["copy", "pin", "permanent", "edit", "share", "delete"]);
const actionsRoot = ref(null);
const menuOpen = ref(false);

function choose(action) {
	menuOpen.value = false;
	emit(action, props.item);
}

function closeOutside(event) {
	if (!actionsRoot.value?.contains(event.target)) {
		menuOpen.value = false;
	}
}

onMounted(() => document.addEventListener("pointerdown", closeOutside));
onBeforeUnmount(() => document.removeEventListener("pointerdown", closeOutside));
</script>
