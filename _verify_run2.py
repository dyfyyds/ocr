import json
from playwright.sync_api import sync_playwright
BASE="http://localhost:18088"
DOCX=r"D:\course\ocr\OCR-docker\uploads\contracts\0fc25e4528dd472bbd8e67028f83dabe.docx"; PDF=r"D:\course\ocr\OCR-docker\uploads\contracts\259ba47ba1614375b50ee4e47ad4c044.pdf"
net=[]; phase="start"
def log(*a): print(*a, flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_page(viewport={"width":1440,"height":1000})
    pg.on("response", lambda r: net.append((r.request.method, r.url.split('/api/')[-1] if '/api/' in r.url else r.url, r.status)) if "/api/" in r.url else None)
    pg.set_default_timeout(45000)
    try:
        phase="login"; pg.goto(BASE, wait_until="networkidle")
        pg.fill('input[autocomplete="username"]', "business")
        pg.fill('input[autocomplete="current-password"]', "123456")
        pg.click('form button[type="submit"]'); pg.wait_for_timeout(2500)
        phase="nav-register"; pg.click('text=智能立项登记'); pg.wait_for_timeout(800)
        pg.screenshot(path="_verify/03_register_step1.png")

        phase="upload-word"
        with pg.expect_file_chooser() as fc:
            pg.locator('div.border-dashed >> visible=true').first.click()
        fc.value.set_files(DOCX)
        log("word uploaded, waiting for OCR…")
        pg.wait_for_selector('input[placeholder="项目名称"]', timeout=60000)
        pg.wait_for_timeout(1500)
        pg.screenshot(path="_verify/04_step2_autofilled.png", full_page=True)
        vals={f: pg.input_value(f'input[placeholder="{ph}"]') for f,ph in
              [("name","项目名称"),("code","合同/立项编码"),("amount","0.00")]}
        log("STEP2 OCR-extracted form values:", json.dumps(vals, ensure_ascii=False))

        phase="next-to-seal"; pg.click('text=下一步：上传盖章扫描版'); pg.wait_for_timeout(1000)
        pg.screenshot(path="_verify/05_step3_expense_form.png", full_page=True)

        phase="add-expense"
        pg.fill('input[placeholder="如：服务器采购 / 第三方外包服务"]', "服务器采购")
        pg.fill('input[placeholder="0.00"]', "8800")
        pg.fill('input[type="date"]', "2026-05-20")
        pg.click('text=添加支出流水'); pg.wait_for_timeout(600)
        expense_rows = pg.locator('table.table-cyber tbody tr').count()
        log("expense rows after add:", expense_rows)
        pg.screenshot(path="_verify/06_step3_expense_added.png", full_page=True)

        phase="upload-pdf"
        with pg.expect_file_chooser() as fc2:
            pg.locator('div.border-dashed >> visible=true').first.click()
        fc2.value.set_files(PDF)
        log("pdf uploaded, waiting…"); pg.wait_for_timeout(8000)
        pg.screenshot(path="_verify/07_step3_pdf_uploaded.png", full_page=True)

        phase="verify"
        pg.click('text=执行双版本 OCR 校验'); 
        log("verify triggered, waiting for /verify…")
        pg.wait_for_timeout(12000)
        pg.screenshot(path="_verify/08_step4_diff.png", full_page=True)
        body=pg.inner_text("body")
        mock=[s for s in ["HT-2026-088","580,000","420000.00","智能大屏数据可视化","网信政务"] if s in body]
        log("mock literals on diff screen:", mock or "NONE ✓")
    except Exception as e:
        log(f"!! FAILED at phase '{phase}': {type(e).__name__}: {str(e)[:200]}")
        try: pg.screenshot(path=f"_verify/ERR_{phase}.png", full_page=True)
        except: pass
    finally:
        log("\n=== /api network during register flow ===")
        for m,u,s in net: 
            if any(k in u for k in ('register','upload-word','upload-pdf','verify','expenses')): log(f"  {m} {u} -> {s}")
        b.close()
