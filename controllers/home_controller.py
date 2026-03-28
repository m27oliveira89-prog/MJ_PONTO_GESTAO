from flask import Blueprint, redirect, session, url_for


home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    current_user = session.get("user")

    if not current_user:
        return redirect(url_for("auth.login"))

    if current_user.get("role") == "admin":
        return redirect(url_for("admin_access"))

    return redirect(url_for("ponto.index"))
