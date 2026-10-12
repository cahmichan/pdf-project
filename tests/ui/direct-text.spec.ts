import { test,expect } from '@playwright/test';
import path from 'node:path';
import fs from 'node:fs';
import { execFileSync } from 'node:child_process';
const root=process.cwd(),python=path.join(root,'.venv','Scripts','python.exe'),fixture=path.join(root,'artifacts','fixtures','sample.pdf');

test('click existing text, select and type in place, preserve drafts and save without drawing boxes',async({page})=>{
  const original=fs.readFileSync(fixture),output=path.join(root,'artifacts','fixtures','ui-direct-edit.pdf'),errors:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));await page.goto('/');
  await page.getByRole('button',{name:'Open PDF',exact:true}).click();await page.getByLabel('Absolute local file path').fill(fixture);await page.getByRole('button',{name:'Continue',exact:true}).click();
  await expect(page.locator('.textLayer')).toContainText('Folio sample document - page 1',{timeout:15000});
  await page.getByRole('button',{name:'Edit',exact:true}).click();
  await page.locator('.textLayer span').filter({hasText:'Folio sample document - page 1'}).click();
  const editor=page.getByLabel('Edit text on page');await expect(editor).toHaveValue('Folio sample document - page 1');
  const originalRevision=await page.locator('.paper').getAttribute('data-revision');await editor.press('Control+Enter');await expect(editor).toHaveCount(0);expect(await page.locator('.paper').getAttribute('data-revision')).toBe(originalRevision);
  await page.locator('.textLayer span').filter({hasText:'Folio sample document - page 1'}).click();await expect(editor).toHaveValue('Folio sample document - page 1');
  await expect(page.locator('.selection-surface')).toHaveCount(0);await expect(page.locator('.selection-box')).toHaveCount(0);await expect(page.getByLabel('Text',{exact:true})).toHaveCount(0);
  await editor.press('Control+Home');await editor.press('Control+ArrowRight');await editor.press('Control+Shift+ArrowRight');await page.keyboard.insertText('personal ');
  await expect(editor).toHaveValue('Folio personal document - page 1');
  await editor.fill('A heading edited directly');
  await page.screenshot({path:'artifacts/ui/direct-text-editing.png',fullPage:true});
  await page.getByLabel('Current page').fill('2');await expect(page.locator('.textLayer')).toContainText('page 2');
  await expect(page.getByRole('button',{name:'Return to text draft on page 1'})).toBeVisible();await page.getByRole('button',{name:'Return to text draft on page 1'}).click();
  await expect(editor).toHaveValue('A heading edited directly');
  await page.getByRole('button',{name:'Save a copy',exact:true}).click();await page.getByLabel('Absolute output path').fill(output);await page.getByRole('button',{name:'Continue',exact:true}).click();
  await expect(page.locator('.status-bar')).toContainText('Saved');await expect(page.locator('.textLayer')).toContainText('A heading edited directly');await expect(page.locator('.textLayer')).not.toContainText('Folio sample document - page 1');
  execFileSync(python,['-c',"import pypdfium2 as p,sys; d=p.PdfDocument(sys.argv[1]); t=d[0].get_textpage().get_text_range(); assert 'A heading edited directly' in t and 'Folio sample document - page 1' not in t; assert 'SAMPLE-12345' in t; d.close()",output],{cwd:root});
  await page.getByRole('button',{name:'Undo',exact:true}).click();await expect(page.locator('.textLayer')).toContainText('Folio sample document - page 1');
  await page.locator('.textLayer span').filter({hasText:'Folio sample document - page 1'}).click();await editor.fill('Cancelled change');await editor.press('Escape');await expect(editor).toHaveCount(0);await expect(page.locator('.textLayer')).toContainText('Folio sample document - page 1');
  await page.getByRole('button',{name:'Add new text',exact:true}).click();const box=await page.locator('.paper').boundingBox();if(!box)throw new Error('Missing page');await page.mouse.click(box.x+45,box.y+320);
  await page.getByLabel('New text on page').fill('New click-to-type text');await page.getByLabel('Text font',{exact:true}).selectOption('tibo');await page.getByLabel('Text size',{exact:true}).fill('16');await page.getByLabel('New text on page').press('Control+Enter');
  await expect(page.locator('.textLayer')).toContainText('New click-to-type text');expect(fs.readFileSync(fixture).equals(original)).toBeTruthy();expect(errors).toEqual([]);
});

test('direct existing-text controls work on cropped pages at every page rotation',async({page})=>{
  const source=path.join(root,'artifacts','fixtures','direct-rotations.pdf');
  execFileSync(python,['-c',"import pymupdf as p,sys; d=p.open();\nfor r in (0,90,180,270):\n q=d.new_page(width=500,height=700); q.set_cropbox(p.Rect(20,30,480,670)); q.insert_text((40,80),'Heading '+str(r),fontsize=20,fontname='hebo'); q.insert_text((40,230),'Neighbor '+str(r),fontsize=12); q.set_rotation(r)\nd.save(sys.argv[1])",source],{cwd:root});
  await page.goto('/');await page.getByRole('button',{name:'Open PDF',exact:true}).click();await page.getByLabel('Absolute local file path').fill(source);await page.getByRole('button',{name:'Continue',exact:true}).click();await page.getByRole('button',{name:'Edit',exact:true}).click();
  for(const [index,rotation] of [0,90,180,270].entries()){
    await page.getByLabel('Current page').fill(String(index+1));await expect(page.locator('.textLayer')).toContainText(`Heading ${rotation}`);await expect(page.locator('.page-loading')).toBeHidden();
    await page.locator('.textLayer span').filter({hasText:`Heading ${rotation}`}).click();await page.getByLabel('Edit text on page').fill(`Edited ${rotation}`);await page.getByRole('button',{name:'Apply text',exact:true}).click();await expect(page.locator('.textLayer')).toContainText(`Edited ${rotation}`);await expect(page.locator('.textLayer')).toContainText(`Neighbor ${rotation}`);
    await page.screenshot({path:`artifacts/ui/direct-text-${rotation}.png`,fullPage:true});
  }
});
