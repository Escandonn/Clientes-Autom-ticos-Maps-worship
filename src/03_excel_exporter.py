import os
import sys
import glob
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from utils.data_manager import DataManager

# Usamos la misma lista que en el scraper para buscar coincidencias exactas
NICHOS = [
    "tiendas", "cafeterias", "tiendas de mascotas", "restaurantes",
    "droguerias", "ferreterias", "peluquerias", "panaderias", "talleres de mecanica"
]

if __name__ == "__main__":
    manager = DataManager()
    
    print("🚀 Iniciando Etapa 3: Exportación Estructurada a Excel (POO)")
    print(f"Buscando JSONs enriquecidos en: {manager.processed_dir}")
    
    archivos_procesados = glob.glob(os.path.join(manager.processed_dir, "*_enriquecidas.json"))
    
    if not archivos_procesados:
        print("❌ No se encontraron archivos enriquecidos para procesar.")
        sys.exit(0)
        
    print(f"📦 Se encontraron {len(archivos_procesados)} archivos procesados.")
    
    # Agrupar archivos por nicho
    archivos_por_nicho = defaultdict(list)
    
    for path in archivos_procesados:
        filename = os.path.basename(path)
        
        # Encontrar a qué nicho pertenece el archivo
        nicho_encontrado = None
        for nicho in NICHOS:
            nicho_seguro = manager.safe_filename(nicho)
            if filename.startswith(f"{nicho_seguro}_"):
                nicho_encontrado = nicho
                break
                
        if nicho_encontrado:
            archivos_por_nicho[nicho_encontrado].append(path)
        else:
            print(f"⚠️ No se pudo determinar el nicho para '{filename}', será ignorado.")
            
    # Exportar cada grupo a Excel utilizando el gestor de datos (POO)
    print("\\n" + "="*50)
    for nicho, paths in archivos_por_nicho.items():
        manager.exportar_nicho_a_excel(nicho, paths)
        
    print("="*50 + "\\n🎉 ¡Exportación masiva a Excel completada con éxito!")
