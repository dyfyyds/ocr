import json
from playwright.sync_api import sync_playwright

BASE="http://localhost:18088"
net=[]; errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_page(viewport={"width":1440,"height":900})
    pg.on("response", lambda r: net.append((r.request.method, r.url, r.status)) if "/api/" in r.url else None)
    pg.on("console", lambda m: errs.append(f"{m.type}: {m.text}") if m.type in ("error","warning") else None)
    pg.on("pageerror", lambda e: errs.append(f"pageerror: {e}"))

    pg.goto(BASE, wait_until="networkidle")
    pg.screenshot(path="_verify/01_login.png")

    pg.fill('input[autocomplete="username"]', "admin")
    pg.fill('input[autocomplete="current-password"]', "123456")
    pg.click('form button[type="submit"]')
    pg.wait_for_timeout(3500)
    pg.screenshot(path="_verify/02_dashboard.png", full_page=True)

    # pull real numbers rendered in the DOM
    body = pg.inner_text("body")
    # check for old mock literals anywhere in rendered app
    mock_hits = [s for s in ["HT-2026-088","580,000","420000","智能大屏数据可视化","网信政务"] if s in body]

    api_calls=[f"{m} {u.split('/api/')[-1]} -> {s}" for (m,u,s) in net]
    login_ok=any("/api/auth/login" in u and s==200 for (m,u,s) in net)
    proj_ok=any("/api/projects" in u and s==200 for (m,u,s) in net)

print("=== API CALLS (real network) ===")
print("\n".join(api_calls) or "(none)")
print("\nlogin 200:", login_ok, "| projects 200:", proj_ok)
print("mock literals in rendered DOM:", mock_hits or "NONE ✓")
print("console errors/warnings:", errs or "NONE ✓")
