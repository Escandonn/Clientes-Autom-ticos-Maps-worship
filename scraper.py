from seleniumbase import SB

URL = "https://www.google.com/maps/@4.0894464,-76.2150912,14z?authuser=1&entry=ttu&g_ep=EgoyMDI2MDMxNS4wIKXMDSoASAFQAw%3D%3D"

with SB(uc=True, headless=False) as sb:
    # 1️⃣ Abrir link
    sb.open(URL)
    sb.sleep(5)

    # 2️⃣ Escribir "tiendas"
    sb.click('input[name="q"]')
    sb.type('input[name="q"]', 'tiendas')
    sb.sleep(1)

    # 3️⃣ Click buscar
    sb.click('button[aria-label="Buscar"]')
    sb.sleep(5)