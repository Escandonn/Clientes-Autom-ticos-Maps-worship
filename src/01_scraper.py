import json
import time
import os
import urllib.parse
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from utils.data_manager import DataManager
from utils.municipios import MUNICIPIOS_VALLE_CAUCA

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

def obtener_url_mapas(nicho, municipio):
    query = f"{nicho} en {municipio}, Valle del Cauca, Colombia"
    query_encodeado = urllib.parse.quote(query)
    return f"https://www.google.com/maps/search/{query_encodeado}/"

def scroll_results(sb, nicho, municipio):
    print(f"📜 Iniciando scroll para cargar más {nicho} en {municipio}...")
    last_count = 0
    intentos_sin_nuevos = 0
    
    for iteracion in range(30): 
        for sub_scroll in range(3):
            script_scroll = """
                (function() {
                    var container = document.querySelector('div[role="feed"]') || document.querySelector('.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde.ecceSd');
                    if(container) {
                        container.scrollBy(0, 800);
                    }
                })();
            """
            sb.execute_script(script_scroll)
            sb.sleep(1)
            
        sb.sleep(3)
        
        current_count = sb.execute_script('return (function(){ return document.querySelectorAll("a.hfpxzc").length; })();')
        print(f"🔄 {current_count} resultados cargados hasta ahora...")
        
        if current_count == last_count:
            intentos_sin_nuevos += 1
            if intentos_sin_nuevos >= 2:
                print(f"✅ Final de la lista alcanzado para {nicho} en {municipio}.")
                break
        else:
            intentos_sin_nuevos = 0
            
        last_count = current_count

from seleniumbase import SB

if __name__ == "__main__":
    manager = DataManager()
    
    print(f"🚀 Iniciando extracción masiva en {len(MUNICIPIOS_VALLE_CAUCA)} municipios del Valle del Cauca.")
    
    with SB(uc=True, headless=False) as sb:
        for municipio in MUNICIPIOS_VALLE_CAUCA:
            print(f"\\n\\n{'#'*60}")
            print(f"📍 EXPLORANDO MUNICIPIO: {municipio.upper()}")
            print(f"{'#'*60}\\n")
            
            for nicho in NICHOS:
                # 0️⃣ Checkpointing (POO)
                if manager.check_interim_exists(nicho, municipio):
                    print(f"⏩ SALTANDO: {nicho.upper()} en {municipio} (Ya existe archivo)")
                    continue

                print(f"\\n{'='*50}")
                print(f"🔍 EXTRACCIÓN: {nicho.upper()} -> {municipio}")
                print(f"{'='*50}")
                
                url_nicho = obtener_url_mapas(nicho, municipio)
                
                # 1️⃣ Abrir link
                sb.open(url_nicho)
                sb.sleep(5)

                # 4️⃣ Scroll progresivo
                scroll_results(sb, nicho, municipio)

                # 5️⃣ Extraer etiquetas masivamente con JavaScript puro
                print("⚡ Extrayendo etiquetas locales...")
                script_extract = """
                    (function() {
                        var items = document.querySelectorAll("a.hfpxzc");
                        var data = [];
                        for (var i = 0; i < items.length; i++) {
                            var a = items[i];
                            var nombre_completo = a.getAttribute("aria-label") || "Desconocido";
                            var nombre_limpio = nombre_completo.split('·')[0].trim();
                            var link = a.getAttribute("href") || "";
                            data.push({"nombre": nombre_limpio, "link": link});
                        }
                        return data;
                    })();
                """
                
                resultados_json = sb.execute_script(script_extract)
                
                # Guardar usando DataManager
                ruta_guardado = manager.get_interim_path(nicho, municipio)
                manager.save_json(resultados_json, ruta_guardado)
                
                print(f"✅ ¡Extraídos {len(resultados_json)} lugares!")
                print(f"💾 Guardado en: {ruta_guardado}")
                
        print("\\n🎉 Etapa 1 Terminada: ¡Todo el departamento ha sido procesado!")