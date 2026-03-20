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
ARCHIVO_ENTRADA = os.path.join(BASE_DIR, "data", "02_interim", "tiendas_links.json")
ARCHIVO_SALIDA = os.path.join(BASE_DIR, "data", "03_processed", "tiendas_enriquecidas.json")
MAX_CONCURRENT_PAGES = 10  # Número de pestañas en paralelo (Multitarea asíncrona real)

MAX_CONCURRENT_PAGES = 10  # Número de pestañas en paralelo (Multitarea asíncrona real)

async def procesar_tienda(context, tienda, sem):
    # El semáforo limita cuántas pestañas se abren al mismo tiempo para no colapsar la RAM
    async with sem:
        url = tienda.get("link")
        if not url: return tienda
        
        page = await context.new_page()
        
        telefono = ""
        direccion = ""
        web = ""
        ig = fb = wa = ""
        
        try:
            # 1. Navegar a la web y esperar que la red se calme
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            
            # 2. Esperar explícitamente a que el JavaScript de Google Maps inyecte los elementos
            # Los selectores proporcionados por ti:
            selector_info = '.Io6YTe.fontBodyMedium.kR99db.fdkmkc'
            try:
                await page.wait_for_selector(selector_info, timeout=5000)
            except:
                pass # Si pasan 5s y no carga, procedemos igual por si ya cargaron algunos

            # 3. Extraer Dirección y Teléfono de los DIVs correspondientes
            # locator.all_inner_texts() obtiene los textos de todos los divs que coinciden con esa clase exactamante
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
                # get_attribute para obtener el enlace href
                web = await web_locator.first.get_attribute('href')
                if web: web = web.strip()

            # 5. Redes sociales (Buscamos enlaces ejecutando JS rápido en la página)
            hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => a.href)")
            for enlace in hrefs:
                if "instagram.com" in enlace: ig = enlace.split('?')[0].split('\\')[0]
                if "facebook.com" in enlace: fb = enlace.split('?')[0].split('\\')[0]
                if "wa.me" in enlace or "api.whatsapp.com" in enlace: wa = enlace.split('\\')[0]
            
        except Exception as e:
            pass # Si da error alguna página, que no se detenga el código entero
        finally:
            await page.close()  # Cerramos la pestaña muy rápido para liberar memoria
            
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

async def main_async():
    print("🚀 Iniciando Extractor Multitarea Asíncrono (Playwright)")
    print("🤖 Esperando a que el JS de Google Maps genere los elementos para poder extraerlos...")
    
    try:
        with open(ARCHIVO_ENTRADA, "r", encoding="utf-8") as f:
            tiendas = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró '{ARCHIVO_ENTRADA}'.")
        return

    tiendas_validas = [t for t in tiendas if t.get("link") and "google.com/maps" in t.get("link")]
    print(f"📦 Procesando {len(tiendas_validas)} tiendas simultáneamente ({MAX_CONCURRENT_PAGES} a la vez).")
    
    start_time = time.time()
    
    # Iniciar motor Playwright
    async with async_playwright() as p:
        # Abrimos SOLO 1 navegador (chromium) oculto
        browser = await p.chromium.launch(headless=True)
        # Context es muchísimo más ligero que abrir navegadores separados
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        sem = asyncio.Semaphore(MAX_CONCURRENT_PAGES)
        
        # Agrupar las tareas
        tareas = [procesar_tienda(context, t, sem) for t in tiendas_validas]
        
        # Ejecutar de forma simultánea todas las tareas
        resultados = await asyncio.gather(*tareas)
        
        await browser.close()
        
    tiempo_total = time.time() - start_time
    
    # Escribir el archivo con lo recopilado
    with open(ARCHIVO_SALIDA, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=4)
        
    print("-" * 60)
    print(f"🎉 Proceso Terminado en {tiempo_total:.2f} segundos!")
    print(f"💾 Guardados en {ARCHIVO_SALIDA}")

if __name__ == "__main__":
    # Arrancar de forma correcta el código asíncrono
    asyncio.run(main_async())