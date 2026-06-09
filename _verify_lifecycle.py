import time, json
from playwright.sync_api import sync_playwright
BASE="http://localhost:18088"
DOCX=r"D:\course\ocr\OCR-docker\uploads\contracts\21727e6c6b8b4a70b698c8e9d2740bc9.docx"
PDF=r"D:\course\ocr\OCR-docker\uploads\contracts\259ba47ba1614375b50ee4e47ad4c044.pdf"
REPORT=r"D:\course\ocr\OCR-docker\uploads\contracts\246d5b6791b54df6a2eab3a77b57fd06.docx"
def log(*a): print(*a, flush=True)
net=[]
def login(pg,u):
    try: pg.evaluate("()=>localStorage.clear()")
    except: pass
    pg.goto(BASE, wait_until="networkidle")
    pg.fill('input[autocomplete="username"]',u); pg.fill('input[autocomplete="current-password"]',"123456")
    pg.click('form button[type="submit"]'); pg.wait_for_timeout(2600)
def st(pg,pid):
    return pg.evaluate("""async(id)=>{const t=localStorage.getItem('pm_token');const r=await fetch('/api/projects/'+id,{headers:{Authorization:'Bearer '+t}});const d=await r.json();return {status:d.status,close_status:d.close_status,desc:d.description};}""", pid)
with sync_playwright() as p:
    b=p.chromium.launch(headless=True); pg=b.new_page(viewport={"width":1480,"height":1000})
    pg.on("response", lambda r: net.append((r.request.method, r.url.split('/api/')[-1], r.status)) if ("/api/" in r.url and r.request.method!="GET") else None)
    pg.set_default_timeout(45000); pid=None; uniq="W5验证说明-"+str(int(time.time()))
    try:
        # STAGE 1 business
        login(pg,"business"); pg.click('text=智能立项登记'); pg.wait_for_timeout(700)
        with pg.expect_file_chooser() as fc: pg.locator('div.border-dashed >> visible=true').first.click()
        fc.value.set_files(DOCX)
        pg.wait_for_selector('input[placeholder="项目名称"]',timeout=60000); pg.wait_for_timeout(1000)
        try: pg.fill('textarea[placeholder^="在此输入"]', uniq)
        except Exception as e: log("desc fill skip:",e)
        pid=pg.evaluate("""async()=>{const t=localStorage.getItem('pm_token');const r=await fetch('/api/projects?size=1',{headers:{Authorization:'Bearer '+t}});const d=await r.json();return d.items[0].id;}""")
        log("created project id:",pid)
        pg.click('text=下一步：上传盖章扫描版'); pg.wait_for_timeout(800)
        with pg.expect_file_chooser() as fc2: pg.get_by_text("点击或拖拽上传带印章").click()
        fc2.value.set_files(PDF)
        pg.wait_for_selector('button:has-text("删除")',timeout=60000); pg.wait_for_timeout(1200)
        pg.click('text=执行双版本 OCR 校验'); pg.wait_for_timeout(11000)
        pg.click('text=确认差异并提交立项审核'); pg.wait_for_timeout(2600)
        log("STAGE1 business submit ->", st(pg,pid))
        # STAGE 2 admin approve
        login(pg,"admin"); pg.click('text=立项终审中心'); pg.wait_for_timeout(1300)
        pg.locator('button:has-text("查看提取比对并评审")').first.click(); pg.wait_for_timeout(900)
        panel=pg.inner_text('.glass-panel-elevated'); pg.screenshot(path="_verify/20_admin_audit.png",full_page=True)
        pg.click('text=审核通过（项目生效）'); pg.wait_for_timeout(2200)
        log("STAGE2 admin approve ->", st(pg,pid), "| real desc shown to admin:", uniq in panel)
        # STAGE 3 finance invoice+payment
        login(pg,"finance"); pg.click('text=财务收支台账'); pg.wait_for_timeout(1500)
        pg.locator('button:has-text("资金记账")').first.click(); pg.wait_for_timeout(900)
        pg.locator('input[placeholder="0.00"]').nth(0).fill("100000")
        pg.locator('input[type="date"]').nth(0).fill("2026-06-10")
        pg.click('text=登记发票'); pg.wait_for_timeout(2200)
        pg.locator('input[placeholder="0.00"]').nth(1).fill("60000")
        pg.locator('input[type="date"]').nth(1).fill("2026-06-15")
        pg.click('text=记回款项'); pg.wait_for_timeout(2200)
        pg.screenshot(path="_verify/21_finance_ledger.png",full_page=True)
        fin=pg.evaluate("""async(id)=>{const t=localStorage.getItem('pm_token');const i=await (await fetch('/api/projects/'+id+'/invoices',{headers:{Authorization:'Bearer '+t}})).json();const p=await (await fetch('/api/projects/'+id+'/payments',{headers:{Authorization:'Bearer '+t}})).json();const inv=(i.items||[]).reduce((s,x)=>s+parseFloat(x.amount),0);const pay=(p.items||[]).reduce((s,x)=>s+parseFloat(x.amount),0);return {invoiced:inv,paid:pay,receivable:inv-pay};}""", pid)
        log("STAGE3 finance ->", fin)
        # STAGE 4 pm close
        login(pg,"pm"); pg.click('text=项目进度跟踪'); pg.wait_for_timeout(1300)
        pg.locator('button:has-text("上传验收报告申请结项")').first.click(); pg.wait_for_timeout(800)
        with pg.expect_file_chooser() as fc3: pg.get_by_text("点击选择验收报告").click()
        fc3.value.set_files(REPORT); pg.wait_for_timeout(1000)
        pg.click('text=确认并提起结项申请'); pg.wait_for_timeout(2200)
        log("STAGE4 pm close request ->", st(pg,pid))
        # STAGE 5 finance close audit
        login(pg,"finance"); pg.click('text=项目结项终审'); pg.wait_for_timeout(1300)
        pg.locator('button:has-text("批准结项")').first.click(); pg.wait_for_timeout(2200)
        log("STAGE5 finance approve close ->", st(pg,pid))
        # STAGE 6 read-only enforcement
        ro=pg.evaluate("""async(id)=>{const t=localStorage.getItem('pm_token');const fd=new FormData();fd.append('amount','1');fd.append('invoice_date','2026-06-20');const r=await fetch('/api/projects/'+id+'/invoices',{method:'POST',headers:{Authorization:'Bearer '+t},body:fd});const d=await r.json().catch(()=>({}));return {http:r.status,msg:d.message||d.detail};}""", pid)
        log("STAGE6 invoice on 已结项 (expect reject) ->", ro)
    except Exception as e:
        log("LIFECYCLE FAILED:", type(e).__name__, str(e)[:200]); pg.screenshot(path="_verify/ERR_lifecycle.png",full_page=True)
    finally:
        log("\n=== write/mutation API calls ===")
        for m,u,s in net:
            if any(k in u for k in ('register','submit','audit','invoices','payments','/close')): log(f"  {m} {u} -> {s}")
        b.close()
