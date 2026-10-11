<template>
	<section
		id="frappin-smart-clipboard"
		class="frappin-panel"
		:class="{ 'is-resizing': resizing }"
		:style="panelStyle"
		role="dialog"
		aria-modal="false"
		aria-labelledby="frappin-panel-title"
	>
		<div
			class="frappin-resize-handle"
			role="separator"
			tabindex="0"
			aria-label="Resize Smart Clipboard panel"
			aria-orientation="horizontal"
			@pointerdown="startResize"
			@keydown="resizeWithKeyboard"
		></div>

		<header class="frappin-panel__header">
			<div class="frappin-panel__identity">
				<img
					class="frappin-panel__brand-icon"
					src="/assets/frappin/images/frappin-pin.svg?v=2"
					alt=""
				/>
				<div>
					<h2 id="frappin-panel-title">Frappin</h2>
				</div>
			</div>

			<div class="frappin-panel__actions">
				<button
					type="button"
					class="frappin-icon-button"
					aria-label="Close Frappin"
					@click="$emit('close')"
				>
					<svg viewBox="0 0 24 24" aria-hidden="true">
						<path d="m6 6 12 12M18 6 6 18" />
					</svg>
				</button>
			</div>
		</header>

		<div class="frappin-search-row">
			<label class="frappin-search">
				<svg viewBox="0 0 24 24" aria-hidden="true">
					<circle cx="11" cy="11" r="7" />
					<path d="m16 16 4 4" />
				</svg>
				<input ref="searchInput" v-model.trim="query" type="search" placeholder="Search your copied items..." />
			</label>
			<button type="button" class="frappin-create-button" aria-label="Create new snippet" title="Create new snippet">
				<svg viewBox="0 0 24 24" aria-hidden="true">
					<path d="M12 5v14M5 12h14" />
				</svg>
			</button>
		</div>

		<nav class="frappin-filters" aria-label="Clipboard filters">
			<button
				v-for="filter in filters"
				:key="filter"
				type="button"
				:class="{ 'is-active': activeFilter === filter }"
				@click="activeFilter = filter"
			>
				{{ filter }}
			</button>
		</nav>

		<div class="frappin-panel__content">
			<div v-if="loading" class="frappin-empty">Loading your clipboard…</div>

			<section v-if="visiblePinned.length" class="frappin-section">
				<div class="frappin-section__heading">
					<h3>Pinned items</h3>
					<span>{{ visiblePinned.length }} {{ visiblePinned.length === 1 ? "item" : "items" }}</span>
				</div>

				<div class="frappin-pinned-list">
					<article v-for="item in visiblePinned" :key="item.id" class="frappin-pinned-card">
						<div class="frappin-item-icon">
							<svg v-if="item.icon === 'hash'" viewBox="0 0 24 24" aria-hidden="true">
								<path d="M10 3 8 21M16 3l-2 18M4 9h16M3 15h16" />
							</svg>
							<svg v-else viewBox="0 0 24 24" aria-hidden="true">
								<rect x="5" y="3" width="14" height="18" rx="2" />
								<path d="M9 8h6M9 12h5" />
							</svg>
						</div>
						<button type="button" class="frappin-item-copy" @click="copyItem(item.value)">
							<strong>{{ item.title }}</strong>
							<span>{{ item.subtitle }}</span>
						</button>
						<ItemActions
							:item="item"
							:copied-value="copiedValue"
							@copy="copyItem"
							@pin="togglePin"
							@edit="editItem"
							@delete="deleteItem"
						/>
					</article>
				</div>
			</section>

			<section v-if="visibleRecent.length" class="frappin-section frappin-section--recent">
				<div class="frappin-section__heading">
					<h3>Recent clipboard</h3>
					<button
						v-if="matchingRecent.length > 3"
						type="button"
						@click="showAllRecent = !showAllRecent"
					>
						{{ showAllRecent ? "Show less" : `View all (${matchingRecent.length})` }}
					</button>
				</div>

				<div class="frappin-recent-list">
					<article v-for="item in visibleRecent" :key="item.id" class="frappin-recent-row">
						<div class="frappin-item-icon">
							<svg v-if="item.icon === 'box'" viewBox="0 0 24 24" aria-hidden="true">
								<path d="m4 7 8-4 8 4-8 4ZM4 7v10l8 4 8-4V7M12 11v10" />
							</svg>
							<svg v-else-if="item.icon === 'mail'" viewBox="0 0 24 24" aria-hidden="true">
								<rect x="3" y="5" width="18" height="14" rx="2" />
								<path d="m4 7 8 6 8-6" />
							</svg>
							<svg v-else viewBox="0 0 24 24" aria-hidden="true">
								<path d="M6 3h9l4 4v14H6Z" />
								<path d="M14 3v5h5M9 14l2 2 4-4" />
							</svg>
						</div>
						<button type="button" class="frappin-item-copy" @click="copyItem(item.value)">
							<strong>{{ item.title }}</strong>
							<span>{{ item.subtitle }}</span>
						</button>
						<ItemActions
							:item="item"
							:copied-value="copiedValue"
							@copy="copyItem"
							@pin="togglePin"
							@edit="editItem"
							@delete="deleteItem"
						/>
					</article>
				</div>
			</section>

			<div v-if="!loading && !visiblePinned.length && !visibleRecent.length" class="frappin-empty">
				No clipboard items found.
			</div>
		</div>


	</section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import ItemActions from "./ItemActions.vue";

defineEmits(["close"]);

const filters = ["All", "Pinned", "Recent", "ERP Documents"];
const activeFilter = ref("All");
const query = ref("");
const panelPinned = ref(false);
const copiedValue = ref("");
const searchInput = ref(null);
const resizing = ref(false);
const loading = ref(true);
const items = ref([]);
const showAllRecent = ref(false);

const SIZE_KEY = "frappin-panel-size";
const panelSize = ref(loadPanelSize());
let resizeSession = null;

const panelStyle = computed(() => ({
	"--frappin-panel-width": `${panelSize.value.width}px`,
	"--frappin-panel-height": `${panelSize.value.height}px`,
}));

function loadPanelSize() {
	try {
		const value = JSON.parse(localStorage.getItem(SIZE_KEY));
		if (Number.isFinite(value?.width) && Number.isFinite(value?.height)) {
			return value;
		}
	} catch {
		// Use the default size when saved state is unavailable.
	}
	return { width: 608, height: 720 };
}

function constrainSize(width, height) {
	return {
		width: Math.min(Math.max(width, 340), Math.max(340, window.innerWidth - 24)),
		height: Math.min(Math.max(height, 420), Math.max(420, window.innerHeight - 88)),
	};
}

function startResize(event) {
	if (event.button !== 0 || window.innerWidth <= 576) {
		return;
	}
	event.preventDefault();
	resizeSession = {
		startX: event.clientX,
		startY: event.clientY,
		width: panelSize.value.width,
		height: panelSize.value.height,
	};
	resizing.value = true;
	document.addEventListener("pointermove", resizePanel);
	document.addEventListener("pointerup", stopResize, { once: true });
}

function resizePanel(event) {
	if (!resizeSession) {
		return;
	}
	panelSize.value = constrainSize(
		resizeSession.width - (event.clientX - resizeSession.startX),
		resizeSession.height - (event.clientY - resizeSession.startY)
	);
}

function stopResize() {
	if (resizeSession) {
		localStorage.setItem(SIZE_KEY, JSON.stringify(panelSize.value));
	}
	resizeSession = null;
	resizing.value = false;
	document.removeEventListener("pointermove", resizePanel);
}

function resizeWithKeyboard(event) {
	const step = event.shiftKey ? 40 : 10;
	const changes = {
		ArrowLeft: [step, 0],
		ArrowRight: [-step, 0],
		ArrowUp: [0, step],
		ArrowDown: [0, -step],
	};
	if (!changes[event.key]) {
		return;
	}
	event.preventDefault();
	const [widthChange, heightChange] = changes[event.key];
	panelSize.value = constrainSize(
		panelSize.value.width + widthChange,
		panelSize.value.height + heightChange
	);
	localStorage.setItem(SIZE_KEY, JSON.stringify(panelSize.value));
}

const pinnedItems = computed(() => items.value.filter((item) => item.pinned));
const recentItems = computed(() => items.value.filter((item) => !item.pinned));

function displayTitle(item) {
	if (item.title) {
		return item.title;
	}
	const firstLine = (item.content || "").split(/\r?\n/, 1)[0];
	return firstLine.length > 64 ? `${firstLine.slice(0, 61)}...` : firstLine;
}

function relativeTime(value) {
	if (!value) {
		return "just now";
	}
	const date = new Date(value.replace(" ", "T"));
	const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
	if (seconds < 60) return "just now";
	if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
	if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
	return `${Math.floor(seconds / 86400)} days ago`;
}

function presentItem(item) {
	const erpDocument = Boolean(item.source_doctype);
	const typeLabel = erpDocument
		? `${item.source_doctype}${item.source_name ? ` · ${item.source_name}` : ""}`
		: item.content_type === "url"
			? "URL"
			: "Copied text";
	return {
		...item,
		id: item.name,
		title: displayTitle(item),
		subtitle: `${typeLabel} · ${relativeTime(item.last_used_at || item.creation)}`,
		value: item.content,
		icon: erpDocument ? "hash" : item.content.includes("@") ? "mail" : "note",
		erpDocument,
	};
}

async function loadItems() {
	try {
		const response = await fetch("/api/method/frappin.api.get_clipboard_items?limit=100", {
			headers: { Accept: "application/json" },
			credentials: "same-origin",
		});
		const payload = await response.json();
		if (response.ok) {
			items.value = (payload.message || []).map(presentItem);
		}
	} catch (error) {
		console.warn("Frappin could not load clipboard items.", error);
	} finally {
		loading.value = false;
	}
}

function matchesSearch(item) {
	if (!query.value) {
		return true;
	}

	const searchText = `${item.title} ${item.subtitle}`.toLowerCase();
	return searchText.includes(query.value.toLowerCase());
}

const visiblePinned = computed(() => {
	if (activeFilter.value === "Recent") {
		return [];
	}

	return pinnedItems.value.filter(
		(item) =>
			matchesSearch(item) && (activeFilter.value !== "ERP Documents" || item.erpDocument)
	);
});

const matchingRecent = computed(() => {
	if (activeFilter.value === "Pinned") {
		return [];
	}

	return recentItems.value.filter(
		(item) =>
			matchesSearch(item) && (activeFilter.value !== "ERP Documents" || item.erpDocument)
	);
});

const visibleRecent = computed(() =>
	showAllRecent.value ? matchingRecent.value : matchingRecent.value.slice(0, 3)
);

let copiedTimer;

async function copyItem(value) {
	try {
		await navigator.clipboard.writeText(value);
		copiedValue.value = value;
		window.clearTimeout(copiedTimer);
		copiedTimer = window.setTimeout(() => {
			copiedValue.value = "";
		}, 1400);
	} catch (error) {
		console.warn("Frappin could not copy this item.", error);
	}
}

async function callServer(method, args) {
	if (window.frappe?.call) {
		const response = await window.frappe.call({ method, args, silent: true });
		return response.message;
	}

	const csrfToken = window.csrf_token || window.frappe?.csrf_token;
	const response = await fetch(`/api/method/${method}`, {
		method: "POST",
		credentials: "same-origin",
		headers: {
			"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
			...(csrfToken ? { "X-Frappe-CSRF-Token": csrfToken } : {}),
		},
		body: new URLSearchParams(args),
	});
	if (!response.ok) {
		throw new Error(`Frappin request failed with status ${response.status}`);
	}
	return (await response.json()).message;
}

async function togglePin(item) {
	try {
		await callServer("frappin.api.set_item_pinned", {
			name: item.name,
			pinned: item.pinned ? 0 : 1,
		});
		await loadItems();
	} catch (error) {
		console.warn("Frappin could not update this pin.", error);
	}
}

async function editItem(item) {
	const content = window.prompt("Edit clipboard item", item.value);
	if (content === null || content.trim() === item.value) {
		return;
	}
	try {
		await callServer("frappin.api.update_clipboard_item", {
			name: item.name,
			content: content.trim(),
		});
		await loadItems();
	} catch (error) {
		console.warn("Frappin could not update this item.", error);
	}
}

async function deleteItem(item) {
	if (!window.confirm(`Delete “${item.title}”?`)) {
		return;
	}
	try {
		await callServer("frappin.api.delete_clipboard_item", { name: item.name });
		await loadItems();
	} catch (error) {
		console.warn("Frappin could not delete this item.", error);
	}
}

onMounted(() => {
	panelSize.value = constrainSize(panelSize.value.width, panelSize.value.height);
	loadItems();
	window.addEventListener("frappin:clipboard-saved", loadItems);
	nextTick(() => searchInput.value?.focus());
});

onBeforeUnmount(() => {
	stopResize();
	window.removeEventListener("frappin:clipboard-saved", loadItems);
});
</script>
