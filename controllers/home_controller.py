from flask import Blueprint, redirect, url_for


home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    return redirect(url_for("auth.login"))
