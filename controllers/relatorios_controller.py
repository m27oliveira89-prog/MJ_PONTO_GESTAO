from functools import wraps

from flask import Blueprint, abort, render_template, request, session

from services.relatorios_service import build_relatorio_ponto


relatorios_bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")


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


@relatorios_bp.route("/", methods=["GET"])
@admin_required
def index():
    filters = {
        "funcionario": request.args.get("funcionario", "").strip(),
        "data_inicial": request.args.get("data_inicial", "").strip(),
        "data_final": request.args.get("data_final", "").strip(),
    }

    relatorio = build_relatorio_ponto(filters)

    return render_template(
        "relatorios.html",
        page_title="Relatorios",
        relatorio=relatorio,
        filters=filters,
        current_user=session.get("user"),
    )
