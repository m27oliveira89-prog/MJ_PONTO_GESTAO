from functools import wraps

from flask import (
    Blueprint,
    abort,
    flash,
    get_flashed_messages,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from services.funcionarios_service import list_funcionarios
from services.ponto_service import list_registros, registrar_ponto_funcionario


ponto_bp = Blueprint("ponto", __name__, url_prefix="/ponto")


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user"):
            abort(401)

        return view_func(*args, **kwargs)

    return wrapped_view


@ponto_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    current_user = session.get("user")
    is_admin = current_user.get("role") == "admin"
    funcionarios_ativos = [
        funcionario
        for funcionario in list_funcionarios()
        if funcionario.get("status") == "ativo"
    ]

    if request.method == "POST":
        payload = request.get_json(silent=True) if request.is_json else request.form

        matricula = (
            current_user.get("matricula")
            if not is_admin
            else (payload.get("matricula") or "").strip()
        )
        tipo = (payload.get("tipo") or "entrada").strip()
        foto_base64 = (payload.get("foto_url") or "").strip()
        latitude = (payload.get("latitude") or "").strip()
        longitude = (payload.get("longitude") or "").strip()

        try:
            registrar_ponto_funcionario(
                matricula,
                tipo=tipo,
                foto_base64=foto_base64,
                latitude=latitude,
                longitude=longitude,
            )
            success_message = "Ponto registrado com sucesso."

            if request.is_json:
                return jsonify(
                    {
                        "success": True,
                        "message": success_message,
                    }
                )

            flash(success_message, "success")
            return redirect(url_for("ponto.index"))
        except ValueError as exc:
            error_message = str(exc)

            if request.is_json:
                return jsonify(
                    {
                        "success": False,
                        "message": error_message,
                    }
                ), 400

            flash(error_message, "error")
            return redirect(url_for("ponto.index"))

    error_message = None
    success_message = None
    flashed_messages = get_flashed_messages(with_categories=True)

    for category, message in flashed_messages:
        if category == "success" and not success_message:
            success_message = message
        elif category == "error" and not error_message:
            error_message = message

    return render_template(
        "ponto.html",
        page_title="Bater Ponto",
        registros=(
            list_registros()
            if is_admin
            else list_registros(current_user.get("display_name"))
        ),
        error_message=error_message,
        success_message=success_message,
        current_user=current_user,
        funcionarios_ativos=funcionarios_ativos,
        is_admin=is_admin,
    )
