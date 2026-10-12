<template>
	<fieldset class="frappin-share-fields">
		<legend>Share</legend>
		<label class="frappin-share-choice">
			<input type="radio" :checked="mode === 'private'" @change="$emit('update:mode', 'private')" />
			<span>Private</span>
		</label>
		<label class="frappin-share-choice">
			<input type="radio" :checked="mode === 'users'" @change="$emit('update:mode', 'users')" />
			<span>Specific users</span>
		</label>
		<label class="frappin-share-choice">
			<input type="radio" :checked="mode === 'everyone'" @change="$emit('update:mode', 'everyone')" />
			<span>Everyone</span>
		</label>
		<div v-if="mode === 'users'" class="frappin-share-users">
			<label v-for="user in users" :key="user.value">
				<input
					type="checkbox"
					:checked="selectedUsers.includes(user.value)"
					@change="toggleUser(user.value)"
				/>
				<span>{{ user.label }}<small v-if="user.label !== user.value">{{ user.value }}</small></span>
			</label>
			<p v-if="!users.length">No other enabled users found.</p>
		</div>
		<div v-if="mode !== 'private'" class="frappin-share-rights">
			<strong>Recipient permissions</strong>
			<label>
				<input type="checkbox" checked disabled />
				<span>View</span>
			</label>
			<label>
				<input
					type="checkbox"
					:checked="allowEdit"
					@change="$emit('update:allowEdit', $event.target.checked)"
				/>
				<span>Edit</span>
			</label>
			<label>
				<input
					type="checkbox"
					:checked="allowDelete"
					@change="$emit('update:allowDelete', $event.target.checked)"
				/>
				<span>Delete</span>
			</label>
		</div>
	</fieldset>
</template>

<script setup>
const props = defineProps({
	mode: { type: String, default: "private" },
	selectedUsers: { type: Array, default: () => [] },
	users: { type: Array, default: () => [] },
	allowEdit: { type: Boolean, default: false },
	allowDelete: { type: Boolean, default: false },
});

const emit = defineEmits(["update:mode", "update:selectedUsers", "update:allowEdit", "update:allowDelete"]);

function toggleUser(user) {
	const selected = props.selectedUsers.includes(user)
		? props.selectedUsers.filter((value) => value !== user)
		: [...props.selectedUsers, user];
	emit("update:selectedUsers", selected);
}
</script>
