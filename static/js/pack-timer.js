(function () {
    const timerEl = document.getElementById("timer");
    const remaining = parseInt(timerEl.dataset.remaining, 10);

    if (Number.isNaN(remaining)) {
        timerEl.innerText = "Prêt à ouvrir !";
        return;
    }

    const endTime = Date.now() + remaining * 1000;

    function updateTimer() {
        const distance = endTime - Date.now();
        if (distance <= 0) {
            location.reload();
            return;
        }
        const minutes = Math.floor(distance / 60000);
        const seconds = Math.floor((distance % 60000) / 1000);
        timerEl.innerText = `Rafraîchissement dans ${minutes}m ${seconds}s`;
    }

    setInterval(updateTimer, 1000);
    updateTimer();
})();
