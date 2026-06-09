from playwright.sync_api import sync_playwright
BASE="http://localhost:18088"; errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True); pg=b.new_page(viewport={"width":1440,"height":900})
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" and "5173" not in m.text else None)
    pg.on("pageerror", lambda e: errs.append("PAGEERROR: "+str(e)))
    pg.goto(BASE, wait_until="domcontentloaded")
    pg.fill('input[autocomplete="username"]',"admin"); pg.fill('input[autocomplete="current-password"]',"123456")
    pg.click('form button[type="submit"]'); pg.wait_for_timeout(3500)
    ok = pg.locator('.tilt-card h3').count() >= 4
    print("dashboard rendered:", ok)
    print("app console errors (excl. vite-hmr):", errs or "NONE ✓")
    b.close()
