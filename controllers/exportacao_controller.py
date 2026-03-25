from functools import wraps

from flask import Blueprint, abort, make_response, request, session

from services.exportacao_service import exportar_excel, exportar_pdf


exportacao_bp = Blueprint("exportacao", __name__, url_prefix="/exportacao")


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


def _build_filters():
    return {
        "funcionario": request.args.get("funcionario", "").strip(),
        "data_inicial": request.args.get("data_inicial", "").strip(),
        "data_final": request.args.get("data_final", "").strip(),
    }


@exportacao_bp.route("/excel", methods=["GET"])
@admin_required
def excel():
    content, filename, mimetype = exportar_excel(_build_filters())
    response = make_response(content)
    response.headers["Content-Type"] = mimetype
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@exportacao_bp.route("/pdf", methods=["GET"])
@admin_required
def pdf():
    content, filename, mimetype = exportar_pdf(_build_filters())
    response = make_response(content)
    response.headers["Content-Type"] = mimetype
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
