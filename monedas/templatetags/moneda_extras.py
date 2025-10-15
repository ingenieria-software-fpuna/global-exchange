from django import template

register = template.Library()

@register.filter
def get_icono_moneda(codigo):
    """
    Retorna el icono de FontAwesome apropiado para cada moneda
    """
    iconos = {
        'USD': 'fas fa-dollar-sign',
        'EUR': 'fas fa-euro-sign',
        'BRL': 'fas fa-brazilian-real-sign',
        'ARS': 'fas fa-peso-sign',
        'GBP': 'fas fa-pound-sign',
        'JPY': 'fas fa-yen-sign',
        'CAD': 'fas fa-dollar-sign',
        'CHF': 'fas fa-franc-sign',
        'AUD': 'fas fa-dollar-sign',
        'CNY': 'fas fa-yen-sign',
        'MXN': 'fas fa-peso-sign',
        'INR': 'fas fa-rupee-sign',
        'RUB': 'fas fa-ruble-sign',
        'KRW': 'fas fa-won-sign',
        'SGD': 'fas fa-dollar-sign',
        'HKD': 'fas fa-dollar-sign',
        'NZD': 'fas fa-dollar-sign',
        'SEK': 'fas fa-krona-sign',
        'NOK': 'fas fa-krone-sign',
        'DKK': 'fas fa-krone-sign',
        'PLN': 'fas fa-zloty-sign',
        'CZK': 'fas fa-koruna-sign',
        'HUF': 'fas fa-forint-sign',
        'TRY': 'fas fa-lira-sign',
        'ZAR': 'fas fa-rand-sign',
        'BGN': 'fas fa-lev-sign',
        'RON': 'fas fa-leu-sign',
        'HRK': 'fas fa-kuna-sign',
        'ISK': 'fas fa-krona-sign',
        'UAH': 'fas fa-hryvnia-sign',
        'BYN': 'fas fa-ruble-sign',
        'KZT': 'fas fa-tenge-sign',
        'UZS': 'fas fa-som-sign',
        'KGS': 'fas fa-som-sign',
        'TJS': 'fas fa-somoni-sign',
        'AMD': 'fas fa-dram-sign',
        'GEL': 'fas fa-lari-sign',
        'AZN': 'fas fa-manat-sign',
        'TMT': 'fas fa-manat-sign',
        'UZS': 'fas fa-som-sign',
        'KGS': 'fas fa-som-sign',
        'TJS': 'fas fa-somoni-sign',
        'AMD': 'fas fa-dram-sign',
        'GEL': 'fas fa-lari-sign',
        'AZN': 'fas fa-manat-sign',
        'TMT': 'fas fa-manat-sign',
        'PYG': 'fas fa-guarani-sign', 
    }
    
    return iconos.get(codigo.upper(), 'fas fa-coins')  # Icono genérico por defecto

@register.filter
def formatear_tasa_para_display(tasa, decimales):
    """
    Formatea una tasa para mostrar en el template con el número correcto de decimales
    """
    if tasa is None:
        return "N/A"
    
    # Formatear con el número de decimales especificado
    formato = f"{{:.{decimales}f}}"
    return formato.format(float(tasa))

@register.filter
def formatear_guaranies(valor):
    """
    Formatea un valor en guaraníes con separadores de miles
    """
    if valor is None:
        return "N/A"
    
    try:
        # Convertir a entero si es necesario
        valor_int = int(valor)
        # Formatear con separadores de miles
        return f"₲ {valor_int:,}".replace(',', '.')
    except (ValueError, TypeError):
        return "N/A"

@register.filter
def formatear_denominacion(valor):
    """
    Formatea un valor de denominación para input type='number'
    Convierte comas a puntos para compatibilidad con HTML5
    """
    if valor is None:
        return ""
    
    try:
        # Convertir a string y reemplazar coma por punto
        valor_str = str(valor)
        if ',' in valor_str:
            valor_str = valor_str.replace(',', '.')
        return valor_str
    except (ValueError, TypeError):
        return ""

@register.filter
def formatear_denominacion_sin_decimales(valor, tipo):
    """
    Formatea un valor de denominación sin decimales para billetes
    """
    if valor is None:
        return ""
    
    try:
        # Para billetes, mostrar sin decimales
        if tipo == 'BILLETE':
            valor_int = int(float(valor))
            return str(valor_int)
        else:
            # Para monedas, mantener decimales
            valor_str = str(valor)
            if ',' in valor_str:
                valor_str = valor_str.replace(',', '.')
            return valor_str
    except (ValueError, TypeError):
        return ""

@register.filter
def formatear_denominacion_con_tipo(denominacion):
    """
    Formatea una denominación completa con valor y tipo
    """
    if denominacion is None:
        return ""
    
    try:
        # Formatear el valor
        valor_str = str(denominacion.valor)
        if ',' in valor_str:
            valor_str = valor_str.replace(',', '.')
        
        # Agregar información del tipo
        tipo_info = " (Billete)" if denominacion.tipo == 'BILLETE' else " (Moneda)"
        return f"{valor_str}{tipo_info}"
    except (ValueError, TypeError, AttributeError):
        return ""
