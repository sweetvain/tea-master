const PARTICLE_COLORS = {
    rare: "#4a9eff", epique: "#b06bff", legendaire: "#ffb830",
    mythique: "#ff2d55", goat: "#39ff6a", hess: "#8a8a9a"
};
const AUTO_FLIP_DELAY_MS = 3000;

const cards = JSON.parse(document.getElementById("pull-data").textContent);
const flipContainer = document.getElementById("flip-container");
const actionBtn = document.getElementById("action-btn");

let currentIndex = 0;
let hasFlipped = false;
let flipTimeout;

function displayCard(index) {
    hasFlipped = false;
    gsap.set(flipContainer, { rotationY: 0 });
    actionBtn.classList.remove("visible");

    const cardEl = makeModalCardEl(cards[index]);
    cardEl.style.pointerEvents = "auto";
    cardEl.addEventListener("click", event => {
        event.stopPropagation();
        openCardModal(cards[currentIndex]);
    });

    const wrap = document.getElementById("modal-card-el-pull");
    wrap.innerHTML = "";
    wrap.appendChild(cardEl);

    flipContainer.onclick = triggerFlip;

    clearTimeout(flipTimeout);
    flipTimeout = setTimeout(triggerFlip, AUTO_FLIP_DELAY_MS);
}

function triggerFlip() {
    if (hasFlipped) return;
    hasFlipped = true;
    clearTimeout(flipTimeout);

    gsap.to(flipContainer, {
        rotationY: 180,
        duration: 0.8,
        ease: "power2.out",
        onComplete: () => {
            createParticles((cards[currentIndex].rarity || "").toLowerCase());
            actionBtn.innerText = currentIndex < cards.length - 1 ? "Continuer" : "Terminer";
            actionBtn.classList.add("visible");
        }
    });
}

function handleAction() {
    if (currentIndex < cards.length - 1) {
        currentIndex++;
        displayCard(currentIndex);
    } else {
        window.location.href = "/collection";
    }
}

function createParticles(rarity) {
    const color = PARTICLE_COLORS[rarity] || "#ffffff";
    const centerX = window.innerWidth / 2;
    const centerY = window.innerHeight / 2;

    for (let i = 0; i < 20; i++) {
        const particle = document.createElement("div");
        particle.className = "particle";
        particle.style.backgroundColor = color;
        document.body.appendChild(particle);

        gsap.fromTo(particle,
            { x: centerX, y: centerY, opacity: 1 },
            {
                x: (Math.random() - 0.5) * 600 + centerX,
                y: (Math.random() - 0.5) * 600 + centerY,
                opacity: 0,
                duration: 1.5,
                onComplete: () => particle.remove()
            }
        );
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (cards.length > 0) {
        displayCard(0);
    } else {
        window.location.href = "/?message=" + encodeURIComponent("Vous avez déjà toutes les cartes !");
    }
});
