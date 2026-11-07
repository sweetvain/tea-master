const RARITY_LABELS = {
    legendaire: "Légendaire", epique: "Épique", rare: "Rare",
    mythique: "Mythique", goat: "GOAT", hess: "Hess"
};
const RARITY_STARS = { legendaire: "★", mythique: "★", goat: "★" };

function escapeHtml(value) {
    if (typeof value !== "string") return "";
    return value
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function rarityKey(card) {
    return (card.rarity || "rare").toLowerCase();
}

function makeModalCardEl(card) {
    const key = rarityKey(card);
    const div = document.createElement("div");
    div.className = `card ${key}`;
    div.style.pointerEvents = "none";

    const star = RARITY_STARS[key] ? `<div class="card-star">${RARITY_STARS[key]}</div>` : "";
    const photo = card.photo
        ? `<img src="${window.TEA_UPLOADS_URL}${encodeURIComponent(card.photo)}" alt="${escapeHtml(card.name)}" />`
        : `<div class="card-photo-initials">${escapeHtml(card.initials || (card.name || "?").slice(0, 2).toUpperCase())}</div>`;

    div.innerHTML = `
        ${key === "mythique" ? '<div class="mythique-border"></div>' : ""}
        ${key === "goat" ? '<div class="goat-border"></div>' : ""}
        <div class="card-photo">
            ${photo}
            <div class="card-photo-fade"></div>
        </div>
        <div class="card-top">
            <div class="rarity-badge">${RARITY_LABELS[key] || "Rare"}</div>
            ${star}
        </div>
        <div class="card-body">
            <div class="card-name">${escapeHtml(card.name || "?")}</div>
            <div class="card-role">${escapeHtml(card.role || "Sans rôle")}</div>
            <div class="card-desc">${escapeHtml(card.description || "")}</div>
        </div>
    `;
    return div;
}

function openCardModal(card) {
    const key = rarityKey(card);

    const wrap = document.getElementById("modal-card-el");
    wrap.innerHTML = "";
    wrap.appendChild(makeModalCardEl(card));

    document.getElementById("modal-card-info").innerHTML = `
        <div class="card-modal-rarity ${escapeHtml(key)}">${RARITY_LABELS[key] || "Rare"}</div>
        <div class="card-modal-name">${escapeHtml(card.name || "?")}</div>
        <div class="card-modal-role">${escapeHtml(card.role || "Sans rôle")}</div>
        <div class="card-modal-divider"></div>
        <div class="card-modal-desc">${escapeHtml(card.description || "Aucune description.")}</div>
    `;

    document.getElementById("card-modal-overlay").classList.add("open");
    document.body.style.overflow = "hidden";
}

function closeCardModal(event) {
    if (event && event.target.id !== "card-modal-overlay" && !event.target.closest(".card-modal-close")) {
        return;
    }
    document.getElementById("card-modal-overlay").classList.remove("open");
    document.body.style.overflow = "";
}

document.addEventListener("keydown", event => {
    if (event.key === "Escape") closeCardModal(null);
});
