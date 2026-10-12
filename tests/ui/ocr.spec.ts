import { test,expect } from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
const root=process.cwd(),python=path.join(root,'.venv','Scripts','python.exe');
test('mixed page OCR mode, repeat, save/reopen and hidden scan-edit explanation',async({page})=>{
  const source=path.join(root,'artifacts','fixtures','mixed-ocr.pdf'),output=path.join(root,'artifacts','fixtures','ui-mixed-ocr.pdf'),original=fs.readFileSync(source),errors:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));await page.goto('/');await page.getByRole('button',{name:'Open PDF',exact:true}).click();await page.getByLabel('Absolute local file path').fill(source);await page.getByRole('button',{name:'Continue',exact:true}).click();await expect(page.locator('.textLayer')).toContainText('13579',{timeout:15000});
  await page.getByRole('button',{name:'Convert',exact:true}).click();await page.getByLabel('Tool',{exact:true}).selectOption('ocr');
  await page.getByLabel('OCR mode').selectOption('skip_text');await page.getByRole('button',{name:'Apply to working copy'}).click();await expect(page.locator('.status-bar')).toContainText('1 skipped');await expect(page.locator('.textLayer')).not.toContainText('24680');
  await page.getByLabel('OCR mode').selectOption('missing');await page.getByLabel('OCR resolution').fill('200');await page.getByRole('button',{name:'Apply to working copy'}).click();await expect(page.locator('.textLayer')).toContainText('24680');await expect(page.locator('.status-bar')).toContainText('1 pages processed');
  await page.getByRole('button',{name:'Apply to working copy'}).click();await expect(page.locator('.status-bar')).toContainText('0 words added');await expect(page.locator('.textLayer')).toContainText('13579');
  await expect(page.locator('.page-loading')).toBeHidden();await page.waitForFunction(()=>{const paper=document.querySelector<HTMLElement>('.paper');return paper?.dataset.renderedRevision===paper?.dataset.revision;});
  await page.screenshot({path:'artifacts/ui/mixed-ocr.png',fullPage:true});
  await page.getByRole('button',{name:'Save a copy',exact:true}).click();await page.getByLabel('Absolute output path').fill(output);await page.getByRole('button',{name:'Continue',exact:true}).click();await expect(page.locator('.status-bar')).toContainText('Saved');
  execFileSync(python,['-c',"import pypdfium2 as p,sys; a=p.PdfDocument(sys.argv[1]); b=p.PdfDocument(sys.argv[2]); t=b[0].get_textpage().get_text_range(); assert '24680' in t and t.count('13579')==1; assert a[0].render(scale=1).to_pil().tobytes()==b[0].render(scale=1).to_pil().tobytes(); a.close(); b.close()",source,output],{cwd:root});
  await page.getByRole('button',{name:'Edit',exact:true}).click();await page.locator('.textLayer span').filter({hasText:'24680'}).click();await expect(page.locator('.error-banner')).toContainText('hidden OCR text');await expect(page.getByLabel('Edit text on page')).toHaveCount(0);
  expect(fs.readFileSync(source).equals(original)).toBeTruthy();expect(errors).toEqual([]);
});
