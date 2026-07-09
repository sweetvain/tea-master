document.addEventListener("DOMContentLoaded", () => {
    // 1. Animation du titre principal
    gsap.from(".pull-title", {
        opacity: 0,
        y: -30,
        duration: 0.8,
        ease: "power3.out"
    });

    // 2. Animation d'apparition en cascade (Stagger) pour les cartes
    gsap.from(".game-card", {
        opacity: 0,
        scale: 0.3,
        y: 80,
        rotation: -10,
        duration: 1,
        stagger: 0.25, // Délai de 0.25s entre chaque carte
        ease: "back.out(1.5)", // Effet de rebond dynamique en s'arrêtant
        clearProps: "transform" // Nettoie les propriétés pour laisser le CSS prendre le relais au survol
    });

    // 3. Animation des boutons d'actions en bas
    gsap.from(".actions-container", {
        opacity: 0,
        y: 20,
        duration: 0.6,
        delay: 1.2, // Attend que les cartes soient apparues
        ease: "power2.out"
    });
});