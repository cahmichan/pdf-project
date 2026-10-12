import { test,expect } from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
const root=process.cwd(),python=path.join(root,'.venv','Scripts','python.exe');
test('saved multilingual batch preset survives dialog reopening and recognizes Chinese',async({page})=>{
  const source=path.join(root,'artifacts','fixtures','scan-chinese.pdf'),original=fs.readFileSync(source),output=path.join(root,'artifacts','fixtures',`batch-languages-${Date.now()}`),name=`Chinese OCR ${Date.now()}`;
  await page.goto('/');await page.getByRole('button',{name:'Batch tools',exact:true}).click();await page.getByRole('button',{name:'Create preset',exact:true}).click();
  await page.getByLabel('Preset name').fill(name);await page.getByRole('button',{name:'Add step',exact:true}).click();await page.getByLabel('OCR language').selectOption('eng+chi_sim');await page.getByRole('button',{name:'Save preset',exact:true}).click();
  await page.getByRole('dialog',{name:'Batch PDF tools'}).getByRole('button',{name:'Close',exact:true}).click();await page.getByRole('button',{name:'Batch tools',exact:true}).click();await page.getByLabel('Batch preset').selectOption({label:name});
  await page.getByRole('button',{name:'Choose PDFs',exact:true}).click();await page.getByLabel('Absolute local file path').fill(source);await page.getByRole('button',{name:'Continue',exact:true}).click();
  await page.getByRole('button',{name:'Choose output folder',exact:true}).click();await page.getByLabel('Absolute output folder').fill(output);await page.getByRole('button',{name:'Continue',exact:true}).click();await page.getByRole('button',{name:'Run batch',exact:true}).click();
  await expect(page.getByRole('heading',{name:'1 of 1 files saved',exact:true})).toBeVisible();
  const saved=fs.readdirSync(output).filter(file=>file.endsWith('.pdf'));expect(saved).toHaveLength(1);
  execFileSync(python,['-c',"import pypdfium2 as p,sys; a=p.PdfDocument(sys.argv[1]); b=p.PdfDocument(sys.argv[2]); t=b[0].get_textpage().get_text_range().replace(' ',''); assert '文件' in t and '测试' in t and '86420' in t; assert a[0].render().to_pil().tobytes()==b[0].render().to_pil().tobytes(); a.close(); b.close()",source,path.join(output,saved[0])],{cwd:root});
  expect(fs.readFileSync(source).equals(original)).toBeTruthy();
  await page.getByRole('button',{name:'Delete preset',exact:true}).click();
});
test('local Malay and Chinese OCR language selection preserves saved page pixels',async({page})=>{
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));await page.goto('/');
  for(const [fixture,language,expected] of [['scan-malay.pdf','msa','97531'],['scan-chinese.pdf','eng+chi_sim','86420']]){
    const source=path.join(root,'artifacts','fixtures',fixture),output=path.join(root,'artifacts','fixtures','ui-'+fixture),original=fs.readFileSync(source);
    await page.getByRole('button',{name:'Open PDF',exact:true}).click();await page.getByLabel('Absolute local file path').fill(source);await page.getByRole('button',{name:'Continue',exact:true}).click();await expect(page.locator('.page-loading')).toBeHidden();
    await page.getByRole('button',{name:'Convert',exact:true}).click();await page.getByLabel('Tool',{exact:true}).selectOption('ocr');await page.getByLabel('OCR language').selectOption(language);
    await page.getByRole('button',{name:'Apply to working copy'}).click();await expect(page.locator('.textLayer')).toContainText(expected);await expect(page.locator('.page-loading')).toBeHidden();
    await page.getByRole('button',{name:'Save a copy',exact:true}).click();await page.getByLabel('Absolute output path').fill(output);await page.getByRole('button',{name:'Continue',exact:true}).click();await expect(page.locator('.status-bar')).toContainText('Saved');
    execFileSync(python,['-c',"import pypdfium2 as p,sys; a=p.PdfDocument(sys.argv[1]); b=p.PdfDocument(sys.argv[2]); t=b[0].get_textpage().get_text_range().replace(' ',''); assert sys.argv[3] in t; assert ('文件' in t and '测试' in t) if 'chinese' in sys.argv[1] else 'Semakan' in t; assert a[0].render().to_pil().tobytes()==b[0].render().to_pil().tobytes(); a.close(); b.close()",source,output,expected],{cwd:root});
    expect(fs.readFileSync(source).equals(original)).toBeTruthy();
  }
  await page.screenshot({path:'artifacts/ui/multilingual-ocr.png',fullPage:true});expect(errors).toEqual([]);
});
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
