from playwright.sync_api import sync_playwright
BASE="http://localhost:18088"; net=[]
def log(*a): print(*a, flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True); pg=b.new_page(viewport={"width":1440,"height":950})
    pg.on("response", lambda r: net.append((r.request.method, r.url.split('/api/')[-1], r.status)) if "/api/dashboard/" in r.url else None)
    pg.set_default_timeout(40000)
    pg.goto(BASE, wait_until="networkidle")
    pg.fill('input[autocomplete="username"]',"admin"); pg.fill('input[autocomplete="current-password"]',"123456")
    pg.click('form button[type="submit"]'); pg.wait_for_timeout(4000)
    pg.screenshot(path="_verify/11_dashboard_backend.png", full_page=True)
    # read the 4 stat-card values from the DOM
    cards = pg.eval_on_selector_all('.tilt-card h3', "els => els.map(e => e.textContent.trim())")
    log("=== /api/dashboard/* requests ===")
    for m,u,s in net: log(f"  {m} {u} -> {s}")
    log("\nstat cards rendered:", cards)
    b.close()
