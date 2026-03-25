import json
import asyncio
import re
import time
import os
import sys

# Agregar la raíz del proyecto al sys.path temporalmente para poder importar 'utils'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from utils.helpers import limpiar_texto

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ Falta la librería Playwright. Para funcionar requieres instalarla:")
    print("   Abre la terminal y ejecuta estos dos comandos:")
    print("   pip install playwright")
    print("   playwright install chromium")
    exit(1)

# Configuración
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_ENTRADA = os.path.join(BASE_DIR, "data", "02_interim")
DIR_SALIDA = os.path.join(BASE_DIR, "data", "03_processed")
MAX_CONCURRENT_PAGES = 10  # Número de pestañas en paralelo (Multitarea asíncrona real)

async def procesar_tienda(context, tienda, sem, fallos_nicho):
    # El semáforo limita cuántas pestañas se abren al mismo tiempo para no colapsar la RAM
    async with sem:
        url = tienda.get("link")
        if not url: return tienda
        
        telefono = ""
        direccion = ""
        web = ""
        ig = fb = wa = ""
        
        max_reintentos = 3
        exito = False
        
        for intento in range(max_reintentos):
            try:
                page = await context.new_page()
                
                # 1. Navegar a la web y esperar que la red se calme
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                
                # 2. Esperar explícitamente a que el JavaScript de Google Maps inyecte los elementos
                selector_info = '.Io6YTe.fontBodyMedium.kR99db.fdkmkc'
                try:
                    await page.wait_for_selector(selector_info, timeout=5000)
                except:
                    pass # Si pasan 5s y no carga, procedemos igual por si ya cargaron algunos

                # 3. Extraer Dirección y Teléfono de los DIVs correspondientes
                textos = await page.locator(selector_info).all_inner_texts()
                
                for texto in textos:
                    texto = texto.strip()
                    if not texto: continue
                    # Detectar teléfono
                    if re.match(r'^[\+\d\s\-\(\)]{7,20}$', texto):
                        telefono = texto
                    # Detectar dirección
                    elif "Cra" in texto or "Cl" in texto or "Calle" in texto or "Carr" in texto or "#" in texto or "Tuluá" in texto or "Valle" in texto or "Sector" in texto:
                        direccion = texto

                # 4. Extraer el sitio web usando a.CsEnBe con data-item-id="authority"
                web_locator = page.locator('a.CsEnBe[data-item-id="authority"]')
                if await web_locator.count() > 0:
                    web = await web_locator.first.get_attribute('href')
                    if web: web = web.strip()

                # 5. Redes sociales (Buscamos enlaces ejecutando JS rápido en la página)
                hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => a.href)")
                for enlace in hrefs:
                    if "instagram.com" in enlace: ig = enlace.split('?')[0].split('\\\\')[0]
                    if "facebook.com" in enlace: fb = enlace.split('?')[0].split('\\\\')[0]
                    if "wa.me" in enlace or "api.whatsapp.com" in enlace: wa = enlace.split('\\\\')[0]
                
                exito = True
                break # Rompe el for de reintentos si procesó todo sin lanzar excepción de Timeout
                
            except Exception as e:
                # Si falla, esperamos 2 segundos y probamos de nuevo
                await asyncio.sleep(2)
            finally:
                if 'page' in locals() and not page.is_closed():
                    await page.close()  # Cerramos la pestaña independientemente
            
        if not exito:
            # Si se quemaron todos los reintentos sin éxito
            fallos_nicho.append({
                "nombre": tienda.get("nombre", "Desconocido"),
                "url": url,
                "motivo": "Fallo de conexión o Timeout tras 3 reintentos"
            })
            
        # Limpiar y asignar variables
        tienda["telefono"] = limpiar_texto(telefono)
        tienda["direccion"] = limpiar_texto(direccion)
        tienda["web"] = web
        tienda["instagram"] = ig
        tienda["facebook"] = fb
        tienda["whatsapp"] = wa
        
        # Validar si extrajo algo
        estado = "✅" if (telefono or direccion or web) else "⚠️"
        print(f"{estado} {tienda['nombre'][:25]:<25} | Dir: {tienda['direccion'][:15]:<15} | Tel: {tienda['telefono']}")
        
        return tienda

import glob

async def main_async():
    print("🚀 Iniciando Extractor Multitarea Asíncrono (Playwright)")
    print("🤖 Esperando a que el JS de Google Maps genere los elementos para poder extraerlos...")
    
    archivos_entrada = glob.glob(os.path.join(DIR_ENTRADA, "*_links.json"))
    
    if not archivos_entrada:
        print(f"❌ Error: No se encontraron archivos *_links.json en '{DIR_ENTRADA}'.")
        return

    # Iniciar motor Playwright de forma global para todos los archivos
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        for archivo_entrada in archivos_entrada:
            nombre_base = os.path.basename(archivo_entrada)
            nicho_nombre = nombre_base.replace("_links.json", "")
            archivo_salida = os.path.join(DIR_SALIDA, f"{nicho_nombre}_enriquecidas.json")
            
            print(f"\\n{'='*50}")
            print(f"📦 Procesando Nicho: {nicho_nombre.upper()}")
            print(f"{'='*50}")
            
            try:
                with open(archivo_entrada, "r", encoding="utf-8") as f:
                    tiendas = json.load(f)
            except Exception as e:
                print(f"❌ Error al leer '{archivo_entrada}': {e}")
                continue

            tiendas_validas = [t for t in tiendas if t.get("link") and "google.com/maps" in t.get("link")]
            print(f"📝 {len(tiendas_validas)} lugares de '{nicho_nombre}' concurrentes ({MAX_CONCURRENT_PAGES} a la vez).")
            
            start_time = time.time()
            sem = asyncio.Semaphore(MAX_CONCURRENT_PAGES)
            fallos_nicho = []
            
            # Agrupar las tareas
            tareas = [procesar_tienda(context, t, sem, fallos_nicho) for t in tiendas_validas]
            
            # Ejecutar de forma simultánea todas las tareas para un nicho
            if tareas:
                resultados = await asyncio.gather(*tareas)
                
                tiempo_total = time.time() - start_time
                
                # Escribir el archivo con lo recopilado
                with open(archivo_salida, "w", encoding="utf-8") as f:
                    json.dump(resultados, f, ensure_ascii=False, indent=4)
                    
                print(f"🎉 Proceso de '{nicho_nombre}' Terminado en {tiempo_total:.2f} segundos!")
                print(f"💾 Guardados en {archivo_salida}")
                
                if fallos_nicho:
                    archivo_fallos = os.path.join(DIR_SALIDA, f"{nicho_nombre}_alertas_fallos.json")
                    with open(archivo_fallos, "w", encoding="utf-8") as f:
                        json.dump(fallos_nicho, f, ensure_ascii=False, indent=4)
                    print(f"⚠️ Atención: Hubo {len(fallos_nicho)} fallos de red persistentes registrados en '{archivo_fallos}'")
            else:
                print(f"⚠️ No se encontraron enlaces válidos en '{archivo_entrada}'.")

        await browser.close()
        print("\\n🌟 ¡Todos los nichos han sido procesados y enriquecidos exitosamente!")

if __name__ == "__main__":
    # Arrancar de forma correcta el código asíncrono
    asyncio.run(main_async())