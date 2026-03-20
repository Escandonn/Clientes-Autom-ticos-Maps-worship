import json
import time
import os

URL = "https://www.google.com/maps/search/tiendas/@4.0844249,-76.1983878,3513m/data=!3m2!1e3!4b1?entry=ttu&g_ep=EgoyMDI2MDMxNS4wIKXMDSoASAFQAw%3D%3D"

def scroll_results(sb):
    print("📜 Iniciando scroll progresivo para cargar más tiendas...")
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
        print(f"🔄 Tiendas descubiertas hasta ahora: {current_count}")
        
        if current_count == last_count:
            intentos_sin_nuevos += 1
            if intentos_sin_nuevos >= 2:
                print("✅ Ya llegamos al final de la lista, no aparecen nuevas tiendas.")
                break
        else:
            intentos_sin_nuevos = 0 # resetear al encontrar más resultados
            
        last_count = current_count

with SB(uc=True, headless=False) as sb:
    # 1️⃣ Abrir link
    sb.open(URL)
    sb.sleep(5)

    # 4️⃣ Scroll progresivo
    scroll_results(sb)

    # 5️⃣ Extraer etiquetas masivamente con JavaScript puro (Parte 1: ultra rápida)
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
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    nombre_archivo = os.path.join(BASE_DIR, "data", "02_interim", "tiendas_links.json")
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        json.dump(resultados_json, f, ensure_ascii=False, indent=4)
        
    print(f"✅ ¡Extraídas {len(resultados_json)} tiendas en 1 segundo!")
    print(f"💾 Guardadas en '{nombre_archivo}' (Etapa 1 Terminada)")