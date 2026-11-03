"""Real-browser regression checks; run the local server before this script."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, os, subprocess
OUT=Path('/tmp/univs-validation'); OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1100})
 errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:3000/');page.wait_for_selector('.hero')
 assert page.title().startswith('수업을 다시 쓰다')
 page.screenshot(path=str(OUT/'desktop.png'),full_page=True)
 page.locator('[data-go="1"]').click()
 page.locator('[data-key="dept"]').fill('나의 원래 학과')
 page.locator('[data-key="teacher"]').fill('홍교수')
 page.locator('[data-key="course"]').fill('나의 원래 과목')
 page.locator('#sample-open').click();page.locator('#sample-dialog [data-sample="cooking"]').click()
 assert page.locator('[data-key="course"]').input_value()=='메뉴 개발 실습'
 page.locator('#sample-undo').click()
 assert page.locator('[data-key="course"]').input_value()=='나의 원래 과목'
 assert page.locator('[data-key="teacher"]').input_value()=='홍교수'
 # Each sample, all pages, keyboard-friendly expanded editor.
 for sid,course in [('cooking','메뉴 개발 실습'),('beauty','뷰티 디자인 실습'),('performance','공연 기획 실습')]:
  page.locator('#sample-open').click();page.locator(f'#sample-dialog [data-sample="{sid}"]').click()
  assert page.locator('[data-key="course"]').input_value()==course
  for n in range(2,10):
   page.locator(f'[data-nav="{n}"]').click()
   page.wait_for_selector('.card')
   assert page.locator('h1').count()==1
  page.locator('[data-nav="1"]').click()
 # Return to a sample with known rubric and ensure large input writes through.
 page.locator('#sample-open').click();page.locator('#sample-dialog [data-sample="cooking"]').click()
 page.locator('[data-key="teacher"]').fill('홍교수')
 page.locator('[data-nav="2"]').click()
 page.locator('[data-expand="mustDo"]').click()
 page.locator('#expanded-input').fill('직접 만든 시제품을 검증하고 이유를 설명하기')
 page.get_by_role('button',name='작성 완료',exact=True).click()
 assert page.locator('[data-key="mustDo"]').input_value()=='직접 만든 시제품을 검증하고 이유를 설명하기'
 page.reload();assert page.locator('[data-key="mustDo"]').input_value()=='직접 만든 시제품을 검증하고 이유를 설명하기'
 # Rubric totals, mismatch warnings, manual edits and explicit regeneration.
 page.locator('[data-nav="5"]').click();page.locator('[data-key="points.0"]').fill('35')
 assert '105' in page.locator('#score-sum').inner_text()
 assert 'invalid' in page.locator('#score-sum').get_attribute('class')
 page.locator('[data-key="points.0"]').fill('30')
 page.locator('[data-nav="6"]').click()
 assert '시세표' in page.locator('[data-key="sections.3"]').input_value()
 page.locator('[data-key="sections.0"]').fill('직접 편집한 과제 목표')
 page.locator('[data-key="issueDate"]').fill('2026. 11. 4.')
 page.locator('[data-nav="7"]').click();page.locator('[data-nav="6"]').click()
 assert page.locator('[data-key="sections.0"]').input_value()=='직접 편집한 과제 목표'
 page.screenshot(path=str(OUT/'document.png'),full_page=True)
 page.locator('[data-nav="7"]').click()
 page.locator('[data-key="syllabusTasks.0.2"]').select_option('2')
 page.locator('[data-nav="8"]').click()
 assert 'AI 단계가' in page.locator('.warning-list').inner_text()
 page.locator('[data-nav="7"]').click();page.locator('#sync-task').click()
 page.locator('[data-nav="8"]').click()
 for i in range(6):page.locator(f'[data-key="checks.{i}"]').check()
 # JSON backup/restore, including literal HTML protection.
 with page.expect_download() as download:
  page.locator('#finish-backup').click()
 backup=download.value
 backup.save_as(str(OUT/'backup.json'))
 backed=json.loads((OUT/'backup.json').read_text())
 assert backed['data']['course']=='메뉴 개발 실습'
 assert backed['previous']['course']=='나의 원래 과목'
 page.locator('[data-nav="0"]').click()
 page.once('dialog',lambda dlg:dlg.accept())
 page.locator('#restore').set_input_files(str(OUT/'backup.json'))
 page.wait_for_function("JSON.parse(localStorage.getItem('daekyeung-workbook-v1')).data.course==='메뉴 개발 실습'")
 page.locator('[data-nav="1"]').click();page.locator('[data-key="task"]').fill('<script>alert(1)</script> 한글 테스트')
 page.locator('[data-nav="6"]').click();assert page.locator('.document-mast p').inner_text()=='<script>alert(1)</script> 한글 테스트'
 page.locator('[data-nav="1"]').click();page.locator('[data-key="task"]').fill('신메뉴 개발 보고서')
 # Print all pages through Chromium; beforeprint builds actual live content.
 page.pdf(path=str(OUT/'workbook.pdf'),format='A4',print_background=True,prefer_css_page_size=True)
 extracted=subprocess.check_output(['pdftotext',str(OUT/'workbook.pdf'),'-'],text=True)
 assert '붙임 2' in extracted and '직접 편집한 과제 목표' in extracted
 # Separate export UI builds the selected document only.
 page.emulate_media(media='screen')
 page.locator('#export-open').click();page.locator('#print-range').select_option('assignment')
 page.evaluate('window.print=()=>{}')
 page.locator('#print-button').click()
 assert page.locator('#print-root .print-document').count()==3
 assert '강의계획서 AI 반영분' not in page.locator('#print-root').inner_text()
 # Reload to reset print interception; reset needs explicit confirmation.
 page.reload();page.locator('#reset-open').click();page.locator('#reset-confirm').click()
 assert page.locator('[data-key="course"]').input_value()==''
 assert page.locator('#sample-undo').count()==0
 page.reload();assert page.locator('[data-key="course"]').input_value()==''
 # Mobile: home and complex forms remain inside viewport.
 page.set_viewport_size({'width':390,'height':844});page.locator('[data-nav="0"]').click()
 page.screenshot(path=str(OUT/'mobile.png'),full_page=True)
 assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
 for n in [4,5,6,7,8,9]:
  page.locator(f'[data-nav="{n}"]').click()
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),f'overflow at step {n}'
 assert not errors,errors
 browser.close()
 print('PASS: 3 samples; sample undo; all 10 screens; expanded input; autosave/reload; rubric totals; manual edit preservation; AI-stage mismatch; backup; escaping; PDF; export ranges; reset; mobile overflow; no browser errors.')
