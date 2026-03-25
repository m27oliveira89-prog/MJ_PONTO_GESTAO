from functools import wraps

from flask import Blueprint, abort, render_template, request, session

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
    error_message = None
    success_message = None
    current_user = session.get("user")
    funcionarios_ativos = [
        funcionario
        for funcionario in list_funcionarios()
        if funcionario.get("status") == "ativo"
    ]

    if request.method == "POST":
        matricula = request.form.get("matricula", "").strip()

        try:
            registro = registrar_ponto_funcionario(matricula)
            success_message = (
                f"Ponto registrado com sucesso para {registro['funcionario']} "
                f"as {registro['hora']}."
            )
        except ValueError as exc:
            error_message = str(exc)

    return render_template(
        "ponto.html",
        page_title="Bater Ponto",
        registros=list_registros(),
        error_message=error_message,
        success_message=success_message,
        current_user=current_user,
        funcionarios_ativos=funcionarios_ativos,
    )
