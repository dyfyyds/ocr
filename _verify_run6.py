from playwright.sync_api import sync_playwright
BASE="http://localhost:18088"
uniq=open("_verify/_pending.txt",encoding="utf-8").read().strip().split("|")[1]
def log(*a): print(*a, flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True); pg=b.new_page(viewport={"width":1480,"height":1000})
    pg.set_default_timeout(40000)
    pg.goto(BASE, wait_until="networkidle")
    pg.fill('input[autocomplete="username"]',"admin"); pg.fill('input[autocomplete="current-password"]',"123456")
    pg.click('form button[type="submit"]'); pg.wait_for_timeout(2500)
    pg.click('text=立项终审中心'); pg.wait_for_timeout(1500)
    # find the row for our pending project (HT-W5-001) and click its review button
    row=pg.locator('tr', has=pg.get_by_text("HT-W5-001")).first
    row.locator('button:has-text("查看提取比对并评审")').click()
    pg.wait_for_timeout(1000)
    panel=pg.inner_text('.glass-panel-elevated')
    pg.screenshot(path="_verify/22_admin_real_desc.png", full_page=True)
    log("admin audit panel shows REAL submitted description:", uniq in panel)
    log("panel contains OLD fake quote '判定为字符编码':", "判定为字符编码" in panel)
    b.close()
