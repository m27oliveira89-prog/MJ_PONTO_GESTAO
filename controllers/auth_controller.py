from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from services.auth_service import authenticate_user, change_password_for_user


auth_bp = Blueprint("auth", __name__)


@auth_bp.before_app_request
def enforce_password_change():
    if not session.get("password_change_required"):
        return None

    allowed_endpoints = {"auth.change_password", "auth.logout", "static"}

    if request.endpoint is None:
        return None

    if request.endpoint.startswith("static") or request.endpoint in allowed_endpoints:
        return None

    return redirect(url_for("auth.change_password"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error_message = None
    access_mode = request.args.get("mode", "normal").strip().lower()

    if access_mode not in {"normal", "admin"}:
        access_mode = "normal"

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        access_mode = request.form.get("access_mode", "normal").strip().lower()

        if access_mode not in {"normal", "admin"}:
            access_mode = "normal"

        try:
            user = authenticate_user(username=username, password=password)
        except ValueError as exc:
            error_message = str(exc)
            user = None

        if user:
            session["user"] = user

            if user.get("trocar_senha_no_primeiro_login"):
                session["password_change_required"] = True
                return redirect(url_for("auth.change_password"))

            session.pop("password_change_required", None)

            if access_mode == "admin":
                if user.get("role") != "admin":
                    session.clear()
                    error_message = "Acesso admin disponivel apenas para administradores."
                else:
                    return redirect(url_for("admin_access"))
            else:
                return redirect(url_for("home.index"))

        if not error_message:
            error_message = "Usuario ou senha invalidos."

    return render_template(
        "login.html",
        error_message=error_message,
        access_mode=access_mode,
    )


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/redefinir-senha", methods=["GET", "POST"])
def change_password():
    current_user = session.get("user")
    error_message = None
    success_message = session.pop("password_change_success_message", None)

    if success_message and current_user:
        return render_template(
            "redefinir_senha.html",
            current_user=current_user,
            error_message=None,
            success_message=success_message,
            flow_completed=True,
        )

    if not current_user or not session.get("password_change_required"):
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        nova_senha = request.form.get("nova_senha", "").strip()

        try:
            updated_user = change_password_for_user(current_user, nova_senha)
            session["user"] = updated_user
            session.pop("password_change_required", None)
            session["password_change_success_message"] = (
                "Senha redefinida com sucesso."
            )
            return redirect(url_for("auth.change_password"))
        except ValueError as exc:
            error_message = str(exc)

    return render_template(
        "redefinir_senha.html",
        current_user=current_user,
        error_message=error_message,
        success_message=None,
        flow_completed=False,
    )
