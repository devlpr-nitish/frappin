import { createApp } from "vue";
import Widget from "./frappin_widget/Widget.vue";

(() => {
	if (window.__frappinWidgetBooted || window.__frappinWidgetBooting) {
		return;
	}

	async function mountWidget() {
		if (window.__frappinWidgetBooted || window.__frappinWidgetBooting) {
			return;
		}

		window.__frappinWidgetBooting = true;

		try {
			const response = await fetch("/api/method/frappin.api.get_widget_settings", {
				headers: { Accept: "application/json" },
				credentials: "same-origin",
			});
			const payload = await response.json();
			if (!response.ok || !payload.message?.enabled) {
				return;
			}

			window.__frappinWidgetBooted = true;

			const host = document.createElement("div");
			host.id = "frappin-widget-host";
			document.body.appendChild(host);

			createApp(Widget).mount(host);
		} catch (error) {
			console.warn("Frappin could not load its settings.", error);
		} finally {
			window.__frappinWidgetBooting = false;
		}
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", mountWidget, { once: true });
	} else {
		mountWidget();
	}
})();
