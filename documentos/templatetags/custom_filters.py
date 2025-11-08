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
    try:
        locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
        return locale.format_string("%.2f", value, grouping=True)
    except Exception:
        # Fallback simples quando locale não está disponível
        return f"{value:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _numero_extenso(n):
    """Converte número inteiro (0..999999999) para extenso em português."""
    unidades = [
        "zero",
        "um",
        "dois",
        "três",
        "quatro",
        "cinco",
        "seis",
        "sete",
        "oito",
        "nove",
    ]
    especiais = {
        10: "dez",
        11: "onze",
        12: "doze",
        13: "treze",
        14: "quatorze",
        15: "quinze",
        16: "dezesseis",
        17: "dezessete",
        18: "dezoito",
        19: "dezenove",
    }
    dezenas = [
        "",
        "",
        "vinte",
        "trinta",
        "quarenta",
        "cinquenta",
        "sessenta",
        "setenta",
        "oitenta",
        "noventa",
    ]
    centenas = [
        "",
        "cento",
        "duzentos",
        "trezentos",
        "quatrocentos",
        "quinhentos",
        "seiscentos",
        "setecentos",
        "oitocentos",
        "novecentos",
    ]

    if n == 0:
        return "zero"
    if n == 100:
        return "cem"

    def trio(x):
        c = x // 100
        r = x % 100
        d = r // 10
        u = r % 10
        partes = []
        if c:
            partes.append(centenas[c])
        if 10 <= r <= 19:
            partes.append(especiais[r])
        else:
            if d:
                partes.append(dezenas[d])
            if u:
                if d:
                    partes.append("e " + unidades[u])
                else:
                    partes.append(unidades[u])
        return " ".join([p for p in partes if p])

    milhoes = n // 1_000_000
    resto = n % 1_000_000
    milhares = resto // 1_000
    centenas_final = resto % 1_000

    partes = []
    if milhoes:
        partes.append(trio(milhoes) + (" milhão" if milhoes == 1 else " milhões"))
    if milhares:
        if milhoes and (milhares or centenas_final):
            partes.append("e " + trio(milhares) + " mil")
        else:
            partes.append(trio(milhares) + " mil")
    if centenas_final:
        if (milhoes or milhares) and centenas_final:
            partes.append("e " + trio(centenas_final))
        else:
            partes.append(trio(centenas_final))
    return " ".join(partes).strip()


@register.filter
def extenso_br(valor):
    """Converte um valor monetário (Decimal/float) para extenso em português.

    Ex.: 1170.00 -> "mil cento e setenta reais"
    """
    if valor is None:
        return ""
    try:
        valor = float(valor)
    except Exception:
        return ""

    inteiro = int(valor)
    centavos = int(round((valor - inteiro) * 100))

    parte_inteira = _numero_extenso(inteiro)
    moeda = "real" if inteiro == 1 else "reais"

    if centavos:
        parte_centavos = _numero_extenso(centavos)
        cent = "centavo" if centavos == 1 else "centavos"
        texto = f"{parte_inteira} {moeda} e {parte_centavos} {cent}"
    else:
        texto = f"{parte_inteira} {moeda}"

    return texto
