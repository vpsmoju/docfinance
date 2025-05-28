def validate_cnpj(cnpj: str) -> tuple[bool, str]:
    """Valida um CNPJ.

    Args:
        cnpj: String contendo o CNPJ a ser validado

    Returns:
        Tuple contendo (válido, mensagem)
        - válido: True se o CNPJ é válido, False caso contrário
        - mensagem: String vazia se válido, ou mensagem de erro se inválido
    """
    # Remove caracteres não numéricos
    cnpj = "".join(filter(str.isdigit, cnpj))

    # Verifica o tamanho
    if len(cnpj) != 14:
        return False, "CNPJ deve ter 14 dígitos"

    # Verifica se todos os dígitos são iguais
    if len(set(cnpj)) == 1:
        return False, "CNPJ inválido"

    # Validação do primeiro dígito
    weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    numbers = cnpj[:-2]
    total_sum = 0

    for i in range(12):
        total_sum += int(numbers[i]) * weights[i]

    first_digit = 11 - (total_sum % 11)
    if first_digit >= 10:
        first_digit = 0

    # Validação do segundo dígito
    weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    numbers = numbers + str(first_digit)
    total_sum = 0

    for i in range(13):
        total_sum += int(numbers[i]) * weights[i]

    second_digit = 11 - (total_sum % 11)
    if second_digit >= 10:
        second_digit = 0

    if int(cnpj[-2]) != first_digit or int(cnpj[-1]) != second_digit:
        return False, "CNPJ inválido"

    return True, ""


def format_cpf(cpf: str) -> str:
    """Formata um CPF com pontos e traço"""
    cpf = "".join(filter(str.isdigit, cpf))
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}" if len(cpf) == 11 else cpf


def format_cnpj(cnpj: str) -> str:
    """Formata um CNPJ com pontos, barra e traço"""
    cnpj = "".join(filter(str.isdigit, cnpj))
    return (
        f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        if len(cnpj) == 14
        else cnpj
    )


def validate_cpf(cpf: str) -> tuple[bool, str]:
    """Valida um CPF.

    Args:
        cpf: String contendo o CPF a ser validado

    Returns:
        Tuple contendo (válido, mensagem)
        - válido: True se o CPF é válido, False caso contrário
        - mensagem: String vazia se válido, ou mensagem de erro se inválido
    """
    # Remove caracteres não numéricos
    cpf = "".join(filter(str.isdigit, cpf))

    # Verifica o tamanho
    if len(cpf) != 11:
        return False, "CPF deve ter 11 dígitos"

    # Verifica se todos os dígitos são iguais
    if len(set(cpf)) == 1:
        return False, "CPF inválido"

    # Validação do primeiro dígito
    total_sum = 0
    for i in range(9):
        total_sum += int(cpf[i]) * (10 - i)

    first_digit = 11 - (total_sum % 11)
    if first_digit >= 10:
        first_digit = 0

    # Validação do segundo dígito
    total_sum = 0
    for i in range(10):
        total_sum += int(cpf[i]) * (11 - i)

    second_digit = 11 - (total_sum % 11)
    if second_digit >= 10:
        second_digit = 0

    if int(cpf[9]) != first_digit or int(cpf[10]) != second_digit:
        return False, "CPF inválido"

    return True, ""
