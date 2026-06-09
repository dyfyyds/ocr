from playwright.sync_api import sync_playwright
BASE="http://localhost:18088"
def log(*a): print(*a, flush=True)
def totals(pg):
    hs=pg.eval_on_selector_all('h4', "els=>els.map(e=>e.textContent.trim()).filter(t=>t.startsWith('¥'))")
    return hs[:4]
with sync_playwright() as p:
    b=p.chromium.launch(headless=True); pg=b.new_page(viewport={"width":1440,"height":950})
    pg.set_default_timeout(40000)
    pg.goto(BASE, wait_until="networkidle")
    pg.fill('input[autocomplete="username"]',"finance"); pg.fill('input[autocomplete="current-password"]',"123456")
    pg.click('form button[type="submit"]'); pg.wait_for_timeout(2500)
    pg.click('text=查询汇总报表'); pg.wait_for_timeout(1500)
    pg.screenshot(path="_verify/12_finance_query_2026.png", full_page=True)
    log("year=2026 (default) [合同/开票/回款/应收]:", totals(pg))
    ysel=pg.locator('select:visible').nth(0); msel=pg.locator('select:visible').nth(1)
    ysel.select_option(index=1); pg.wait_for_timeout(800)   # 2025
    log("year=2025:", totals(pg))
    ysel.select_option(index=0); pg.wait_for_timeout(400)   # back to 2026
    log("year=2026 again:", totals(pg))
    # sweep months to find which holds the real invoices
    hits=[]
    for m in range(1,13):
        msel.select_option(index=m); pg.wait_for_timeout(150)
        t=totals(pg)
        if len(t)>1 and t[1] not in ('¥ 0','¥ 0.00','¥0',''): hits.append((m,t[1],t[2] if len(t)>2 else ''))
    log("months with invoiced>0 (month, 开票, 回款):", hits)
    msel.select_option(index=0); pg.wait_for_timeout(300)   # 全年
    pg.screenshot(path="_verify/13_finance_query_filtered.png", full_page=True)
    b.close()
