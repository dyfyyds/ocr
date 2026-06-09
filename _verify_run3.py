import json
from playwright.sync_api import sync_playwright
BASE="http://localhost:18088"; DOCX=r"D:\course\ocr\OCR-docker\uploads\contracts\21727e6c6b8b4a70b698c8e9d2740bc9.docx"; PDF=r"D:\course\ocr\OCR-docker\uploads\contracts\259ba47ba1614375b50ee4e47ad4c044.pdf"
net=[]; verify_body={"_":None}
def log(*a): print(*a, flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True); pg=b.new_page(viewport={"width":1440,"height":1000})
    def on_resp(r):
        if "/api/" in r.url:
            u=r.url.split('/api/')[-1]; net.append((r.request.method,u,r.status))
            if "verify" in u and r.status==200:
                try: verify_body["_"]=r.json()
                except: pass
    pg.on("response", on_resp); pg.set_default_timeout(45000)
    try:
        pg.goto(BASE, wait_until="networkidle")
        pg.fill('input[autocomplete="username"]',"business"); pg.fill('input[autocomplete="current-password"]',"123456")
        pg.click('form button[type="submit"]'); pg.wait_for_timeout(2000)
        pg.click('text=智能立项登记'); pg.wait_for_timeout(700)
        # Word upload
        with pg.expect_file_chooser() as fc: pg.locator('div.border-dashed >> visible=true').first.click()
        fc.value.set_files(DOCX)
        pg.wait_for_selector('input[placeholder="项目名称"]', timeout=60000); pg.wait_for_timeout(1200)
        pg.click('text=下一步：上传盖章扫描版'); pg.wait_for_timeout(1000)
        # PDF upload via explicit text target
        with pg.expect_file_chooser() as fc2:
            pg.get_by_text("点击或拖拽上传带印章").click()
        fc2.value.set_files(PDF)
        log("pdf set, waiting for upload-pdf + contractFile…")
        pg.wait_for_selector('button:has-text("删除")', timeout=60000)  # v-else block shows once contractFile set
        pg.wait_for_timeout(1500)
        pg.screenshot(path="_verify/09_pdf_ok.png", full_page=True)
        # trigger verify
        pg.click('text=执行双版本 OCR 校验')
        log("verify clicked, waiting for /verify response…")
        for _ in range(40):
            pg.wait_for_timeout(1000)
            if verify_body["_"] is not None: break
        pg.wait_for_timeout(1500)
        pg.screenshot(path="_verify/10_step4_real_diff.png", full_page=True)
        body=pg.inner_text("body")
        mock=[s for s in ["HT-2026-088","580,000","420000.00","智能大屏数据可视化","网信政务"] if s in body]
        log("VERIFY response (real backend diffs):", json.dumps(verify_body["_"], ensure_ascii=False)[:500] if verify_body["_"] else "NONE")
        log("mock literals on diff screen:", mock or "NONE ✓")
    except Exception as e:
        log("FAILED:", type(e).__name__, str(e)[:200]); pg.screenshot(path="_verify/ERR_run3.png", full_page=True)
    finally:
        log("\n=== register-flow /api calls ===")
        for m,u,s in net:
            if any(k in u for k in ('register','upload-word','upload-pdf','verify')): log(f"  {m} {u} -> {s}")
        b.close()
