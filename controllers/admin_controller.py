from functools import wraps

from flask import Blueprint, abort, render_template, request, session

from services.admin_service import get_admin_config, update_admin_config


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        user = session.get("user")

        if not user:
            abort(401)

        if user.get("role") != "admin":
            abort(403)

        return view_func(*args, **kwargs)

    return wrapped_view


@admin_bp.route("/configuracoes", methods=["GET", "POST"])
@admin_required
def configuracoes():
    error_message = None
    success_message = None

    if request.method == "POST":
        config_data = {
            "usar_gps": request.form.get("usar_gps") == "on",
            "bloquear_localizacao": request.form.get("bloquear_localizacao") == "on",
            "exigir_foto": request.form.get("exigir_foto") == "on",
            "raio": request.form.get("raio", "").strip(),
            "dias_retencao": request.form.get("dias_retencao", "").strip(),
            "latitude_referencia": request.form.get("latitude_referencia", "").strip(),
            "longitude_referencia": request.form.get("longitude_referencia", "").strip(),
        }

        try:
            update_admin_config(config_data)
            success_message = "Configuracoes atualizadas com sucesso."
        except ValueError as exc:
            error_message = str(exc)

    return render_template(
        "admin_config.html",
        page_title="Configuracoes Administrativas",
        config=get_admin_config(),
        error_message=error_message,
        success_message=success_message,
        current_user=session.get("user"),
    )
