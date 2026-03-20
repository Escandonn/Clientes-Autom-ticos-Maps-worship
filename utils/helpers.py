import re

def limpiar_texto(texto):
    """
    Limpia el texto extraído eliminando iconos de Maps
    y prefijos comunes como 'Dirección:' o 'Teléfono:'.
    """
    if not texto: 
        return ""
    
    # Quitar íconos comunes que inyecta Google Maps
    texto = texto.replace('\ue0c8', '').replace('\ue0b0', '').replace('\ue80b', '')
    
    # Quitar prefijos que añade Maps
    texto = re.sub(r'^(Dirección:\s*|Teléfono:\s*)', '', texto)
    
    return texto.strip()
