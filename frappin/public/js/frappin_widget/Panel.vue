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

		<div v-if="!creating && !sharingItem && !deletingItem" class="frappin-search-row">
			<label class="frappin-search">
				<svg viewBox="0 0 24 24" aria-hidden="true">
					<circle cx="11" cy="11" r="7" />
					<path d="m16 16 4 4" />
				</svg>
				<input ref="searchInput" v-model.trim="query" type="search" placeholder="Search your copied items..." />
			</label>
			<button
				type="button"
				class="frappin-create-button"
				aria-label="Create new item"
				title="Create new item"
				@click="openCreate"
			>
				<svg viewBox="0 0 24 24" aria-hidden="true">
					<path d="M12 5v14M5 12h14" />
				</svg>
			</button>
		</div>

		<div v-if="creating" class="frappin-create-view">
			<form class="frappin-create-dialog" aria-labelledby="frappin-create-title" @submit.prevent="saveItem">
				<div class="frappin-create-dialog__header">
					<h3 id="frappin-create-title">{{ editingItem ? "Edit clipboard item" : "New clipboard item" }}</h3>
					<button type="button" class="frappin-icon-button" aria-label="Close" @click="closeCreate">
						<svg viewBox="0 0 24 24" aria-hidden="true">
							<path d="m6 6 12 12M18 6 6 18" />
						</svg>
					</button>
				</div>
				<label>
					<span>Item type</span>
					<select v-model="newItemType" @change="changeItemType">
						<option value="text">Text</option>
						<option value="template">ERP template</option>
					</select>
				</label>
				<label>
					<span>Title <small>Optional</small></span>
					<input v-model.trim="newItemTitle" type="text" maxlength="140" placeholder="Item title" />
				</label>
				<label v-if="newItemType !== 'template'">
					<span>Content</span>
					<textarea
						ref="createContentInput"
						v-model="newItemContent"
						rows="6"
						required
						placeholder="Paste or type content..."
					></textarea>
				</label>
				<div v-else class="frappin-template-builder">
					<label>
						<span>Field source DocType</span>
						<input
							v-model.trim="templateDoctype"
							list="frappin-template-doctype-options"
							type="search"
							required
							autocomplete="off"
							placeholder="Search or select a DocType"
							@change="loadTemplateFields"
						/>
						<datalist id="frappin-template-doctype-options">
							<option v-for="doctype in templateDoctypes" :key="doctype" :value="doctype"></option>
						</datalist>
						<small>Used to choose fields. The template works on any form with matching field names.</small>
					</label>
					<div v-if="loadingTemplateFields" class="frappin-inline-loading">Loading fields…</div>
					<div v-else-if="templateDoctype" class="frappin-template-fields">
						<div class="frappin-template-fields__heading">
							<strong>Fields and values</strong>
							<button type="button" @click="addTemplateRow">+ Add field</button>
						</div>
						<p class="frappin-template-fields__hint">
							Child rows use paths such as <code>items[1].item_code</code> and <code>items[2].qty</code>.
						</p>
						<datalist id="frappin-template-field-options">
							<option v-for="field in templateFields" :key="field.fieldname" :value="field.fieldname">
								{{ field.label }}{{ field.reqd ? " *" : "" }}
							</option>
						</datalist>
						<div v-for="(row, index) in templateRows" :key="row.key" class="frappin-template-row">
							<input
								v-model.trim="row.fieldname"
								list="frappin-template-field-options"
								type="text"
								maxlength="140"
								aria-label="Template field name"
								placeholder="Field name"
							/>
							<select
								v-if="templateField(row.fieldname)?.fieldtype === 'Select'"
								v-model="row.value"
								aria-label="Template value"
							>
								<option value="">Choose value</option>
								<option v-for="option in templateFieldOptions(row.fieldname)" :key="option" :value="option">
									{{ option }}
								</option>
							</select>
							<label v-else-if="templateField(row.fieldname)?.fieldtype === 'Check'" class="frappin-template-check">
								<input v-model="row.value" type="checkbox" />
								<span>{{ row.value ? "Yes" : "No" }}</span>
							</label>
							<input v-else v-model="row.value" type="text" aria-label="Template value" placeholder="Value" />
							<button type="button" class="frappin-template-remove" aria-label="Remove field" @click="removeTemplateRow(index)">
								<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14" /></svg>
							</button>
						</div>
					</div>
				</div>
				<label v-if="collections.length">
					<span>Collection <small>Optional</small></span>
					<select v-model="newItemCollection">
						<option value="">No collection</option>
						<option v-for="collection in collections" :key="collection.name" :value="collection.name">
							{{ collection.title }}
						</option>
					</select>
				</label>
				<fieldset v-if="!editingItem || editingItem.is_owner" class="frappin-create-options">
					<legend>Item options</legend>
					<label class="frappin-option-check">
						<input v-model="newItemPinned" type="checkbox" />
						<span>Pin item</span>
					</label>
					<label class="frappin-option-check">
						<input v-model="newItemPermanent" type="checkbox" />
						<span>Permanent</span>
					</label>
				</fieldset>
				<ShareFields
					v-if="!editingItem || editingItem.is_owner"
					v-model:mode="createShareMode"
					v-model:selected-users="createShareUsers"
					v-model:allow-edit="createAllowEdit"
					v-model:allow-delete="createAllowDelete"
					:users="shareableUsers"
				/>
				<div class="frappin-create-dialog__actions">
					<button type="button" class="frappin-dialog-button" @click="closeCreate">Cancel</button>
					<button
						type="submit"
						class="frappin-dialog-button frappin-dialog-button--primary"
						:disabled="creatingItem || !canSaveItem"
					>
						{{ creatingItem ? "Saving…" : editingItem ? "Save changes" : "Save item" }}
					</button>
				</div>
			</form>
		</div>

		<div v-else-if="sharingItem" class="frappin-create-view">
			<form class="frappin-create-dialog" aria-labelledby="frappin-share-title" @submit.prevent="saveSharing">
				<div class="frappin-create-dialog__header">
					<div>
						<h3 id="frappin-share-title">Share item</h3>
						<p>{{ sharingItem.title }}</p>
					</div>
					<button type="button" class="frappin-icon-button" aria-label="Back" @click="closeSharing">
						<svg viewBox="0 0 24 24" aria-hidden="true">
							<path d="M19 12H5M11 18l-6-6 6-6" />
						</svg>
					</button>
				</div>
				<div v-if="loadingSharing" class="frappin-inline-loading">Loading sharing settings…</div>
				<ShareFields
					v-else
					v-model:mode="sharingMode"
					v-model:selected-users="sharingUsers"
					v-model:allow-edit="sharingAllowEdit"
					v-model:allow-delete="sharingAllowDelete"
					:users="shareableUsers"
				/>
				<div class="frappin-create-dialog__actions">
					<button type="button" class="frappin-dialog-button" @click="closeSharing">Cancel</button>
					<button
						type="submit"
						class="frappin-dialog-button frappin-dialog-button--primary"
						:disabled="savingShare || loadingSharing"
					>
						{{ savingShare ? "Saving…" : "Save sharing" }}
					</button>
				</div>
			</form>
		</div>

		<div v-else-if="deletingItem" class="frappin-create-view">
			<div class="frappin-create-dialog" role="alertdialog" aria-labelledby="frappin-delete-title">
				<div class="frappin-create-dialog__header">
					<h3 id="frappin-delete-title">Delete clipboard item?</h3>
				</div>
				<div class="frappin-delete-summary">
					<strong>{{ deletingItem.title }}</strong>
					<p>This item will be deleted permanently.</p>
				</div>
				<div class="frappin-create-dialog__actions">
					<button type="button" class="frappin-dialog-button" @click="closeDelete">Cancel</button>
					<button
						type="button"
						class="frappin-dialog-button frappin-dialog-button--delete"
						:disabled="deleting"
						@click="confirmDelete"
					>
						{{ deleting ? "Deleting…" : "Delete" }}
					</button>
				</div>
			</div>
		</div>

		<nav v-if="!creating && !sharingItem && !deletingItem" class="frappin-filters" aria-label="Clipboard filters">
			<button
				v-for="filter in filters"
				:key="filter.key"
				type="button"
				:class="{ 'is-active': activeFilter === filter.key }"
				@click="selectFilter(filter.key)"
			>
				{{ filter.label }}
			</button>
			<button
				v-if="!addingCollection"
				type="button"
				class="frappin-add-collection"
				@click="openCollectionCreate"
			>
				<span aria-hidden="true">+</span> Collection
			</button>
			<form v-else class="frappin-collection-create" @submit.prevent="createCollection">
				<input
					ref="collectionInput"
					v-model.trim="newCollectionTitle"
					type="text"
					maxlength="140"
					placeholder="Collection name"
					aria-label="Collection name"
					required
					@keydown.esc.prevent="closeCollectionCreate"
				/>
				<button type="submit" :disabled="savingCollection || !newCollectionTitle" aria-label="Save collection">
					<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6" /></svg>
				</button>
				<button type="button" :disabled="savingCollection" aria-label="Cancel" @click="closeCollectionCreate">
					<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18" /></svg>
				</button>
			</form>
		</nav>

		<div
			v-if="!creating && !sharingItem && !deletingItem"
			ref="panelContent"
			class="frappin-panel__content"
			@scroll.passive="handleContentScroll"
			@wheel.passive="handleContentWheel"
		>
			<div v-if="loading" class="frappin-empty">Loading your clipboard…</div>

			<section v-if="visiblePinned.length" class="frappin-section">
				<div class="frappin-section__heading">
					<h3>Pinned items</h3>
					<span>{{ visiblePinned.length }} {{ visiblePinned.length === 1 ? "item" : "items" }}</span>
				</div>

				<div class="frappin-pinned-list">
					<article v-for="item in visiblePinned" :key="item.id" class="frappin-pinned-card">
						<div class="frappin-item-icon">
							<svg v-if="item.icon === 'template'" viewBox="0 0 24 24" aria-hidden="true">
								<path d="M4 5h16v14H4zM4 9h16M9 9v10" />
							</svg>
							<svg v-else-if="item.icon === 'hash'" viewBox="0 0 24 24" aria-hidden="true">
								<path d="M10 3 8 21M16 3l-2 18M4 9h16M3 15h16" />
							</svg>
							<svg v-else viewBox="0 0 24 24" aria-hidden="true">
								<rect x="5" y="3" width="14" height="18" rx="2" />
								<path d="M9 8h6M9 12h5" />
							</svg>
						</div>
						<button
							type="button"
							class="frappin-item-copy"
							:class="{ 'is-template': item.isTemplate }"
							:draggable="item.isTemplate"
							:title="item.isTemplate ? 'Click or drag onto the form to apply' : 'Copy item'"
							@click="activateItem(item)"
							@dragstart="startTemplateDrag($event, item)"
							@dragend="finishTemplateDrag"
						>
							<strong>{{ item.title }}</strong>
							<span>{{ item.subtitle }}</span>
						</button>
						<ItemActions
							:item="item"
							:copied-value="copiedValue"
							@copy="copyItem"
							@pin="togglePin"
							@permanent="togglePermanent"
							@share="openSharing"
							@edit="editItem"
							@delete="deleteItem"
						/>
					</article>
				</div>
			</section>

			<section v-if="visibleRecent.length" class="frappin-section frappin-section--recent">
				<div class="frappin-section__heading">
					<h3>Recent clipboard</h3>
					<button type="button" @click="openFullList">View all</button>
				</div>

				<div class="frappin-recent-list">
					<article v-for="item in visibleRecent" :key="item.id" class="frappin-recent-row">
						<div class="frappin-item-icon">
							<svg v-if="item.icon === 'template'" viewBox="0 0 24 24" aria-hidden="true">
								<path d="M4 5h16v14H4zM4 9h16M9 9v10" />
							</svg>
							<svg v-else-if="item.icon === 'box'" viewBox="0 0 24 24" aria-hidden="true">
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
						<button
							type="button"
							class="frappin-item-copy"
							:class="{ 'is-template': item.isTemplate }"
							:draggable="item.isTemplate"
							:title="item.isTemplate ? 'Click or drag onto the form to apply' : 'Copy item'"
							@click="activateItem(item)"
							@dragstart="startTemplateDrag($event, item)"
							@dragend="finishTemplateDrag"
						>
							<strong>{{ item.title }}</strong>
							<span>{{ item.subtitle }}</span>
						</button>
						<ItemActions
							:item="item"
							:copied-value="copiedValue"
							@copy="copyItem"
							@pin="togglePin"
							@permanent="togglePermanent"
							@share="openSharing"
							@edit="editItem"
							@delete="deleteItem"
						/>
					</article>
				</div>
			</section>

			<div v-if="!loading && !visiblePinned.length && !visibleRecent.length" class="frappin-empty">
				No clipboard items found.
			</div>
			<div v-if="loadingMore" class="frappin-list-loading">Loading more…</div>
		</div>


	</section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import ItemActions from "./ItemActions.vue";
import ShareFields from "./ShareFields.vue";

const emit = defineEmits(["close"]);

const baseFilters = [
	{ key: "all", label: "All" },
	{ key: "pinned", label: "Pinned" },
	{ key: "recent", label: "Recent" },
	{ key: "erp_documents", label: "ERP Documents" },
];
const activeFilter = ref("all");
const query = ref("");
const panelPinned = ref(false);
const copiedValue = ref("");
const searchInput = ref(null);
const panelContent = ref(null);
const resizing = ref(false);
const loading = ref(true);
const loadingMore = ref(false);
const hasMore = ref(true);
const nextStart = ref(0);
const items = ref([]);
const collections = ref([]);
const addingCollection = ref(false);
const savingCollection = ref(false);
const newCollectionTitle = ref("");
const collectionInput = ref(null);
const creating = ref(false);
const creatingItem = ref(false);
const editingItem = ref(null);
const deletingItem = ref(null);
const deleting = ref(false);
const newItemTitle = ref("");
const newItemContent = ref("");
const newItemType = ref("text");
const newItemCollection = ref("");
const newItemPinned = ref(false);
const newItemPermanent = ref(false);
const createContentInput = ref(null);
const shareableUsers = ref([]);
const createShareMode = ref("private");
const createShareUsers = ref([]);
const createAllowEdit = ref(false);
const createAllowDelete = ref(false);
const sharingItem = ref(null);
const sharingMode = ref("private");
const sharingUsers = ref([]);
const sharingAllowEdit = ref(false);
const sharingAllowDelete = ref(false);
const loadingSharing = ref(false);
const savingShare = ref(false);
const templateDoctypes = ref([]);
const templateDoctype = ref("");
const templateFields = ref([]);
let templateRowKey = 1;
const templateRows = ref([newTemplateRow()]);
const loadingTemplateFields = ref(false);
let draggedTemplate = null;
let highlightedDropTarget = null;

const SIZE_KEY = "frappin-panel-size";
const panelSize = ref(loadPanelSize());
let resizeSession = null;

const panelStyle = computed(() => ({
	"--frappin-panel-width": `${panelSize.value.width}px`,
	"--frappin-panel-height": `${panelSize.value.height}px`,
}));

const canSaveItem = computed(() => {
	if (newItemType.value !== "template") {
		return Boolean(newItemContent.value.trim());
	}
	return Boolean(templateDoctype.value && validTemplateRows().length);
});

function newTemplateRow(fieldname = "", value = "") {
	return { key: templateRowKey++, fieldname, value };
}

const filters = computed(() => [
	...baseFilters,
	...collections.value.map((collection) => ({
		key: `collection:${collection.name}`,
		label: collection.title,
	})),
]);

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
	if (item.content_type === "template") {
		return `${item.source_doctype || "ERP"} template`;
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
	const isTemplate = item.content_type === "template";
	const typeLabel = isTemplate
		? `Field template · ${item.source_doctype} fields · Click or drag to apply`
		: erpDocument
		? `${item.source_doctype}${item.source_name ? ` · ${item.source_name}` : ""}`
		: item.content_type === "url"
			? "URL"
			: "Copied text";
	return {
		...item,
		id: item.name,
		rawTitle: item.title || "",
		title: displayTitle(item),
		subtitle: `${typeLabel} · ${relativeTime(item.last_used_at || item.creation)}`,
		value: item.content,
		icon: isTemplate ? "template" : erpDocument ? "hash" : item.content.includes("@") ? "mail" : "note",
		erpDocument,
		isTemplate,
	};
}

async function loadItems(reset = true) {
	if ((!reset && (!hasMore.value || loadingMore.value)) || (reset && loading.value && items.value.length)) {
		return;
	}
	if (reset) {
		loading.value = true;
		hasMore.value = true;
		nextStart.value = 0;
	} else {
		loadingMore.value = true;
	}
	try {
		const collection = activeFilter.value.startsWith("collection:")
			? activeFilter.value.slice("collection:".length)
			: "";
		const filterType = collection ? "all" : activeFilter.value;
		const params = new URLSearchParams({
			limit: "5",
			start: String(nextStart.value),
			filter_type: filterType,
			...(collection ? { collection } : {}),
		});
		const response = await fetch(`/api/method/frappin.api.clipboard.get_clipboard_items?${params}`, {
			headers: { Accept: "application/json" },
			credentials: "same-origin",
		});
		const payload = await response.json();
		if (response.ok) {
			const result = payload.message || {};
			const pageItems = (result.items || []).map(presentItem);
			if (reset) {
				items.value = pageItems;
			} else {
				const knownNames = new Set(items.value.map((item) => item.name));
				items.value.push(...pageItems.filter((item) => !knownNames.has(item.name)));
			}
			hasMore.value = Boolean(result.has_more);
			nextStart.value = result.next_start ?? nextStart.value + 5;
		}
	} catch (error) {
		console.warn("Frappin could not load clipboard items.", error);
	} finally {
		loading.value = false;
		loadingMore.value = false;
	}
}

async function loadCollections() {
	try {
		collections.value = (await callServer("frappin.api.clipboard.get_collections", {})) || [];
	} catch (error) {
		console.warn("Frappin could not load collections.", error);
	}
}

function openCollectionCreate() {
	addingCollection.value = true;
	nextTick(() => collectionInput.value?.focus());
}

function closeCollectionCreate() {
	if (savingCollection.value) return;
	addingCollection.value = false;
	newCollectionTitle.value = "";
}

async function createCollection() {
	const title = newCollectionTitle.value.trim();
	if (!title || savingCollection.value) return;
	savingCollection.value = true;
	try {
		const collection = await callServer("frappin.api.clipboard.create_collection", { title });
		await loadCollections();
		addingCollection.value = false;
		newCollectionTitle.value = "";
		if (collection?.name) {
			activeFilter.value = `collection:${collection.name}`;
			await loadItems(true);
		}
	} catch (error) {
		console.warn("Frappin could not create this collection.", error);
	} finally {
		savingCollection.value = false;
	}
}

function selectFilter(filter) {
	if (activeFilter.value === filter) {
		return;
	}
	activeFilter.value = filter;
	loadItems(true);
}

function isAtListBottom() {
	const element = panelContent.value;
	return element && element.scrollTop + element.clientHeight >= element.scrollHeight - 40;
}

function handleContentScroll() {
	if (isAtListBottom()) {
		loadItems(false);
	}
}

function handleContentWheel(event) {
	if (event.deltaY > 0 && isAtListBottom()) {
		loadItems(false);
	}
}

function openFullList() {
	emit("close");
	if (window.frappe?.set_route) {
		window.frappe.set_route("List", "Frappin Clipboard Item");
		return;
	}
	window.location.assign("/app/frappin-clipboard-item");
}

function matchesSearch(item) {
	if (!query.value) {
		return true;
	}

	const searchText = `${item.title} ${item.subtitle}`.toLowerCase();
	return searchText.includes(query.value.toLowerCase());
}

const visiblePinned = computed(() => {
	return pinnedItems.value.filter(matchesSearch);
});

const matchingRecent = computed(() => {
	return recentItems.value.filter(matchesSearch);
});

const visibleRecent = computed(() => matchingRecent.value);

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

function showMessage(message, indicator = "blue") {
	if (window.frappe?.show_alert) {
		window.frappe.show_alert({ message, indicator }, 5);
	} else {
		console.info(message);
	}
}

function parseTemplate(item) {
	try {
		const values = JSON.parse(item.value || item.content || "{}");
		return values && typeof values === "object" && !Array.isArray(values) ? values : null;
	} catch {
		return null;
	}
}

function parseChildFieldPath(fieldname) {
	const match = /^([A-Za-z_][A-Za-z0-9_]*)\[([1-9][0-9]{0,2})\]\.([A-Za-z_][A-Za-z0-9_]*)$/.exec(
		fieldname
	);
	return match ? { tableFieldname: match[1], rowIndex: Number(match[2]), fieldname: match[3] } : null;
}

function isWritableField(field) {
	return Boolean(
		field &&
			!field.df?.read_only &&
			!field.df?.hidden &&
			(typeof field.get_status !== "function" || field.get_status() === "Write")
	);
}

async function applyTemplate(item) {
	const frm = window.cur_frm;
	if (!frm?.doc) {
		showMessage("Open a DocType form to apply this template.", "orange");
		return false;
	}
	if (Number(frm.doc.docstatus || 0) !== 0) {
		showMessage("Only draft forms can be filled from a template.", "orange");
		return false;
	}

	const values = parseTemplate(item);
	if (!values) {
		showMessage("This template has invalid field values.", "red");
		return false;
	}

	let applied = 0;
	let failed = 0;
	const childTables = new Map();
	for (const [fieldname, value] of Object.entries(values)) {
		const childPath = parseChildFieldPath(fieldname);
		if (childPath) {
			const tableField = frm.fields_dict?.[childPath.tableFieldname];
			if (!isWritableField(tableField) || tableField.df?.fieldtype !== "Table") {
				continue;
			}
			const childField = window.frappe?.get_meta?.(tableField.df.options)?.fields?.find(
				(field) => field.fieldname === childPath.fieldname
			);
			if (!childField || childField.read_only || childField.hidden || childField.fieldtype === "Table") {
				continue;
			}
			if (!childTables.has(childPath.tableFieldname)) {
				childTables.set(childPath.tableFieldname, new Map());
			}
			const rows = childTables.get(childPath.tableFieldname);
			if (!rows.has(childPath.rowIndex)) rows.set(childPath.rowIndex, {});
			rows.get(childPath.rowIndex)[childPath.fieldname] = value;
			continue;
		}
		const field = frm.fields_dict?.[fieldname];
		if (!isWritableField(field) || field.df?.fieldtype === "Table") {
			continue;
		}
		try {
			await frm.set_value(fieldname, value);
			applied += 1;
		} catch (error) {
			failed += 1;
			console.warn(`Frappin could not apply the ${fieldname} template field.`, error);
		}
	}
	for (const [tableFieldname, indexedRows] of childTables) {
		const rows = [...indexedRows.entries()]
			.sort(([left], [right]) => left - right)
			.map(([, row]) => row);
		try {
			await frm.set_value(tableFieldname, rows);
			applied += rows.reduce((count, row) => count + Object.keys(row).length, 0);
		} catch (error) {
			failed += rows.reduce((count, row) => count + Object.keys(row).length, 0);
			console.warn(`Frappin could not apply the ${tableFieldname} child table.`, error);
		}
	}

	if (!applied) {
		showMessage("No editable fields from this template exist on the open form.", "orange");
		return false;
	}
	frm.dirty?.();
	showMessage(
		`${item.title}: ${applied} matching ${applied === 1 ? "field" : "fields"} applied to ${frm.doc.doctype}${
			failed ? `; ${failed} skipped` : ""
		}.`,
		"green"
	);
	emit("close");
	return true;
}

function activateItem(item) {
	if (item.isTemplate) {
		applyTemplate(item);
		return;
	}
	copyItem(item.value);
}

function startTemplateDrag(event, item) {
	if (!item.isTemplate) {
		event.preventDefault();
		return;
	}
	draggedTemplate = item;
	event.dataTransfer.effectAllowed = "copy";
	event.dataTransfer.setData("application/x-frappin-template", item.name);
	event.dataTransfer.setData("text/plain", item.title);
}

function clearDropTarget() {
	highlightedDropTarget?.classList.remove("frappin-template-drop-target");
	highlightedDropTarget = null;
}

function findFormDropTarget(target) {
	if (!(target instanceof Element) || target.closest("#frappin-smart-clipboard")) {
		return null;
	}
	return target.closest(".form-layout, .form-page, .layout-main-section");
}

function handleTemplateDragOver(event) {
	if (!draggedTemplate || !window.cur_frm?.doc) {
		clearDropTarget();
		return;
	}
	const target = findFormDropTarget(event.target);
	if (!target) {
		clearDropTarget();
		return;
	}
	event.preventDefault();
	event.dataTransfer.dropEffect = "copy";
	if (highlightedDropTarget !== target) {
		clearDropTarget();
		highlightedDropTarget = target;
		target.classList.add("frappin-template-drop-target");
	}
}

function handleTemplateDrop(event) {
	if (!draggedTemplate || !findFormDropTarget(event.target)) {
		return;
	}
	event.preventDefault();
	const item = draggedTemplate;
	finishTemplateDrag();
	applyTemplate(item);
}

function finishTemplateDrag() {
	draggedTemplate = null;
	clearDropTarget();
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

async function loadShareableUsers() {
	if (shareableUsers.value.length) {
		return;
	}
	try {
		shareableUsers.value = (await callServer("frappin.api.clipboard.get_shareable_users", {})) || [];
	} catch (error) {
		console.warn("Frappin could not load users for sharing.", error);
	}
}

function openCreate() {
	editingItem.value = null;
	creating.value = true;
	newItemType.value = "text";
	templateDoctype.value = "";
	templateFields.value = [];
	templateRows.value = [newTemplateRow()];
	createShareMode.value = "private";
	createShareUsers.value = [];
	createAllowEdit.value = false;
	createAllowDelete.value = false;
	loadShareableUsers();
	loadTemplateDoctypes();
	nextTick(() => createContentInput.value?.focus());
}

function closeCreate() {
	if (creatingItem.value) {
		return;
	}
	creating.value = false;
	editingItem.value = null;
	newItemTitle.value = "";
	newItemContent.value = "";
	newItemType.value = "text";
	newItemCollection.value = "";
	newItemPinned.value = false;
	newItemPermanent.value = false;
	createShareMode.value = "private";
	createShareUsers.value = [];
	createAllowEdit.value = false;
	createAllowDelete.value = false;
	templateDoctype.value = "";
	templateFields.value = [];
	templateRows.value = [newTemplateRow()];
}

async function loadTemplateDoctypes() {
	if (templateDoctypes.value.length) return;
	try {
		templateDoctypes.value = (await callServer("frappin.api.clipboard.get_template_doctypes", {})) || [];
	} catch (error) {
		console.warn("Frappin could not load ERP DocTypes.", error);
	}
}

async function loadTemplateFields() {
	templateFields.value = [];
	templateRows.value = [newTemplateRow()];
	if (!templateDoctype.value) return;
	loadingTemplateFields.value = true;
	try {
		templateFields.value =
			(await callServer("frappin.api.clipboard.get_template_fields", {
				doctype: templateDoctype.value,
			})) || [];
	} catch (error) {
		console.warn("Frappin could not load fields for this DocType.", error);
	} finally {
		loadingTemplateFields.value = false;
	}
}

function changeItemType() {
	if (newItemType.value === "template") {
		loadTemplateDoctypes();
	}
}

function templateField(fieldname) {
	return templateFields.value.find((field) => field.fieldname === fieldname);
}

function templateFieldOptions(fieldname) {
	return (templateField(fieldname)?.options || "")
		.split("\n")
		.map((option) => option.trim())
		.filter(Boolean);
}

function addTemplateRow() {
	templateRows.value.push(newTemplateRow());
}

function removeTemplateRow(index) {
	templateRows.value.splice(index, 1);
	if (!templateRows.value.length) templateRows.value.push(newTemplateRow());
}

function validTemplateRows() {
	return templateRows.value.filter((row) => row.fieldname && row.value !== "" && row.value !== null);
}

function serializeTemplate() {
	return JSON.stringify(Object.fromEntries(validTemplateRows().map((row) => [row.fieldname, row.value])));
}

async function saveItem() {
	const content = newItemType.value === "template" ? serializeTemplate() : newItemContent.value.trim();
	if (!content || creatingItem.value) {
		return;
	}

	creatingItem.value = true;
	try {
		if (editingItem.value) {
			await callServer("frappin.api.clipboard.update_clipboard_item", {
				name: editingItem.value.name,
				content,
				title: newItemTitle.value.trim(),
				collection: newItemCollection.value,
				content_type:
					newItemType.value === "template" ? "template" : editingItem.value.content_type || "",
				source_doctype: newItemType.value === "template" ? templateDoctype.value : "",
			});
			if (editingItem.value.is_owner) {
				await callServer("frappin.api.clipboard.set_item_pinned", {
					name: editingItem.value.name,
					pinned: newItemPinned.value ? 1 : 0,
				});
				await callServer("frappin.api.clipboard.set_item_permanent", {
					name: editingItem.value.name,
					permanent: newItemPermanent.value ? 1 : 0,
				});
				await callServer("frappin.api.clipboard.set_item_sharing", {
					name: editingItem.value.name,
					share_mode: createShareMode.value,
					users: JSON.stringify(createShareUsers.value),
					allow_edit: createAllowEdit.value ? 1 : 0,
					allow_delete: createAllowDelete.value ? 1 : 0,
				});
			}
		} else {
			await callServer("frappin.api.clipboard.save_clipboard_item", {
				content,
				title: newItemTitle.value.trim(),
				collection: newItemCollection.value,
				content_type: newItemType.value === "template" ? "template" : "",
				source_doctype: newItemType.value === "template" ? templateDoctype.value : "",
				pinned: newItemPinned.value ? 1 : 0,
				permanent: newItemPermanent.value ? 1 : 0,
				share_mode: createShareMode.value,
				users: JSON.stringify(createShareUsers.value),
				allow_edit: createAllowEdit.value ? 1 : 0,
				allow_delete: createAllowDelete.value ? 1 : 0,
			});
		}
		creating.value = false;
		editingItem.value = null;
		newItemTitle.value = "";
		newItemContent.value = "";
		newItemType.value = "text";
		newItemCollection.value = "";
		newItemPinned.value = false;
		newItemPermanent.value = false;
		createShareMode.value = "private";
		createShareUsers.value = [];
		createAllowEdit.value = false;
		createAllowDelete.value = false;
		await loadItems();
	} catch (error) {
		console.warn("Frappin could not create this item.", error);
	} finally {
		creatingItem.value = false;
	}
}

async function openSharing(item) {
	sharingItem.value = item;
	loadingSharing.value = true;
	await loadShareableUsers();
	try {
		const sharing = await callServer("frappin.api.clipboard.get_item_sharing", { name: item.name });
		sharingMode.value = sharing?.mode || "private";
		sharingUsers.value = sharing?.users || [];
		sharingAllowEdit.value = Boolean(sharing?.allow_edit);
		sharingAllowDelete.value = Boolean(sharing?.allow_delete);
	} catch (error) {
		console.warn("Frappin could not load sharing settings.", error);
		sharingItem.value = null;
	} finally {
		loadingSharing.value = false;
	}
}

function closeSharing() {
	if (savingShare.value) {
		return;
	}
	sharingItem.value = null;
	sharingMode.value = "private";
	sharingUsers.value = [];
	sharingAllowEdit.value = false;
	sharingAllowDelete.value = false;
}

async function saveSharing() {
	if (!sharingItem.value || savingShare.value) {
		return;
	}
	savingShare.value = true;
	try {
		await callServer("frappin.api.clipboard.set_item_sharing", {
			name: sharingItem.value.name,
			share_mode: sharingMode.value,
			users: JSON.stringify(sharingUsers.value),
			allow_edit: sharingAllowEdit.value ? 1 : 0,
			allow_delete: sharingAllowDelete.value ? 1 : 0,
		});
		sharingItem.value = null;
		sharingMode.value = "private";
		sharingUsers.value = [];
		sharingAllowEdit.value = false;
		sharingAllowDelete.value = false;
		await loadItems();
	} catch (error) {
		console.warn("Frappin could not update sharing.", error);
	} finally {
		savingShare.value = false;
	}
}

async function togglePin(item) {
	try {
		await callServer("frappin.api.clipboard.set_item_pinned", {
			name: item.name,
			pinned: item.pinned ? 0 : 1,
		});
		await loadItems();
	} catch (error) {
		console.warn("Frappin could not update this pin.", error);
	}
}

async function togglePermanent(item) {
	try {
		await callServer("frappin.api.clipboard.set_item_permanent", {
			name: item.name,
			permanent: item.permanent ? 0 : 1,
		});
		await loadItems();
	} catch (error) {
		console.warn("Frappin could not update permanent storage for this item.", error);
	}
}

async function editItem(item) {
	editingItem.value = item;
	newItemTitle.value = item.rawTitle || "";
	newItemContent.value = item.value;
	newItemType.value = item.content_type === "template" ? "template" : "text";
	newItemCollection.value = item.collection || "";
	newItemPinned.value = Boolean(item.pinned);
	newItemPermanent.value = Boolean(item.permanent);
	createShareMode.value = "private";
	createShareUsers.value = [];
	createAllowEdit.value = false;
	createAllowDelete.value = false;
	creating.value = true;
	if (newItemType.value === "template") {
		templateDoctype.value = item.source_doctype || "";
		await loadTemplateDoctypes();
		loadingTemplateFields.value = true;
		try {
			templateFields.value =
				(await callServer("frappin.api.clipboard.get_template_fields", {
					doctype: templateDoctype.value,
				})) || [];
			const values = parseTemplate(item) || {};
			templateRows.value = Object.entries(values).map(([fieldname, value]) =>
				newTemplateRow(fieldname, value)
			);
			if (!templateRows.value.length) templateRows.value = [newTemplateRow()];
		} finally {
			loadingTemplateFields.value = false;
		}
	}

	if (item.is_owner) {
		await loadShareableUsers();
		try {
			const sharing = await callServer("frappin.api.clipboard.get_item_sharing", { name: item.name });
			createShareMode.value = sharing?.mode || "private";
			createShareUsers.value = sharing?.users || [];
			createAllowEdit.value = Boolean(sharing?.allow_edit);
			createAllowDelete.value = Boolean(sharing?.allow_delete);
		} catch (error) {
			console.warn("Frappin could not load sharing settings for editing.", error);
		}
	}
	nextTick(() => createContentInput.value?.focus());
}

function deleteItem(item) {
	deletingItem.value = item;
}

function closeDelete() {
	if (deleting.value) {
		return;
	}
	deletingItem.value = null;
}

async function confirmDelete() {
	if (!deletingItem.value || deleting.value) {
		return;
	}
	deleting.value = true;
	try {
		await callServer("frappin.api.clipboard.delete_clipboard_item", { name: deletingItem.value.name });
		deletingItem.value = null;
		await loadItems();
	} catch (error) {
		console.warn("Frappin could not delete this item.", error);
	} finally {
		deleting.value = false;
	}
}

onMounted(() => {
	panelSize.value = constrainSize(panelSize.value.width, panelSize.value.height);
	loadItems();
	loadCollections();
	window.addEventListener("frappin:clipboard-saved", loadItems);
	document.addEventListener("dragover", handleTemplateDragOver);
	document.addEventListener("drop", handleTemplateDrop);
	nextTick(() => searchInput.value?.focus());
});

onBeforeUnmount(() => {
	stopResize();
	window.removeEventListener("frappin:clipboard-saved", loadItems);
	document.removeEventListener("dragover", handleTemplateDragOver);
	document.removeEventListener("drop", handleTemplateDrop);
	finishTemplateDrag();
});
</script>
