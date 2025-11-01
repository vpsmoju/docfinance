from django import template

register = template.Library()

@register.filter
def format_cpf(value):
    """Formata um CPF no padrão 000.000.000-00"""
    if not value:
        return ""
    
    # Remove caracteres não numéricos
    value = ''.join(filter(str.isdigit, str(value)))
    
    # Verifica se tem 11 dígitos
    if len(value) != 11:
        return value
    
    return f"{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:]}"

@register.filter
def format_telefone(value):
    """Formata um telefone no padrão (00) 00000-0000"""
    if not value:
        return ""
    
    # Remove caracteres não numéricos
    value = ''.join(filter(str.isdigit, str(value)))
    
    # Verifica o tamanho para determinar o formato
    if len(value) == 11:  # Celular com 11 dígitos
        return f"({value[:2]}) {value[2:7]}-{value[7:]}"
    elif len(value) == 10:  # Telefone fixo com 10 dígitos
        return f"({value[:2]}) {value[2:6]}-{value[6:]}"
    else:
        return value  # Retorna sem formatação se não tiver o tamanho esperado