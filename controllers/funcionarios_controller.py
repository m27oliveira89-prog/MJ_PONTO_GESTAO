from functools import wraps

from flask import Blueprint, abort, redirect, render_template, request, session, url_for

from services.funcionarios_service import (
    create_funcionario,
    get_funcionario,
    list_funcionarios,
    reset_funcionario_password,
    set_funcionario_status,
    update_funcionario,
)


funcionarios_bp = Blueprint("funcionarios", __name__, url_prefix="/funcionarios")


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


@funcionarios_bp.route("/", methods=["GET", "POST"])
@admin_required
def index():
    listing_url = url_for("funcionarios.index")
    error_message = None
    success_message = session.pop("funcionarios_success_message", None)
    edit_matricula = request.args.get("edit", "").strip()
    funcionario_em_edicao = get_funcionario(edit_matricula) if edit_matricula else None

    if request.method == "POST":
        form_action = request.form.get("form_action", "create").strip()

        try:
            if form_action == "set_status":
                matricula = request.form.get("matricula", "").strip()
                status = request.form.get("status", "").strip()
                funcionario = set_funcionario_status(matricula, status)
                session["funcionarios_success_message"] = (
                    f"Status do funcionario {funcionario['nome']} alterado para "
                    f"{funcionario['status']}."
                )
                return redirect(listing_url)
            elif form_action == "update":
                matricula_original = request.form.get("matricula_original", "").strip()
                nova_senha_provisoria = request.form.get(
                    "nova_senha_provisoria", ""
                ).strip()
                funcionario_data = {
                    "nome": request.form.get("nome", "").strip(),
                    "matricula": request.form.get("matricula", "").strip(),
                    "cargo": request.form.get("cargo", "").strip(),
                    "status": request.form.get("status", "").strip(),
                }
                funcionario = update_funcionario(matricula_original, funcionario_data)

                if nova_senha_provisoria:
                    funcionario = reset_funcionario_password(
                        funcionario["matricula"],
                        nova_senha_provisoria,
                    )
                    session["funcionarios_success_message"] = (
                        f"Funcionario atualizado e senha redefinida para "
                        f"{funcionario['nome']}."
                    )
                else:
                    session["funcionarios_success_message"] = (
                        "Funcionario atualizado com sucesso."
                    )

                return redirect(listing_url)
            else:
                funcionario_data = {
                    "nome": request.form.get("nome", "").strip(),
                    "matricula": request.form.get("matricula", "").strip(),
                    "cargo": request.form.get("cargo", "").strip(),
                    "status": request.form.get("status", "").strip(),
                }
                funcionario = create_funcionario(funcionario_data)
                session["funcionarios_success_message"] = (
                    f"Funcionario cadastrado com sucesso. Login: "
                    f"{funcionario['matricula']} / 123456."
                )
                return redirect(listing_url)
        except ValueError as exc:
            error_message = str(exc)

    return render_template(
        "funcionarios.html",
        page_title="Cadastro de Funcionarios",
        funcionarios=list_funcionarios(),
        error_message=error_message,
        success_message=success_message,
        current_user=session.get("user"),
        funcionario_em_edicao=funcionario_em_edicao,
        funcionarios_url=listing_url,
        admin_url=url_for("admin_access"),
        logout_url=url_for("auth.logout"),
    )
