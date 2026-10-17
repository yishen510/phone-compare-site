#!/usr/bin/env python3
"""Chromium browser interaction tests for the standalone comparison site.
Loads the shipped HTML and its inline scripts in Chromium, then exercises UI paths.
This is not a test of production hosting/CDN/TLS or external retailer APIs.
"""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from playwright.sync_api import sync_playwright
import json, time, sys, re
ROOT=Path(__file__).resolve().parents[1]
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
server=ThreadingHTTPServer(('127.0.0.1',0),QuietHandler)
Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_address[1]}/index.html'
results=[]
def _raise(errors):
    raise AssertionError(errors)
def check(name, fn):
    try:
        detail=fn(); results.append({'name':name,'status':'PASS','detail':detail or ''})
    except Exception as e:
        results.append({'name':name,'status':'FAIL','detail':str(e)})
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox','--no-proxy-server','--proxy-bypass-list=*'])
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    try:
        # Some managed environments block navigation to localhost/file URLs. Load the exact
        # shipped HTML into Chromium's about:blank document so inline app JS still executes.
        # This is real browser interaction coverage, but not HTTP/deployment-host coverage.
        html=(ROOT/'index.html').read_text(encoding='utf-8')
        scripts=re.findall(r'<script[^>]*>(.*?)</script>', html, flags=re.S|re.I)
        clean_html=re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.S|re.I)
        page.set_content(clean_html, wait_until='domcontentloaded', timeout=15000)
        # Inject the exact shipped inline scripts in source order. Separating them avoids
        # this sandbox's document parser hanging on large inline script blocks.
        for script in scripts:
            page.add_script_tag(content=script)
        page.wait_for_selector('.phone-card')
        # Expand default year filter to include the 2025 targets used below.
        page.locator('#yearFrom').select_option('2021')
        page.locator('#yearTo').select_option('2026')
        navigation_mode='Chromium page.set_content from shipped index.html (localhost/file navigation blocked)'
    except Exception as browser_error:
        browser.close(); server.shutdown(); server.server_close()
        report={'testDate':'2026-10-18','target':'Chromium UI E2E using shipped HTML via set_content','testCount':1,'passed':0,'failed':1,'results':[{'name':'Browser harness bootstrap','status':'BLOCKED','detail':str(browser_error)}],'scope':'No interaction assertions ran; not a passing E2E result.'}
        out=ROOT/'reports/deployment_e2e_test_2026-10-18.json'; out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False,indent=2)); sys.exit(2)
    check('Local browser entrypoint and initial render',lambda:f'{navigation_mode}; cards={page.locator(".phone-card").count()}')
    def search_test():
        search=page.locator('#searchInput'); search.fill('iPhone 17 Pro Max'); page.wait_for_timeout(200)
        names=page.locator('.phone-card h3').all_text_contents()
        assert names and all('iPhone 17 Pro Max' in n for n in names), names[:8]
        assert page.locator('.phone-card').count()==1, f'expected 1 result, got {page.locator(".phone-card").count()}'
        search.fill('nonexistent-phone-query'); page.wait_for_timeout(100)
        assert page.locator('#emptyState').is_visible(), 'empty state not visible'
        search.fill(''); page.wait_for_timeout(100)
        return 'keyword match and empty state work'
    check('Search and empty-state behavior',search_test)
    def brand_filter_test():
        page.locator('#brandFilters input[value="Apple"]').check(); page.wait_for_timeout(100)
        brands=page.locator('.phone-card .card-brand').all_text_contents()
        assert brands and all(b=='Apple' for b in brands), set(brands)
        page.locator('#brandFilters input[value="Apple"]').uncheck(); page.wait_for_timeout(100)
        return f'brand filter narrowed to {len(brands)} Apple card(s)'
    check('Brand filtering',brand_filter_test)
    def year_filter_test():
        page.locator('#yearFrom').select_option('2026'); page.locator('#yearTo').select_option('2026'); page.wait_for_timeout(100)
        years=page.locator('.phone-card .card-year').all_text_contents()
        assert years and all(str(y).startswith('2026') for y in years), set(years)
        page.locator('#yearFrom').select_option('2021'); page.locator('#yearTo').select_option('2026'); page.wait_for_timeout(100)
        return f'2026 filter returned {len(years)} cards'
    check('Year filtering',year_filter_test)
    def compare_test():
        page.locator('#searchInput').fill('iPhone 17 Pro Max'); page.wait_for_timeout(100)
        page.locator('.phone-card button[data-compare="apple-17pm"]').click(); page.wait_for_timeout(100)
        page.locator('#searchInput').fill('Galaxy S25'); page.wait_for_timeout(100)
        target=page.locator('.phone-card').filter(has=page.locator('h3',has_text='Galaxy S25')).first
        btn=target.locator('button[data-compare]').first
        btn.click(); page.wait_for_timeout(100)
        assert page.locator('#dockCount').inner_text().strip()=='2', page.locator('#dockCount').inner_text()
        page.locator('#openCompare').click(); page.wait_for_timeout(100)
        assert page.locator('#compareModal').is_visible(), 'compare modal did not open'
        assert page.locator('#compareModal').inner_text().find('未开放排名/推荐')>=0, 'gate status not shown in comparison'
        page.locator('#compareModal [data-close]').click(); page.wait_for_timeout(50)
        page.locator('#clearCompare').click(); page.wait_for_timeout(100)
        assert page.locator('#compareDock').is_hidden(), 'compare dock not cleared'
        return 'add two phones, open comparison, gate label, clear all passed'
    check('Compare workflow and gate display',compare_test)
    def recommendation_test():
        page.locator('#heroRecommend').click(); page.wait_for_timeout(100)
        assert page.locator('#recommendPanel').is_visible(), 'recommend panel did not open'
        page.locator('#applyRecommend').click(); page.wait_for_timeout(150)
        assert page.locator('.phone-card').count()==0, f'non-approved phone leaked into recommendation candidates: {page.locator(".phone-card").count()}'
        assert page.locator('#emptyState').is_visible(), 'no-eligible-candidate state not shown'
        return 'recommendation candidate list is empty while all eligibility flags are false'
    check('Recommendation fail-closed behavior',recommendation_test)
    def gate_tamper_test():
        # Mutate a clone only in browser memory to prove that eligibility requires all gates + evidence.
        result=page.evaluate('''() => {
          const base=window.PHONE_DATA.find(p=>p.id==='apple-17pm');
          const clone=JSON.parse(JSON.stringify(base));
          clone.auditStatus='verified'; clone.eligibleForRanking=true; clone.eligibleForRecommendation=true;
          const before=window.PhoneEligibility.modelPassed(clone);
          clone.fieldAudit={};
          const noEvidence=window.PhoneEligibility.modelPassed(clone);
          return {before,noEvidence,required:window.PhoneEligibility.REQUIRED_FIELDS.length};
        }''')
        assert result['before'] is False, f'candidate unexpectedly passed all-field gate: {result}'
        assert result['noEvidence'] is False, result
        assert result['required']>=8, result
        return json.dumps(result,ensure_ascii=False)
    check('Independent eligibility evidence gate',gate_tamper_test)
    check('No unhandled browser JS exceptions',lambda: (_raise(errors) if errors else 'none'))
    browser.close()
server.shutdown(); server.server_close()
report={'testDate':'2026-10-18','target':'Chromium UI E2E using exact shipped index.html via page.set_content','testCount':len(results),'passed':sum(r['status']=='PASS' for r in results),'failed':sum(r['status']=='FAIL' for r in results),'results':results,'scope':'real Chromium interaction tests against exact shipped HTML loaded with page.set_content; local navigation is blocked by environment. Does not cover production hosting, TLS/CDN, live price API, mobile devices, or factual source verification'}
out=ROOT/'reports/deployment_e2e_test_2026-10-18.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if report['failed']: sys.exit(1)
