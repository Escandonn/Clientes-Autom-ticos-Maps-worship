# 🚀 Clientes Automáticos Maps - Worship

## 📖 Descripción del Proyecto
Este ecosistema automatizado de extracción avanzada (Web Scraping) está diseñado para recolectar clientes potenciales de Google Maps. 

El flujo está estructurado en un **Pipeline de dos etapas (Fase 2 de Arquitectura)** que combina técnicas de evasión de bloqueos con *SeleniumBase* en su primera mitad, y extracción ultrarrápida multihilo asíncrona con *Playwright* en su segunda mitad. Todo rediseñado bajo estándares profesionales separando lógica fuente (`src`), utilidades (`utils`), y almacenamiento progresivo de datos (`data`).

---

## 🏗️ Arquitectura del Proyecto (Fase 2)

El directorio de este proyecto obedece a buenas prácticas de ingeniería de software, enfocándose en la modularidad y separación de componentes.

```mermaid
graph TD
    A[clientes-potenciales/] --> B(data/)
    A --> C(src/)
    A --> D(utils/)
    
    B --> B1(01_raw/)
    subgraph Almacenamiento
    B2(02_interim/)
    B3(03_processed/)
    end
    B --> B2
    B --> B3
    
    subgraph Scripts Fuente
    C1(01_scraper.py)
    C2(02_extractor_pro.py)
    end
    C --> C1
    C --> C2
    
    D --> D1(helpers.py)
    
    C1 -->|Crea JSON de links| B2
    C2 -->|Crea JSON final de contactos| B3
    D1 -.->|Usa funcion| C2
```

---

## 🔄 Diagrama de Flujo (Pipeline Paso a Paso)

El siguiente modelo de secuencia demuestra cómo interactúa cada componente con su base de datos designada dentro del nuevo esquema de la Fase 2.

```mermaid
sequenceDiagram
    autonumber
    participant U as Usuario
    participant S1 as src/01_scraper.py
    participant DB1 as data/02_interim/
    participant S2 as src/02_extractor_pro.py
    participant DB2 as data/03_processed/
    
    U->>S1: Ejecuta Etapa 1
    Note over S1: Emulación humana con SeleniumBase
    S1->>S1: Itera sobre lista de Nichos
    S1->>S1: Abre Google Maps y Scroll progresivo
    S1->>DB1: Guarda {nicho}_links.json
    
    U->>S2: Ejecuta Etapa 2
    Note over S2: Multitarea asíncrona con Playwright
    S2->>DB1: Descubre y lee todos los *_links.json
    S2->>S2: Lanza Contexto (Max 10 pestañas paralelas)
    S2->>S2: Espera carga JS e inyección de .Io6YTe y .CsEnBe
    S2->>S2: Extrae Teléfono, Dirección, Sitio Web, IG, WA
    S2->>DB2: Escribe {nicho}_enriquecidas.json
    DB2-->>U: ¡Clientes potenciales listos para venta!
```

---

## 🧠 Diagrama de Clases y Funciones Conceptuales

El diseño base que representa la orientación del código detrás de cada script que compone este ecosistema.

```mermaid
classDiagram
    %% Etapa 1
    class ScraperBase {
        +String URL_OBJETIVO
        +String ARCHIVO_SALIDA
        +__init__()
        +scroll_progresivo(sb) void
        +extraer_etiquetas_javascript() List_Dict
        +guardar_json()
    }
    
    %% Helper
    class UtilidadesCompartidas {
        <<Utility>>
        +limpiar_texto(texto: String) String
    }
    
    %% Etapa 2
    class ExtractorProAsync {
        +Int MAX_PAGINAS_PARALELAS
        +String ARCHIVO_ENTRADA
        +String ARCHIVO_SALIDA
        +main_async()
        +procesar_tienda(contexto, tienda, semaforo) Dict
    }
    
    ExtractorProAsync ..> UtilidadesCompartidas : "Importa para limpiar HTML"
    ScraperBase --> ExtractorProAsync : "Abastece de links"
```

---

## ⚙️ Instalación y Requisitos

Si estás clonando el proyecto en un nuevo entorno, asegúrate de tener todo lo necesario.

### 1. Prerrequisitos
- Python 3.9 o superior

### 2. Archivo de Dependencias
Abre tu terminal y ejecuta:
```bash
pip install seleniumbase playwright
playwright install chromium
```

---

## 🚀 Guía de Uso Rápido

### Etapa 1 (Minería de Enlaces)
Se encarga de engañar a Google para descubrir de forma rápida y legal todos los locales que aparezcan en un área seleccionada, iterando automáticamente sobre una lista de nichos (tiendas, restaurantes, farmacias, etc.). **Implementa Checkpointing (Reanudación automática)**, por lo que si el código se interrumpe, retomará inteligentemente desde el progreso actual saltándose archivos existentes. Los resultados se guardan en la carpeta temporal de datos intermedios como archivos separados por nicho.
```bash
python src/01_scraper.py
```

### Etapa 2 (Enriquecimiento Simultáneo)
Procesa automáticamente todos los archivos JSON de nichos generados en la etapa anterior. Toma en paralelo 10 URLs por lote desde los datos intermedios y usa contextos fantasma súper-rápidos que permiten extraer contactos ocultos por JavaScript. **Integra Lógica de Reintentos (Retry Automático)** que intenta abrir el local hasta 3 veces si detecta bloqueos de red, generando registros de depuración precisos (`alertas_fallos.json`) con las tiendas imposibles de acceder. Los contactos exitosos se consolidan en archivos JSON separados por nicho listos para su uso.
```bash
python src/02_extractor_pro.py
```
