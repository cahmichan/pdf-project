import { test,expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const root=process.cwd(),python=path.join(root,'.venv','Scripts','python.exe');
test('photo straightening proposal, reset and manual adjustment persist to saved PDF',async({page})=>{
  const source=path.join(root,'artifacts','fixtures','tilted-scan.png'),output=path.join(root,'artifacts','fixtures','ui-straightened.pdf');
  execFileSync(python,['-c',"import runpy,sys; from pathlib import Path; runpy.run_path('tests/test_scan_straightening.py')['tilted_photo'](Path(sys.argv[1]),7)",source],{cwd:root});
  const original=fs.readFileSync(source),errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
  await page.goto('/');await page.getByRole('button',{name:'Scan photos',exact:true}).click();await page.getByRole('button',{name:'Add photos',exact:true}).click();await page.getByLabel('Absolute local file path').fill(source);await page.getByRole('button',{name:'Continue',exact:true}).click();
  await page.getByRole('button',{name:'Use whole photo',exact:true}).click();await page.getByLabel('Scan enhancement').selectOption('color');
  await page.getByRole('button',{name:'Suggest straightening',exact:true}).click();await expect(page.getByText('A straightening angle was suggested.',{exact:false})).toBeVisible();
  const angle=page.getByLabel('Scan straightening angle');expect(Math.abs(Number(await angle.inputValue())+7)).toBeLessThan(.6);await expect(page.getByAltText('Corrected scan preview')).toBeVisible();
  await page.getByRole('button',{name:'Reset straightening',exact:true}).click();await expect(angle).toHaveValue('0');await expect(page.getByAltText('Corrected scan preview')).toHaveCount(0);
  await angle.fill('-7');await page.getByRole('button',{name:'Preview scan',exact:true}).click();await expect(page.getByAltText('Corrected scan preview')).toBeVisible();await page.screenshot({path:'artifacts/ui/scan-straightening.png',fullPage:true});
  await page.getByRole('button',{name:'Create scanned PDF',exact:true}).click();await expect(page.locator('.page-loading')).toBeHidden();await page.getByRole('button',{name:'Save a copy',exact:true}).click();await page.getByLabel('Absolute output path').fill(output);await page.getByRole('button',{name:'Continue',exact:true}).click();await expect(page.locator('.status-bar')).toContainText('Saved');
  execFileSync(python,['-c',"import pypdfium2 as p,sys; d=p.PdfDocument(sys.argv[1]); q=d[0]; assert q.get_width()>800*72/150 and q.get_height()>600*72/150; assert q.render().to_pil().convert('L').getextrema()[0]<80; d.close()",output],{cwd:root});
  expect(fs.readFileSync(source).equals(original)).toBeTruthy();expect(errors).toEqual([]);
});
