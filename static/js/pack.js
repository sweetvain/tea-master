/* Page paquets : déchirure du paquet au geste, puis éventail de cartes à choisir et retourner. */
(() => {
    if (!window.gsap) return; // sans GSAP, le formulaire classique (/pull) prend le relais

    const $ = id => document.getElementById(id);
    const stage = $("pack-stage");
    const form = $("pack-form");
    const wrap = $("pack-wrap");
    const pack = $("pack");
    const tilt = $("pack-tilt");
    const topEl = $("pack-top");
    const mainEl = $("pack-main");
    const tearEl = $("pack-tear");
    const hint = $("pack-hint");
    const openBtn = $("open-btn");
    const reveal = $("reveal");
    const fan = $("fan");
    const actions = $("reveal-actions");
    const revealAllBtn = $("reveal-all");
    const done = $("reveal-done");
    const againBtn = $("again-btn");
    const packsCount = $("packs-count");

    const reduceMotion = TeaFX.reduceMotion;
    const canTilt = window.matchMedia("(hover: hover)").matches && !reduceMotion;

    const CARD_W = 266;
    const CARD_H = 355;
    const TEAR_DISTANCE = 170;
    const RARITIES = {
        hess:       { label: "Hess",       color: "#8a8a9a", tier: 0 },
        rare:       { label: "Rare",       color: "#4a9eff", tier: 1 },
        epique:     { label: "Épique",     color: "#b06bff", tier: 2 },
        legendaire: { label: "Légendaire", color: "#ffb830", tier: 3 },
        mythique:   { label: "Mythique",   color: "#ff2d55", tier: 4 },
        goat:       { label: "GOAT",       color: "#39ff6a", tier: 5 }
    };
    const BURST_COUNT = [14, 26, 42, 72, 110, 150];

    const state = {
        packs: parseInt(stage.dataset.packs, 10) || 0,
        opening: false,
        dir: 1,
        slots: [],
        revealed: 0
    };

    const clamp = (v, min, max) => Math.min(max, Math.max(min, v));
    const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
    const notify = (message, type) => typeof showNotification === "function" && showNotification(message, type);

    function rarityInfo(card) {
        const key = (card.rarity || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
        return RARITIES[key] || RARITIES.rare;
    }

    /* ---------------------------------------------------------------
       Paquet : inclinaison 3D + reflet holographique
       --------------------------------------------------------------- */
    let dragging = null;

    if (canTilt) {
        const toRX = gsap.quickTo(tilt, "rotationX", { duration: 0.45, ease: "power3" });
        const toRY = gsap.quickTo(tilt, "rotationY", { duration: 0.45, ease: "power3" });
        let pending = null;
        let scheduled = false;

        function applyTilt() {
            scheduled = false;
            if (!pending || dragging || state.opening) return;
            const rect = pack.getBoundingClientRect();
            const x = clamp((pending.x - rect.left) / rect.width, 0, 1);
            const y = clamp((pending.y - rect.top) / rect.height, 0, 1);
            toRY((x - 0.5) * 26);
            toRX(-(y - 0.5) * 22);
            tilt.style.setProperty("--mx", (x * 100).toFixed(1) + "%");
            tilt.style.setProperty("--my", (y * 100).toFixed(1) + "%");
            tilt.style.setProperty("--px", ((x - 0.5) * 2).toFixed(2));
            tilt.style.setProperty("--py", ((y - 0.5) * 2).toFixed(2));
            tilt.style.setProperty("--shine", "0.5");
        }

        pack.addEventListener("pointermove", event => {
            pending = { x: event.clientX, y: event.clientY };
            if (!scheduled) {
                scheduled = true;
                requestAnimationFrame(applyTilt);
            }
        });
        pack.addEventListener("pointerleave", () => {
            pending = null;
            if (state.opening) return;
            toRX(0);
            toRY(0);
            tilt.style.setProperty("--shine", "0.22");
        });
    }

    /* ---------------------------------------------------------------
       Déchirure au geste
       --------------------------------------------------------------- */
    function setTear(progress, dir) {
        const origin = dir > 0 ? "0% 100%" : "100% 100%";
        gsap.set(topEl, {
            rotation: -dir * progress * 9,
            x: dir * progress * 20,
            y: -progress * 12,
            transformOrigin: origin
        });
        gsap.set(tearEl, {
            opacity: Math.min(1, progress * 3),
            scaleX: progress,
            transformOrigin: dir > 0 ? "0% 50%" : "100% 50%"
        });
        gsap.set(tilt, { rotationY: dir * progress * 12, rotationZ: dir * progress * 2 });
    }

    function springBack() {
        gsap.to(topEl, { rotation: 0, x: 0, y: 0, duration: 0.45, ease: "back.out(2.2)" });
        gsap.to(tearEl, { opacity: 0, scaleX: 0, duration: 0.25 });
        gsap.to(tilt, { rotationY: 0, rotationZ: 0, duration: 0.45, ease: "back.out(2)" });
    }

    pack.addEventListener("pointerdown", event => {
        if (state.opening || state.packs <= 0 || event.button > 0) return;
        dragging = { id: event.pointerId, x: event.clientX, dx: 0, moved: false };
        try {
            pack.setPointerCapture(event.pointerId);
        } catch {
            /* pointeur déjà relâché : sans importance */
        }
    });

    pack.addEventListener("pointermove", event => {
        if (!dragging || event.pointerId !== dragging.id) return;
        dragging.dx = event.clientX - dragging.x;
        if (Math.abs(dragging.dx) > 6) dragging.moved = true;
        if (dragging.moved) {
            state.dir = dragging.dx >= 0 ? 1 : -1;
            setTear(clamp(Math.abs(dragging.dx) / TEAR_DISTANCE, 0, 1), state.dir);
        }
    });

    pack.addEventListener("pointerup", event => {
        if (!dragging || event.pointerId !== dragging.id) return;
        const drag = dragging;
        dragging = null;
        if (!drag.moved || Math.abs(drag.dx) / TEAR_DISTANCE >= 0.5) {
            openPack();
        } else {
            springBack();
        }
    });

    pack.addEventListener("pointercancel", () => {
        if (dragging) {
            dragging = null;
            springBack();
        }
    });

    pack.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openPack();
        }
    });

    form.addEventListener("submit", event => {
        event.preventDefault();
        openPack();
    });

    /* ---------------------------------------------------------------
       Ouverture
       --------------------------------------------------------------- */
    function setBusy(busy) {
        state.opening = busy;
        document.body.dataset.busy = busy ? "1" : "0";
        wrap.classList.toggle("is-busy", busy);
    }

    function playTear() {
        const dir = state.dir;
        const rect = pack.getBoundingClientRect();
        const tearX = rect.left + rect.width / 2;
        const tearY = rect.top + 62;

        const burstEl = document.createElement("span");
        burstEl.className = "pack-burst";
        tilt.appendChild(burstEl);

        const tl = gsap.timeline();
        tl.to(tearEl, { opacity: 1, scaleX: 1, duration: 0.18, ease: "power2.out" }, 0)
            .to(topEl, {
                x: dir * 320, y: -280, rotation: dir * 38, opacity: 0,
                duration: 0.65, ease: "power2.in", transformOrigin: dir > 0 ? "0% 100%" : "100% 100%"
            }, 0.05)
            .fromTo(burstEl, { scale: 0.2, opacity: 1 }, { scale: 1.5, opacity: 0, duration: 0.6, ease: "power2.out" }, 0.05)
            .to(tearEl, { opacity: 0, duration: 0.3 }, 0.35)
            .to(tilt, { rotationX: 0, rotationY: 0, rotationZ: 0, duration: 0.3 }, 0)
            .to(mainEl, { y: 3, duration: 0.06, repeat: 7, yoyo: true, ease: "none" }, 0.1)
            .add(() => {
                TeaFX.burst(tearX, tearY, "#00f0ff", 60, 1.1);
                TeaFX.burst(tearX, tearY, "#ffffff", 30, 0.8);
                TeaFX.flash("#00f0ff", 0.3);
                if (navigator.vibrate) navigator.vibrate(25);
            }, 0.05)
            .add(() => burstEl.remove(), 0.75);
        return tl;
    }

    async function restorePack() {
        gsap.set([topEl, mainEl, tearEl, tilt], { clearProps: "all" });
        gsap.from(wrap, { scale: 0.92, duration: 0.4, ease: "back.out(2)" });
        setBusy(false);
        syncState(state.packs);
        hint.textContent = state.packs > 0 ? "Glisse sur le paquet pour le déchirer (ou touche-le)" : "Plus de paquet pour le moment";
    }

    async function openPack() {
        if (state.opening || state.packs <= 0) return;
        setBusy(true);
        openBtn.disabled = true;
        hint.textContent = "Ouverture…";
        gsap.set(topEl, { clearProps: "all" });

        const request = fetch(stage.dataset.endpoint, {
            method: "POST",
            credentials: "same-origin",
            headers: { "X-Requested-With": "XMLHttpRequest", Accept: "application/json" }
        })
            .then(async response => ({ ok: response.ok, data: await response.json().catch(() => ({})) }))
            .catch(() => ({ ok: false, data: { error: "Connexion impossible." } }));

        await playTear();
        const { ok, data } = await request;

        if (!ok || !data.success) {
            notify(data.error || "Impossible d'ouvrir le paquet.", "error");
            if (data.code === "no_packs") state.packs = 0;
            await restorePack();
            return;
        }

        state.packs = data.packs_left;
        syncState(data.packs_left, data.refresh_in);
        await showCards(data.cards);
    }

    function syncState(packs, refreshIn) {
        state.packs = packs;
        packsCount.textContent = packs;
        wrap.classList.toggle("is-empty", packs <= 0);
        if (!state.opening) {
            openBtn.disabled = packs <= 0;
            openBtn.textContent = packs > 0 ? "Ouvrir le paquet" : "Packs épuisés";
        }
        if (refreshIn !== undefined) PackTimer.set(refreshIn);
    }

    /* ---------------------------------------------------------------
       Éventail de cartes
       --------------------------------------------------------------- */
    function createSlot(card, index, total) {
        const info = rarityInfo(card);
        const name = document.querySelector(".pack-name")?.textContent || "TeaMasters";

        const slot = document.createElement("button");
        slot.type = "button";
        slot.className = "pick-slot";
        slot.style.setProperty("--rc", info.color);
        slot.setAttribute("aria-label", `Carte ${index + 1} sur ${total}, face cachée. Appuie pour la retourner.`);
        slot.innerHTML = `
            <span class="pick-tilt"><span class="pick-scale"><span class="pick-flip">
                <span class="pick-face pick-back">
                    <span class="back-emblem">✦</span>
                    <span class="back-name"></span>
                    <span class="back-tap">Touche pour retourner</span>
                </span>
                <span class="pick-face pick-front"><span class="pick-glare"></span></span>
            </span></span></span>
            <span class="pick-ring"></span>
            <span class="pick-label"></span>`;
        slot.querySelector(".back-name").textContent = name.toUpperCase();
        slot.querySelector(".pick-label").textContent = "✦ " + info.label.toUpperCase();
        slot.querySelector(".pick-front").prepend(makeModalCardEl(card));

        const entry = { el: slot, card, info, index, done: false, busy: false, baseY: 0, z: index + 1 };
        slot.addEventListener("click", () => onPick(entry));
        return entry;
    }

    function layoutFan() {
        const count = state.slots.length;
        if (!count) return;
        const available = Math.max(280, fan.clientWidth - 8);
        const gap = 18;
        const scale = clamp((available - (count - 1) * gap) / (count * CARD_W), 0.62, 1);
        const width = CARD_W * scale;
        const total = count * width + (count - 1) * gap;
        const margin = total > available && count > 1 ? -((total - available) / (count - 1)) : gap;
        const mid = (count - 1) / 2;

        state.slots.forEach((s, i) => {
            s.el.style.width = width + "px";
            s.el.style.height = CARD_H * scale + "px";
            s.el.style.marginLeft = i === 0 ? "0" : margin + "px";
            s.el.querySelector(".pick-scale").style.transform = `scale(${scale})`;
            s.baseY = Math.abs(i - mid) * 10;
            if (!s.done) gsap.set(s.el, { rotation: (i - mid) * 5, y: s.baseY, zIndex: s.z });
        });
    }

    async function showCards(cards) {
        form.hidden = true;
        reveal.hidden = false;
        actions.hidden = false;
        done.hidden = true;
        revealAllBtn.disabled = false;
        fan.innerHTML = "";
        state.revealed = 0;
        state.slots = cards.map((card, i) => createSlot(card, i, cards.length));
        state.slots.forEach(s => fan.appendChild(s.el));
        layoutFan();
        updateHint();

        const mid = (cards.length - 1) / 2;
        gsap.from(state.slots.map(s => s.el), {
            y: 160, scale: 0.55, opacity: 0, duration: 0.75, stagger: 0.12, ease: "back.out(1.6)",
            rotation: i => (i - mid) * -28, clearProps: "opacity"
        });
        reveal.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" });
    }

    function updateHint() {
        const remaining = state.slots.length - state.revealed;
        hint.textContent = remaining > 0
            ? `Choisis une carte à retourner, dans l'ordre que tu veux (${remaining} restante${remaining > 1 ? "s" : ""})`
            : "Paquet ouvert ! Touche une carte pour la voir en grand.";
    }

    function onPick(slot) {
        if (slot.done) {
            openCardModal(slot.card);
        } else {
            revealCard(slot, false);
        }
    }

    function anticipate(slot) {
        return new Promise(resolve => {
            const ring = slot.el.querySelector(".pick-ring");
            TeaFX.flash(slot.info.color, 0.12);
            gsap.timeline({ onComplete: resolve })
                .to(slot.el, { x: "+=5", duration: 0.05, repeat: 9, yoyo: true, ease: "none" }, 0)
                .fromTo(ring, { scale: 0.5, opacity: 0.8 }, { scale: 1.5, opacity: 0, duration: 0.55, ease: "power2.out" }, 0);
        });
    }

    function impact(slot) {
        const { info } = slot;
        const rect = slot.el.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top + rect.height / 2;

        TeaFX.burst(x, y, info.color, BURST_COUNT[info.tier], 1 + info.tier * 0.12);
        if (info.tier >= 2) TeaFX.burst(x, y, "#ffffff", Math.round(BURST_COUNT[info.tier] / 3), 0.8);
        if (info.tier >= 3) TeaFX.flash(info.color, 0.15 + info.tier * 0.06);
        if (info.tier >= 4) TeaFX.shake(stage, 4 + info.tier * 2);
        if (navigator.vibrate) navigator.vibrate(info.tier >= 4 ? [30, 40, 70] : 15);

        const ring = slot.el.querySelector(".pick-ring");
        gsap.fromTo(ring, { scale: 0.6, opacity: 0.9 }, { scale: 2.1 + info.tier * 0.15, opacity: 0, duration: 0.8, ease: "power2.out" });
        gsap.fromTo(slot.el.querySelector(".pick-label"), { y: 8, opacity: 0 }, { y: 0, opacity: 1, duration: 0.45, ease: "power2.out" });
    }

    async function revealCard(slot, fast) {
        if (slot.done || slot.busy) return;
        slot.busy = true;
        slot.el.classList.add("is-revealed");
        gsap.set(slot.el, { zIndex: 60 });

        if (!fast && !reduceMotion && slot.info.tier >= 3) await anticipate(slot);

        const flip = slot.el.querySelector(".pick-flip");
        const duration = fast || reduceMotion ? 0.4 : 0.75;
        await new Promise(resolve => {
            gsap.timeline({ onComplete: resolve })
                .to(slot.el, { y: slot.baseY - 30, scale: 1.08, rotation: 0, duration: 0.28, ease: "power2.out" }, 0)
                .to(flip, { rotationY: 180, duration, ease: "power3.inOut" }, 0)
                .add(() => impact(slot), duration * 0.5)
                .to(slot.el, { y: slot.baseY, scale: 1, zIndex: slot.z, duration: 0.45, ease: "back.out(1.6)" }, ">-0.12");
        });

        slot.done = true;
        slot.busy = false;
        slot.el.setAttribute(
            "aria-label",
            `${slot.card.name}, ${slot.info.label}. Appuie pour voir la carte en grand.`
        );
        state.revealed += 1;
        updateHint();
        if (state.revealed === state.slots.length) finish();
    }

    async function revealAll() {
        revealAllBtn.disabled = true;
        for (const slot of state.slots) {
            if (!slot.done) {
                revealCard(slot, true);
                await sleep(260);
            }
        }
    }

    function finish() {
        actions.hidden = true;
        done.hidden = false;
        againBtn.hidden = state.packs <= 0;
        setBusy(false);
        gsap.from(done, { y: 14, opacity: 0, duration: 0.5, ease: "power2.out" });
    }

    revealAllBtn.addEventListener("click", revealAll);

    againBtn.addEventListener("click", () => {
        reveal.hidden = true;
        fan.innerHTML = "";
        state.slots = [];
        gsap.set([topEl, mainEl, tearEl, tilt], { clearProps: "all" });
        form.hidden = false;
        syncState(state.packs);
        hint.textContent = state.packs > 0 ? "Glisse sur le paquet pour le déchirer (ou touche-le)" : "Plus de paquet pour le moment";
        gsap.from(wrap, { y: 50, opacity: 0, scale: 0.9, duration: 0.55, ease: "back.out(1.6)", clearProps: "opacity" });
        window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
    });

    /* Éclat + inclinaison des cartes déjà retournées */
    fan.addEventListener("pointermove", event => {
        if (!canTilt) return;
        const slot = event.target.closest(".pick-slot.is-revealed");
        if (!slot) return;
        const rect = slot.getBoundingClientRect();
        const x = clamp((event.clientX - rect.left) / rect.width, 0, 1);
        const y = clamp((event.clientY - rect.top) / rect.height, 0, 1);
        const glare = slot.querySelector(".pick-glare");
        glare.style.setProperty("--gx", (x * 100).toFixed(0) + "%");
        glare.style.setProperty("--gy", (y * 100).toFixed(0) + "%");
        gsap.to(slot.querySelector(".pick-tilt"), {
            rotationY: (x - 0.5) * 22, rotationX: -(y - 0.5) * 18, duration: 0.3, overwrite: "auto"
        });
    });
    fan.addEventListener("pointerout", event => {
        const slot = event.target.closest(".pick-slot.is-revealed");
        if (slot && !slot.contains(event.relatedTarget)) {
            gsap.to(slot.querySelector(".pick-tilt"), { rotationY: 0, rotationX: 0, duration: 0.45, overwrite: "auto" });
        }
    });

    let resizeTimer = 0;
    window.addEventListener("resize", () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(layoutFan, 120);
    }, { passive: true });

    /* Ouverture sans JavaScript au chargement : /pull a déjà tiré les cartes */
    const initial = document.getElementById("initial-cards");
    if (initial) {
        setBusy(true);
        showCards(JSON.parse(initial.textContent));
    }
})();
