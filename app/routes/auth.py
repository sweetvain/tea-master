from flask import Blueprint, redirect, render_template, request, session, url_for

from app.services import auth as auth_service

bp = Blueprint("auth", __name__)


def _start_session(user):
    session.clear()
    session["user_id"] = user.id


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        try:
            user = auth_service.authenticate(
                request.form.get("username"), request.form.get("password")
            )
        except auth_service.AuthError as exc:
            error = str(exc)
        else:
            _start_session(user)
            return redirect(url_for("main.index"))
    return render_template("login.html", error=error)


@bp.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        try:
            user = auth_service.register_user(
                request.form.get("username"), request.form.get("password")
            )
        except auth_service.AuthError as exc:
            error = str(exc)
        else:
            _start_session(user)
            return redirect(url_for("main.index"))
    return render_template("register.html", error=error)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
