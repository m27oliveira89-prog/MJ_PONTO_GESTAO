from functools import wraps

from flask import Blueprint, abort, render_template, request, session

from services.historico_service import filter_historico_ponto, list_historico_ponto


historico_bp = Blueprint("historico", __name__, url_prefix="/historico")


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("user"):
            abort(401)

        return view_func(*args, **kwargs)

    return wrapped_view


@historico_bp.route("/ponto", methods=["GET"])
@login_required
def ponto():
    current_user = session.get("user")
    filters = {
        "funcionario": request.args.get("funcionario", "").strip(),
        "data": request.args.get("data", "").strip(),
        "tipo": request.args.get("tipo", "").strip(),
    }

    if current_user.get("role") != "admin":
        filters["funcionario"] = current_user.get(
            "display_name",
            current_user.get("username"),
        )

    registros = (
        filter_historico_ponto(filters)
        if any(filters.values())
        else list_historico_ponto(filters.get("funcionario"))
    )

    return render_template(
        "historico_ponto.html",
        page_title="Historico de Ponto",
        registros=registros,
        filters=filters,
        current_user=current_user,
        is_admin=current_user.get("role") == "admin",
    )
