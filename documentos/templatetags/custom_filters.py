import locale  # Adicionando a importação do módulo locale

from django import template

register = template.Library()


@register.filter
def currency_br(value):
    """Formata um valor para o formato de moeda brasileira"""
    if value is None or value == "":
        return "0,00"

    # Converte para float se for string
    if isinstance(value, str):
        value = float(value)

    # Formata o número
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
    return locale.format_string("%.2f", value, grouping=True)
