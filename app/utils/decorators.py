from functools import wraps

from flask import g, jsonify, redirect, request, url_for


def _wants_json() -> bool:
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.accept_mimetypes.best == "application/json"
    )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            if _wants_json():
                return jsonify({"success": False, "error": "Non connecté."}), 401
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def api_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return jsonify({"success": False, "error": "Non connecté."}), 401
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not g.user.is_admin:
            return "Accès interdit : vous n'êtes pas administrateur.", 403
        return view(*args, **kwargs)

    return wrapped
