from django import template
from utils.document_validators import format_cnpj, format_cpf

register = template.Library()


@register.filter
def format_agencia(value):
    """Formata o número da agência bancária, suportando dígito verificador 'X'.

    Exemplos:
    - "23132" -> "2313-2"
    - "2313X" -> "2313-X"
    - "2313"  -> "2313"
    """
    if not value or value == "Não informado":
        return "Não informado"

    raw = str(value).replace("-", "").replace(" ", "")
    cleaned = "".join(ch for ch in raw if ch.isdigit() or ch.lower() == "x")

    if len(cleaned) == 5:
        dv = cleaned[-1].upper()
        base = cleaned[:4]
        if base.isdigit() and (dv.isdigit() or dv == "X"):
            return f"{base}-{dv}"
    elif len(cleaned) == 4 and cleaned.isdigit():
        return cleaned

    return value


@register.filter
def format_conta(value):
    """Formata o número da conta bancária com dígito verificador no final.

    Suporta dígito verificador numérico ou letra 'X'.
    """
    if not value or value == "Não informado":
        return "Não informado"

    # Remover espaços e hífens para reconstruir a máscara
    raw = str(value).replace("-", "").replace(" ", "")
    # Manter apenas dígitos e possível 'x'/'X' como dígito verificador
    cleaned = "".join(ch for ch in raw if ch.isdigit() or ch.lower() == "x")

    if len(cleaned) >= 2:
        dv = cleaned[-1].upper()  # dígito verificador pode ser número ou 'X'
        numeros = "".join(ch for ch in cleaned[:-1] if ch.isdigit())
        if numeros:
            return f"{numeros}-{dv}"

    return value
@register.filter
def format_cnpj_cpf(value):
    """Formata visualmente CPF/CNPJ sem alterar o dado salvo.

    - Se tiver 11 dígitos, aplica máscara de CPF.
    - Se tiver 14 dígitos, aplica máscara de CNPJ.
    - Caso contrário, retorna o valor original.
    """
    if not value or value == "Não informado":
        return value or ""

    digits = "".join(filter(str.isdigit, str(value)))
    if len(digits) == 11:
        return format_cpf(digits)
    if len(digits) == 14:
        return format_cnpj(digits)
    return value


@register.filter
def format_telefone(value):
    """Formata telefone brasileiro a partir de dígitos.

    - 11 dígitos: (AA) BBBBB-CCCC
    - 10 dígitos: (AA) BBBB-CCCC
    """
    if not value or value == "Não informado":
        return value or ""

    digits = "".join(filter(str.isdigit, str(value)))
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return value
