document.addEventListener("DOMContentLoaded", () => {
    gsap.from(".cyber-header", { y: -80, opacity: 0, duration: 0.8, ease: "power4.out" });

    document.querySelectorAll(".cyber-nav-link").forEach(link => {
        link.addEventListener("mouseenter", () => {
            gsap.to(link, { scale: 1.05, duration: 0.2, ease: "power2.out" });
        });
        link.addEventListener("mouseleave", () => {
            gsap.to(link, { scale: 1, duration: 0.2, ease: "power2.out" });
        });
    });

    const usernameInput = document.getElementById("modal-friend-username");
    if (usernameInput) {
        usernameInput.addEventListener("keydown", event => {
            if (event.key === "Enter") submitInviteFromModal();
        });
    }
});

// Précharge la page au survol / au toucher : la navigation devient quasi instantanée.
(function prefetchOnIntent() {
    const seen = new Set();
    const prefetch = event => {
        const link = event.target.closest && event.target.closest("a[href]");
        if (!link || link.origin !== location.origin || link.pathname === location.pathname) return;
        if (link.pathname === "/logout" || seen.has(link.href)) return;
        seen.add(link.href);
        const tag = document.createElement("link");
        tag.rel = "prefetch";
        tag.href = link.href;
        document.head.appendChild(tag);
    };
    document.addEventListener("pointerenter", prefetch, { capture: true, passive: true });
    document.addEventListener("touchstart", prefetch, { passive: true });
})();

const TOAST_INDICATORS = { success: "✔ Super !", error: "✘ Oups", info: "✦ Info" };

function showNotification(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast-card ${type}`;

    const wrapper = document.createElement("div");
    const indicator = document.createElement("strong");
    indicator.style.cssText = "display:block; font-size:10px; opacity:0.5; letter-spacing:1px; margin-bottom:2px;";
    indicator.textContent = TOAST_INDICATORS[type] || TOAST_INDICATORS.info;
    const text = document.createElement("span");
    text.textContent = message;
    wrapper.append(indicator, text);
    toast.appendChild(wrapper);
    container.appendChild(toast);

    gsap.fromTo(toast,
        { x: 150, opacity: 0, scale: 0.9, skewX: -10 },
        { x: 0, opacity: 1, scale: 1, skewX: 0, duration: 0.4, ease: "back.out(1.2)" }
    );
    gsap.to(toast, {
        x: 100, opacity: 0, scale: 0.9, delay: 4.5, duration: 0.3, ease: "power3.in",
        onComplete: () => toast.remove()
    });
}

function openInviteModal(event) {
    if (event) event.preventDefault();
    document.getElementById("invite-modal").classList.add("open");
    document.getElementById("modal-friend-username").focus();
}

function closeInviteModal(event) {
    if (!event || event.target.id === "invite-modal") {
        document.getElementById("invite-modal").classList.remove("open");
        document.getElementById("modal-friend-username").value = "";
    }
}

function submitInviteFromModal() {
    const username = document.getElementById("modal-friend-username").value.trim();

    if (!username) {
        showNotification("Entre le pseudo de ton ami.", "error");
        return;
    }

    fetch(`/send_friend_request/${encodeURIComponent(username)}`, { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, "success");
                closeInviteModal(null);
                if (window.location.pathname === "/profile") {
                    setTimeout(() => window.location.reload(), 1000);
                }
            } else {
                showNotification((data.error || "Une erreur est survenue"), "error");
            }
        })
        .catch(() => showNotification("Connexion impossible, réessaie.", "error"));
}
