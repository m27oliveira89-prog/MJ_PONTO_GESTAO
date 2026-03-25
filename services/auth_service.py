from services.funcionarios_service import (
    change_funcionario_password,
    get_funcionario,
    list_funcionarios,
)


TEST_USERS = {
    "nociam": {
        "username": "Nociam",
        "password": "321",
        "role": "admin",
        "display_name": "Nociam",
    },
    "colaborador": {
        "username": "Colaborador",
        "password": "321",
        "role": "funcionario",
        "display_name": "Colaborador",
    },
}


def authenticate_user(username, password):
    normalized_username = username.strip().lower()
    user = TEST_USERS.get(normalized_username)

    if user:
        if user["password"] != password:
            return None

        return {
            "username": user["username"],
            "role": user["role"],
            "display_name": user["display_name"],
            "trocar_senha_no_primeiro_login": False,
        }

    funcionario = _get_funcionario_for_login(normalized_username)

    if not funcionario:
        return None

    if funcionario.get("status") != "ativo":
        raise ValueError("Funcionario inativo nao pode acessar o sistema.")

    if funcionario.get("senha") != password:
        return None

    return {
        "username": funcionario["matricula"],
        "role": "funcionario",
        "display_name": funcionario["nome"],
        "matricula": funcionario["matricula"],
        "trocar_senha_no_primeiro_login": funcionario.get(
            "trocar_senha_no_primeiro_login",
            False,
        ),
    }


def change_password_for_user(user, nova_senha):
    if user.get("role") != "funcionario":
        raise ValueError("A troca obrigatoria de senha se aplica apenas a funcionarios.")

    matricula = user.get("matricula") or user.get("username")
    funcionario = change_funcionario_password(matricula, nova_senha)

    return {
        "username": funcionario["matricula"],
        "role": "funcionario",
        "display_name": funcionario["nome"],
        "matricula": funcionario["matricula"],
        "trocar_senha_no_primeiro_login": False,
    }


def _get_funcionario_for_login(normalized_username):
    for funcionario in list_funcionarios():
        if funcionario["matricula"].strip().lower() == normalized_username:
            return get_funcionario(funcionario["matricula"])

    return None
