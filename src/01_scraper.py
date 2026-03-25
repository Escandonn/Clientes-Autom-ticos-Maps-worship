import json
import time
import os
import urllib.parse

NICHOS = [
    "tiendas",
    "cafeterias",
    "tiendas de mascotas",
    "restaurantes",
    "droguerias",
    "ferreterias",
    "peluquerias",
    "panaderias",
    "talleres de mecanica"
]

def obtener_url_mapas(nicho):
    nicho_encodeado = urllib.parse.quote(nicho)
    return f"https://www.google.com/maps/search/{nicho_encodeado}/@4.0844249,-76.1983878,3513m/data=!3m2!1e3!4b1?entry=ttu&g_ep=EgoyMDI2MDMxNS4wIKXMDSoASAFQAw%3D%3D"

def scroll_results(sb, nicho):
    print(f"📜 Iniciando scroll progresivo para cargar más {nicho}...")
    last_count = 0
    intentos_sin_nuevos = 0
    
    # Intentamos bajar progresivamente
    for iteracion in range(30): 
        # Hacemos 3 pequeños scrolls imitando el salto de una rueda de ratón (mouse wheel)
        for sub_scroll in range(3):
            script_scroll = """
                (function() {
                    var container = document.querySelector('div[role="feed"]') || document.querySelector('.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde.ecceSd');
                    if(container) {
                        // En lugar de ir al fondo de golpe, bajamos de a 800 píxeles
                        container.scrollBy(0, 800);
                    }
                })();
            """
            sb.execute_script(script_scroll)
            sb.sleep(1) # pausa entre cada pequeño salto
            
        sb.sleep(3) # Pausa al final de los 3 saltos para validar la carga de la página
        
        # Validamos cuántas tiendas hay en memoria ahora
        current_count = sb.execute_script('return (function(){ return document.querySelectorAll("a.hfpxzc").length; })();')
        print(f"🔄 {nicho.capitalize()} descubiertas hasta ahora: {current_count}")
        
        if current_count == last_count:
            intentos_sin_nuevos += 1
            if intentos_sin_nuevos >= 2:
                print(f"✅ Ya llegamos al final de la lista para {nicho}, no aparecen más resultados.")
                break
        else:
            intentos_sin_nuevos = 0 # resetear al encontrar más resultados
            
        last_count = current_count

from seleniumbase import SB

with SB(uc=True, headless=False) as sb:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    for nicho in NICHOS:
        nombre_archivo_seguro = nicho.replace(" ", "_").lower()
        nombre_archivo = os.path.join(BASE_DIR, "data", "02_interim", f"{nombre_archivo_seguro}_links.json")
        
        # 0️⃣ Checkpointing: Si el archivo ya existe (y tiene datos), saltamos este nicho
        if os.path.exists(nombre_archivo):
            print(f"\\n{'='*50}")
            print(f"⏩ SALTANDO: {nicho.upper()} (Ya extraído en sesiones anteriores)")
            print(f"{'='*50}\\n")
            continue

        print(f"\\n{'='*50}")
        print(f"🔍 INICIANDO EXTRACCIÓN PARA EL NICHO: {nicho.upper()}")
        print(f"{'='*50}\\n")
        
        url_nicho = obtener_url_mapas(nicho)
        
        # 1️⃣ Abrir link
        sb.open(url_nicho)
        sb.sleep(5)

        # 4️⃣ Scroll progresivo
        scroll_results(sb, nicho)

        # 5️⃣ Extraer etiquetas masivamente con JavaScript puro
        print("⚡ Extrayendo etiquetas de forma masiva y rápida...")
        script_extract = """
            (function() {
                var items = document.querySelectorAll("a.hfpxzc");
                var data = [];
                for (var i = 0; i < items.length; i++) {
                    var a = items[i];
                    var nombre_completo = a.getAttribute("aria-label") || "Desconocido";
                    var nombre_limpio = nombre_completo.split('·')[0].trim(); // Limpiamos "· Vínculo visitado"
                    
                    var link = a.getAttribute("href") || "";
                    
                    data.push({
                        "nombre": nombre_limpio,
                        "link": link
                    });
                }
                return data;
            })();
        """
        
        resultados_json = sb.execute_script(script_extract)
        
        # Guardar a archivo JSON
        with open(nombre_archivo, "w", encoding="utf-8") as f:
            json.dump(resultados_json, f, ensure_ascii=False, indent=4)
            
        print(f"✅ ¡Extraídos {len(resultados_json)} lugares de {nicho} en 1 segundo!")
        print(f"💾 Guardados en '{nombre_archivo}'")
        
    print("\\n🎉 Etapa 1 Terminada: ¡Todos los nichos extraídos!")