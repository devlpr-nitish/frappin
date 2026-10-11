<template>
	<div class="frappin-widget">
		<Panel v-if="panelOpen" @close="panelOpen = false" />

		<button
			v-if="!panelOpen"
			ref="launcher"
			type="button"
			class="frappin-launcher"
			:class="{ 'is-dragging': dragging }"
			:style="launcherStyle"
			:aria-expanded="panelOpen"
			aria-controls="frappin-smart-clipboard"
			aria-label="Open Frappin. Drag to reposition."
			@click="togglePanel"
			@pointerdown="startDrag"
			@pointermove="moveLauncher"
			@pointerup="finishDrag"
			@pointercancel="finishDrag"
		>
			<img src="/assets/frappin/images/frappin-pin.svg?v=2" alt="" />
			<span>Frappin</span>
		</button>
	</div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import Panel from "./Panel.vue";

const POSITION_KEY = "frappin-launcher-position";
const panelOpen = ref(false);
const launcher = ref(null);
const launcherPosition = ref(loadPosition());
const dragging = ref(false);

let dragSession = null;
let suppressClick = false;
let originalClipboardWriteText = null;
let monitoredClipboardWriteText = null;

const launcherStyle = computed(() => {
	if (!launcherPosition.value) {
		return {};
	}

	return {
		left: `${launcherPosition.value.x}px`,
		top: `${launcherPosition.value.y}px`,
		right: "auto",
		bottom: "auto",
	};
});

function loadPosition() {
	try {
		const value = JSON.parse(localStorage.getItem(POSITION_KEY));
		return Number.isFinite(value?.x) && Number.isFinite(value?.y) ? value : null;
	} catch {
		return null;
	}
}

function clamp(value, minimum, maximum) {
	return Math.min(Math.max(value, minimum), Math.max(minimum, maximum));
}

function startDrag(event) {
	if (event.button !== 0) {
		return;
	}

	const rect = launcher.value.getBoundingClientRect();
	dragSession = {
		pointerId: event.pointerId,
		startX: event.clientX,
		startY: event.clientY,
		originX: rect.left,
		originY: rect.top,
		width: rect.width,
		height: rect.height,
		moved: false,
	};
	launcher.value.setPointerCapture(event.pointerId);
}

function moveLauncher(event) {
	if (!dragSession || dragSession.pointerId !== event.pointerId) {
		return;
	}

	const deltaX = event.clientX - dragSession.startX;
	const deltaY = event.clientY - dragSession.startY;
	if (!dragSession.moved && Math.hypot(deltaX, deltaY) < 4) {
		return;
	}

	dragSession.moved = true;
	dragging.value = true;
	launcherPosition.value = {
		x: clamp(dragSession.originX + deltaX, 8, window.innerWidth - dragSession.width - 8),
		y: clamp(dragSession.originY + deltaY, 8, window.innerHeight - dragSession.height - 8),
	};
}

function finishDrag(event) {
	if (!dragSession || dragSession.pointerId !== event.pointerId) {
		return;
	}

	if (dragSession.moved) {
		localStorage.setItem(POSITION_KEY, JSON.stringify(launcherPosition.value));
		suppressClick = true;
		window.setTimeout(() => {
			suppressClick = false;
		}, 0);
	}

	dragSession = null;
	dragging.value = false;
}

function togglePanel() {
	if (!suppressClick) {
		panelOpen.value = !panelOpen.value;
	}
}

function closeOnEscape(event) {
	if (event.key === "Escape") {
		panelOpen.value = false;
	}
}

function copiedText(event) {
	const target = event.target;
	if (
		(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement) &&
		target.selectionStart !== null &&
		target.selectionEnd !== null
	) {
		return target.value.slice(target.selectionStart, target.selectionEnd).trim();
	}
	return window.getSelection()?.toString().trim() || "";
}

function captureCopy(event) {
	persistCopiedText(copiedText(event));
}

function persistCopiedText(value) {
	const content = String(value || "").trim();
	if (!content) {
		return;
	}

	if (window.frappe?.call) {
		frappe.call({
			method: "frappin.api.save_clipboard_item",
			args: { content },
			silent: true,
			callback: () => window.dispatchEvent(new CustomEvent("frappin:clipboard-saved")),
		});
		return;
	}

	const csrfToken = window.csrf_token || window.frappe?.csrf_token;
	fetch("/api/method/frappin.api.save_clipboard_item", {
		method: "POST",
		credentials: "same-origin",
		headers: {
			"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
			...(csrfToken ? { "X-Frappe-CSRF-Token": csrfToken } : {}),
		},
		body: new URLSearchParams({ content }),
	})
		.then((response) => {
			if (response.ok) {
				window.dispatchEvent(new CustomEvent("frappin:clipboard-saved"));
			}
		})
		.catch((error) => console.warn("Frappin could not save copied text.", error));
}

function monitorProgrammaticCopies() {
	if (!navigator.clipboard?.writeText) {
		return;
	}

	originalClipboardWriteText = navigator.clipboard.writeText.bind(navigator.clipboard);
	monitoredClipboardWriteText = async (content) => {
		const result = await originalClipboardWriteText(content);
		persistCopiedText(content);
		return result;
	};

	try {
		navigator.clipboard.writeText = monitoredClipboardWriteText;
	} catch {
		originalClipboardWriteText = null;
		monitoredClipboardWriteText = null;
	}
}

function stopMonitoringProgrammaticCopies() {
	if (
		originalClipboardWriteText &&
		monitoredClipboardWriteText &&
		navigator.clipboard?.writeText === monitoredClipboardWriteText
	) {
		navigator.clipboard.writeText = originalClipboardWriteText;
	}
}

function keepLauncherInViewport() {
	if (!launcherPosition.value || !launcher.value) {
		return;
	}
	const rect = launcher.value.getBoundingClientRect();
	launcherPosition.value = {
		x: clamp(launcherPosition.value.x, 8, window.innerWidth - rect.width - 8),
		y: clamp(launcherPosition.value.y, 8, window.innerHeight - rect.height - 8),
	};
	localStorage.setItem(POSITION_KEY, JSON.stringify(launcherPosition.value));
}

onMounted(() => {
	document.addEventListener("keydown", closeOnEscape);
	document.addEventListener("copy", captureCopy);
	window.addEventListener("resize", keepLauncherInViewport);
	monitorProgrammaticCopies();
	keepLauncherInViewport();
});

onBeforeUnmount(() => {
	document.removeEventListener("keydown", closeOnEscape);
	document.removeEventListener("copy", captureCopy);
	window.removeEventListener("resize", keepLauncherInViewport);
	stopMonitoringProgrammaticCopies();
});
</script>
