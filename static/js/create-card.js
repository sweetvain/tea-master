document.addEventListener("DOMContentLoaded", () => {
    gsap.from(".cyber-form-grid", { opacity: 0, y: 30, duration: 0.6, ease: "power3.out" });
    gsap.from(".cyber-dropzone", { opacity: 0, scale: 0.95, duration: 0.5, delay: 0.2, ease: "back.out(1.2)" });
    gsap.from(".cyber-form-group", { opacity: 0, x: 20, duration: 0.4, delay: 0.3, stagger: 0.08, ease: "power2.out" });

    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("photo-input");
    const previewContainer = document.getElementById("preview-container");
    const previewImg = document.getElementById("preview-img");
    const form = document.getElementById("cyber-create-form");

    ["dragenter", "dragover"].forEach(eventName => {
        dropzone.addEventListener(eventName, event => {
            event.preventDefault();
            dropzone.classList.add("dragover");
            gsap.to(dropzone, { scale: 1.02, duration: 0.2 });
        });
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropzone.addEventListener(eventName, event => {
            event.preventDefault();
            dropzone.classList.remove("dragover");
            gsap.to(dropzone, { scale: 1, duration: 0.2 });
        });
    });

    dropzone.addEventListener("drop", event => {
        const files = event.dataTransfer.files;
        if (files.length) {
            fileInput.files = files;
            showPreview(files[0]);
        }
    });

    fileInput.addEventListener("change", event => {
        if (event.target.files.length) showPreview(event.target.files[0]);
    });

    function showPreview(file) {
        if (!file.type.startsWith("image/")) {
            showNotification("Ce fichier n'est pas une image.", "error");
            return;
        }
        const reader = new FileReader();
        reader.onloadend = () => {
            previewImg.src = reader.result;
            previewContainer.style.display = "flex";
            gsap.fromTo(previewContainer, { opacity: 0, scale: 0.9 }, { opacity: 1, scale: 1, duration: 0.3, ease: "power2.out" });
            showNotification("Image ajoutée ✓", "info");
        };
        reader.readAsDataURL(file);
    }

    function resetForm() {
        form.reset();
        previewContainer.style.display = "none";
        previewImg.src = "";
        gsap.fromTo(".cyber-form-grid",
            { boxShadow: "0 0 30px rgba(57, 255, 106, 0.4)" },
            { boxShadow: "0 20px 40px rgba(0,0,0,0.6)", duration: 1 });
    }

    form.addEventListener("submit", async event => {
        event.preventDefault();
        gsap.to("#btn-submit", { scale: 0.98, yoyo: true, repeat: 1, duration: 0.1 });

        try {
            const response = await fetch("/create", {
                method: "POST",
                body: new FormData(form),
                headers: { "X-Requested-With": "XMLHttpRequest" }
            });
            const data = await response.json().catch(() => ({}));

            if (response.ok && data.success) {
                showNotification("Carte ajoutée à la collection !", "success");
                resetForm();
            } else {
                showNotification((data.error || "Impossible d'ajouter la carte."), "error");
            }
        } catch {
            showNotification("Connexion impossible, réessaie.", "error");
        }
    });
});
