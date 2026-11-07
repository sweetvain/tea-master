(function () {
    const searchInput = document.getElementById("coll-search");
    const filterButtons = document.querySelectorAll(".filter-btn, .stat-chip");
    const cards = document.querySelectorAll(".card-item-logic");
    const cardCountDisplay = document.getElementById("card-count-display");
    const SPECIAL_ACTIVE = ["mythique", "goat", "hess"];

    let currentRarityFilter = "all";

    function normalize(rarity) {
        return rarity.replace("é", "e");
    }

    function filterCards() {
        const query = searchInput.value.toLowerCase();
        const filter = normalize(currentRarityFilter);
        let visibleCount = 0;

        cards.forEach(card => {
            const matchesSearch = card.dataset.name.includes(query);
            const matchesRarity = filter === "all" || normalize(card.dataset.rarity) === filter;
            const visible = matchesSearch && matchesRarity;

            card.style.display = visible ? "" : "none";
            if (visible) visibleCount++;
        });
        cardCountDisplay.textContent = visibleCount;
    }

    function highlightActiveFilter() {
        document.querySelectorAll(".filter-btn").forEach(btn => {
            btn.classList.remove("active", "active-mythique", "active-goat", "active-hess");
            if (btn.dataset.filter === currentRarityFilter) {
                btn.classList.add("active");
                if (SPECIAL_ACTIVE.includes(currentRarityFilter)) {
                    btn.classList.add("active-" + currentRarityFilter);
                }
            }
        });
    }

    searchInput.addEventListener("input", filterCards);

    filterButtons.forEach(button => {
        button.addEventListener("click", () => {
            currentRarityFilter = button.dataset.filter;
            highlightActiveFilter();
            filterCards();
        });
    });
})();
