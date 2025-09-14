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
        'PYG': 'fas fa-guarani-sign',  # Si existe, sino usar genérico
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
