const PackTimer = (() => {
    const timerEl = document.getElementById("timer");
    let interval = null;
    let endTime = 0;

    function render() {
        const distance = endTime - Date.now();
        if (distance <= 0) {
            clearInterval(interval);
            interval = null;
            // ne recharge pas la page pendant l'ouverture d'un paquet
            if (document.body.dataset.busy === "1") {
                timerEl.innerText = "Prêt à ouvrir !";
            } else {
                location.reload();
            }
            return;
        }
        const minutes = Math.floor(distance / 60000);
        const seconds = Math.floor((distance % 60000) / 1000);
        timerEl.innerText = `Rafraîchissement dans ${minutes}m ${seconds}s`;
    }

    function set(remainingSeconds) {
        clearInterval(interval);
        interval = null;
        if (remainingSeconds === null || remainingSeconds === undefined || Number.isNaN(remainingSeconds)) {
            timerEl.innerText = "Prêt à ouvrir !";
            return;
        }
        endTime = Date.now() + remainingSeconds * 1000;
        interval = setInterval(render, 1000);
        render();
    }

    const initial = parseInt(timerEl.dataset.remaining, 10);
    set(Number.isNaN(initial) ? null : initial);

    return { set };
})();
