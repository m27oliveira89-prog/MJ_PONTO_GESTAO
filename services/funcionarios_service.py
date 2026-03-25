FUNCIONARIOS = [
    {
        "nome": "David Cerqueira",
        "matricula": "MAT001",
        "cargo": "Motorista",
        "status": "ativo",
        "senha": "123456",
        "trocar_senha_no_primeiro_login": False,
    },
    {
        "nome": "Lucio M",
        "matricula": "MAT002",
        "cargo": "Auxiliar Administrativo",
        "status": "ativo",
        "senha": "123456",
        "trocar_senha_no_primeiro_login": False,
    },
    {
        "nome": "Maik Oliveira",
        "matricula": "MAT003",
        "cargo": "Conferente",
        "status": "inativo",
        "senha": "123456",
        "trocar_senha_no_primeiro_login": False,
    },
    {
        "nome": "Juliene Batista",
        "matricula": "MAT004",
        "cargo": "RH",
        "status": "ativo",
        "senha": "123456",
        "trocar_senha_no_primeiro_login": False,
    },
]

REQUIRED_FIELDS = (
    "nome",
    "matricula",
    "cargo",
    "status",
)


def list_funcionarios():
    return list(FUNCIONARIOS)


def get_funcionario(matricula):
    normalized_matricula = (matricula or "").strip()

    if not normalized_matricula:
        return None

    for funcionario in FUNCIONARIOS:
        if funcionario["matricula"] == normalized_matricula:
            return dict(funcionario)

    return None


def create_funcionario(funcionario_data):
    cleaned_data = _normalize_funcionario_data(funcionario_data)
    cleaned_data["senha"] = "123456"
    cleaned_data["trocar_senha_no_primeiro_login"] = True

    if any(
        funcionario["matricula"] == cleaned_data["matricula"]
        for funcionario in FUNCIONARIOS
    ):
        raise ValueError("Ja existe um funcionario cadastrado com esta matricula.")

    FUNCIONARIOS.append(cleaned_data)
    return cleaned_data


def update_funcionario(matricula_original, funcionario_data):
    normalized_original = (matricula_original or "").strip()

    if not normalized_original:
        raise ValueError("Matricula original nao informada.")

    cleaned_data = _normalize_funcionario_data(funcionario_data)

    for funcionario in FUNCIONARIOS:
        if (
            funcionario["matricula"] == cleaned_data["matricula"]
            and funcionario["matricula"] != normalized_original
        ):
            raise ValueError("Ja existe um funcionario cadastrado com esta matricula.")

    for funcionario in FUNCIONARIOS:
        if funcionario["matricula"] == normalized_original:
            senha_atual = funcionario.get("senha", funcionario["matricula"])
            trocar_senha = funcionario.get("trocar_senha_no_primeiro_login", False)
            funcionario.update(cleaned_data)
            funcionario["senha"] = senha_atual
            funcionario["trocar_senha_no_primeiro_login"] = trocar_senha
            return funcionario

    raise ValueError("Funcionario nao encontrado.")


def set_funcionario_status(matricula, status):
    normalized_matricula = (matricula or "").strip()
    normalized_status = (status or "").strip()

    if not normalized_matricula:
        raise ValueError("Matricula nao informada.")

    if normalized_status not in {"ativo", "inativo"}:
        raise ValueError("Status invalido para o funcionario.")

    for funcionario in FUNCIONARIOS:
        if funcionario["matricula"] == normalized_matricula:
            funcionario["status"] = normalized_status
            return funcionario

    raise ValueError("Funcionario nao encontrado.")


def reset_funcionario_password(matricula, nova_senha):
    normalized_matricula = (matricula or "").strip()
    normalized_password = (nova_senha or "").strip()

    if not normalized_matricula:
        raise ValueError("Matricula nao informada.")

    if not normalized_password:
        raise ValueError("Informe uma nova senha provisoria.")

    for funcionario in FUNCIONARIOS:
        if funcionario["matricula"] == normalized_matricula:
            funcionario["senha"] = normalized_password
            funcionario["trocar_senha_no_primeiro_login"] = True
            return funcionario

    raise ValueError("Funcionario nao encontrado.")


def change_funcionario_password(matricula, nova_senha):
    normalized_matricula = (matricula or "").strip()
    normalized_password = (nova_senha or "").strip()

    if not normalized_matricula:
        raise ValueError("Matricula nao informada.")

    if not normalized_password:
        raise ValueError("Informe a nova senha.")

    for funcionario in FUNCIONARIOS:
        if funcionario["matricula"] == normalized_matricula:
            funcionario["senha"] = normalized_password
            funcionario["trocar_senha_no_primeiro_login"] = False
            return funcionario

    raise ValueError("Funcionario nao encontrado.")


def _normalize_funcionario_data(funcionario_data):
    cleaned_data = {}

    for field in REQUIRED_FIELDS:
        value = funcionario_data.get(field, "").strip()

        if not value:
            raise ValueError(f"O campo '{field}' e obrigatorio.")

        cleaned_data[field] = value

    if cleaned_data["status"] not in {"ativo", "inativo"}:
        raise ValueError("O campo 'status' deve ser 'ativo' ou 'inativo'.")

    return cleaned_data
