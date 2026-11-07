const EMPTY_PENDING_HTML = '<p id="no-pending-msg" class="empty-msg">Aucune invitation reçue pour le moment.</p>';
const EMPTY_FRIENDS_HTML = '<p id="no-friends-msg" class="empty-msg">Tu n\'as pas encore d\'amis.</p>';

function postJson(url) {
    return fetch(url, { method: "POST" }).then(response => response.json());
}

function fadeOutAndRemove(element, animation, onDone) {
    gsap.to(element, {
        ...animation,
        onComplete: () => {
            element.remove();
            if (onDone) onDone();
        }
    });
}

function restoreIfEmpty(listId, html) {
    const list = document.getElementById(listId);
    if (list.children.length === 0) list.innerHTML = html;
}

function reloadSoon() {
    setTimeout(() => window.location.reload(), 1000);
}

function answerRequest(requestId, action) {
    const url = `/${action === "accept" ? "accept" : "reject"}_friend_request/${requestId}`;
    const box = document.getElementById(`req-box-${requestId}`);

    postJson(url)
        .then(data => {
            if (!data.success) return showNotification(data.error, "error");

            showNotification(data.message, "success");
            fadeOutAndRemove(box, { opacity: 0, x: -30, duration: 0.3 },
                () => restoreIfEmpty("pending-list", EMPTY_PENDING_HTML));
            if (action === "accept") reloadSoon();
        })
        .catch(() => showNotification("Erreur de connexion", "error"));
}

function sendRequestFromSuggest(username, box) {
    postJson(`/send_friend_request/${encodeURIComponent(username)}`)
        .then(data => {
            if (!data.success) return showNotification(data.error, "error");

            showNotification(data.message, "success");
            fadeOutAndRemove(box, { opacity: 0, y: -15, duration: 0.35 });
        })
        .catch(() => showNotification("Erreur de connexion", "error"));
}

function removeFriend(username, box) {
    if (!confirm(`Retirer ${username} de tes amis ?`)) return;

    postJson(`/remove_friend/${encodeURIComponent(username)}`)
        .then(data => {
            if (!data.success) return showNotification(data.error, "error");

            showNotification(data.message, "info");
            fadeOutAndRemove(box, { opacity: 0, scale: 0.9, duration: 0.3 },
                () => restoreIfEmpty("friends-list", EMPTY_FRIENDS_HTML));
            reloadSoon();
        })
        .catch(() => showNotification("Erreur de connexion", "error"));
}

document.addEventListener("click", event => {
    const button = event.target.closest("[data-action]");
    if (!button) return;

    const box = button.closest(".friend-item");
    const { action, requestId, username } = button.dataset;

    if (action === "accept" || action === "reject") answerRequest(requestId, action);
    else if (action === "add-friend") sendRequestFromSuggest(username, box);
    else if (action === "remove-friend") removeFriend(username, box);
});
