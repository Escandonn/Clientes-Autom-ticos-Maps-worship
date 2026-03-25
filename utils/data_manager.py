import os
import json
import re
import unicodedata
import pandas as pd

class DataManager:
    """Clase para la gestión centralizada de archivos JSON y conversión a Excel."""
    
    def __init__(self, base_dir=None):
        if base_dir is None:
            # Apunta a la raíz del proyecto asumiendo que este script está en /utils/
            self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.base_dir = base_dir
            
        self.raw_dir = os.path.join(self.base_dir, "data", "01_raw")
        self.interim_dir = os.path.join(self.base_dir, "data", "02_interim")
        self.processed_dir = os.path.join(self.base_dir, "data", "03_processed")
        self.exports_dir = os.path.join(self.base_dir, "data", "04_exports")
        
        self._crear_directorios()
        
    def _crear_directorios(self):
        for directorio in [self.raw_dir, self.interim_dir, self.processed_dir, self.exports_dir]:
            os.makedirs(directorio, exist_ok=True)
            
    def safe_filename(self, text):
        """Convierte texto en formato seguro para nombres de archivo."""
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
        return re.sub(r'[^a-zA-Z0-9]', '_', text).lower()
            
    def get_interim_path(self, nicho, municipio):
        nicho_seguro = self.safe_filename(nicho)
        muni_seguro = self.safe_filename(municipio)
        return os.path.join(self.interim_dir, f"{nicho_seguro}_{muni_seguro}_links.json")
        
    def get_processed_path(self, nicho, municipio):
        nicho_seguro = self.safe_filename(nicho)
        muni_seguro = self.safe_filename(municipio)
        return os.path.join(self.processed_dir, f"{nicho_seguro}_{muni_seguro}_enriquecidas.json")
        
    def get_error_log_path(self, nicho, municipio):
        nicho_seguro = self.safe_filename(nicho)
        muni_seguro = self.safe_filename(municipio)
        return os.path.join(self.processed_dir, f"{nicho_seguro}_{muni_seguro}_alertas_fallos.json")

    def check_interim_exists(self, nicho, municipio):
        return os.path.exists(self.get_interim_path(nicho, municipio))
        
    def save_json(self, data, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
    def load_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def exportar_nicho_a_excel(self, nicho, json_paths):
        """Toma una lista de rutas de JSONs en procesados y crea un 
        Excel con hojas separadas por municipio (para ese nicho particular)."""
        if not json_paths:
            print(f"⚠️ No hay archivos de datos para generar reporte de '{nicho}'.")
            return
            
        nicho_seguro = self.safe_filename(nicho)
        excel_path = os.path.join(self.exports_dir, f"{nicho_seguro}_directorio.xlsx")
        
        # Agrupamos por Dataframes
        print(f"📊 Empaquetando {len(json_paths)} municipios en el Excel de {nicho.upper()}...")
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            for path in sorted(json_paths):
                # Extraer municipio del nombre archivo "{nicho}_{municipio}_enriquecidas.json"
                filename = os.path.basename(path)
                muni_part = filename.replace(f"{nicho_seguro}_", "").replace("_enriquecidas.json", "")
                
                try:
                    data = self.load_json(path)
                    df = pd.DataFrame(data)
                    # Sheet name max 31 chars
                    sheet_name = muni_part[:31].capitalize().replace('_', ' ')
                    
                    if df.empty:
                        # Si está vacío, generamos tabla vacía
                        df = pd.DataFrame(columns=["nombre", "link", "telefono", "direccion", "web", "instagram", "facebook", "whatsapp"])
                        
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                except Exception as e:
                    print(f"❌ Error al exportar la hoja {filename}: {e}")
                    
        print(f"✅ Excel consolidado creado exitosamente: {excel_path}")
