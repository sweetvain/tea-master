import re
import uuid
from pathlib import Path

from flask import current_app


SAFE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")
UUID_PREFIX = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


class UploadError(ValueError):
    """Fichier envoyé invalide (extension non autorisée, etc.)."""


def safe_name(filename: str) -> str:
    """Nom de fichier 100 % ASCII : les anciens noms « uuid_nom accentué.jpg » deviennent « uuid.jpg »."""
    if SAFE_NAME.match(filename):
        return filename
    match = UUID_PREFIX.match(filename)
    stem = match.group(0).lower() if match else uuid.uuid5(uuid.NAMESPACE_URL, filename).hex
    extension = Path(filename).suffix.lower()
    return stem + (extension if SAFE_NAME.match(extension) else "")


def _upload_dir() -> Path:
    folder = Path(current_app.config["UPLOAD_FOLDER"])
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise UploadError("L'envoi d'images n'est pas disponible sur cet hébergement.")
    return folder


def save_photo(file) -> str | None:
    """Enregistre l'image envoyée et retourne son nom de fichier (ou None si aucun fichier)."""
    if file is None or not file.filename:
        return None

    extension = Path(file.filename).suffix.lower().lstrip(".")
    if extension not in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        allowed = ", ".join(sorted(current_app.config["ALLOWED_IMAGE_EXTENSIONS"]))
        raise UploadError(f"Format d'image non supporté (autorisés : {allowed}).")

    filename = f"{uuid.uuid4()}.{extension}"
    try:
        file.save(_upload_dir() / filename)
    except OSError:
        raise UploadError("L'envoi d'images n'est pas disponible sur cet hébergement.")
    return filename


def delete_photo(filename: str | None) -> None:
    """Supprime une image du dossier d'uploads, sans jamais sortir de ce dossier."""
    if not filename:
        return

    folder = _upload_dir().resolve()
    path = (folder / filename).resolve()
    if folder in path.parents and path.is_file():
        path.unlink()
