from django import template

register = template.Library()


@register.filter
def format_agencia(value):
    """Formata o número da agência bancária (2313 -> 2313-2)"""
    if not value or value == "Não informado":
        return "Não informado"

    # Remove qualquer formatação existente e pega apenas os números
    value = "".join(filter(str.isdigit, value))

    # Formata apenas se for um número válido
    if value.isdigit():
        if len(value) == 5:  # 4 dígitos + 1 dígito verificador
            return f"{value[:4]}-{value[4]}"
        elif len(value) == 4:  # Apenas 4 dígitos
            return value

    return value


@register.filter
def format_conta(value):
    """Formata o número da conta bancária com dígito verificador no final"""
    if not value or value == "Não informado":
        return "Não informado"

    # Remove qualquer formatação existente e pega apenas os números
    value = "".join(filter(str.isdigit, value))

    # Formata apenas se for um número válido
    if value.isdigit():
        # Garante que sempre terá pelo menos 2 dígitos (1 número + 1 dígito verificador)
        if len(value) >= 2:
            # Separa o último dígito como verificador
            return f"{value[:-1]}-{value[-1]}"

    return value
