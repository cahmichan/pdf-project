"""Canonical document sessions. All edits create validated immutable revisions."""
from __future__ import annotations
import math
import re
import hashlib
import json
import os
import shutil
import sys
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Callable

import pymupdf as pdf


class PDFError(Exception):
    pass


def tessdata_dir() -> Path:
    return (Path(sys._MEIPASS) / 'tessdata' if getattr(sys, 'frozen', False)
            else Path(__file__).resolve().parents[1] / 'tools' / 'tessdata')


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def pages_arg(value: Any, count: int) -> list[int]:
    """UI page numbers are one-based; preserve ordering, reject malformed ranges."""
    if value in (None, '', 'all'):
        return list(range(count))
    if isinstance(value, list):
        numbers = [int(n) - 1 for n in value]
    else:
        numbers = []
        for part in str(value).split(','):
            ends = part.strip().split('-')
            if len(ends) == 1:
                numbers.append(int(ends[0]) - 1)
            elif len(ends) == 2:
                start, end = map(int, ends)
                if end < start:
                    raise PDFError('Page range must ascend.')
                numbers.extend(range(start - 1, end))
            else:
                raise PDFError('Use page ranges such as 1-3,5.')
    if not numbers or any(n < 0 or n >= count for n in numbers):
        raise PDFError(f'Page numbers must be between 1 and {count}.')
    return numbers


def valid_rect(value: Any, page: pdf.Page) -> pdf.Rect:
    rect = pdf.Rect(value)
    if rect.is_empty or rect.is_infinite or not page.rect.contains(rect):
        raise PDFError('Selection must be a non-empty rectangle inside the page.')
    return rect * page.derotation_matrix


def rgb(value: Any, default: tuple = (0.12, 0.2, 0.3)) -> tuple:
    if value is None:
        return default
    if isinstance(value, str):
        text = value.lstrip('#')
        if len(text) != 6:
            raise PDFError('Choose an RGB color.')
        return tuple(int(text[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return tuple(value)


def select_independent(doc: pdf.Document, selected: list[int]) -> None:
    """Keep original page references; create independent objects for duplicates."""
    unique=list(dict.fromkeys(selected))
    if len(unique)==len(selected):
        doc.select(selected)
        return
    # The immutable input file stays open and unchanged until commit saves rN.
    snapshot=pdf.open(doc.name) if doc.name else pdf.open(stream=doc.tobytes(),filetype='pdf')
    try:
        doc.select(unique)
        first={number:selected.index(number) for number in unique}
        names={w.field_name for page in doc for w in page.widgets() or []}
        seen=set();copied_links=[]
        for index,number in enumerate(selected):
            if number in seen:
                source_page=snapshot[number]
                links=source_page.get_links()
                doc.insert_pdf(snapshot,from_page=number,to_page=number,start_at=index,
                               widgets=True,annots=True,links=False)
                page=doc[index]
                for field in page.widgets() or []:
                    base=field.field_name;count=1
                    while f'{base}_copy{count}' in names:count+=1
                    field.field_name=f'{base}_copy{count}';names.add(field.field_name);field.update()
                copied_links.append((index,number,links))
            seen.add(number)
        for index,number,links in copied_links:
            page=doc[index];source_page=snapshot[number]
            for link in links:
                value={key:item for key,item in link.items() if key not in ('xref','id')}
                raw_rect=snapshot.xref_get_key(link['xref'],'Rect')[1]
                value['from']=pdf.Rect([float(n) for n in raw_rect.strip('[]').split()])*source_page.transformation_matrix
                if link['kind']==pdf.LINK_GOTO:
                    target=link.get('page',-1)
                    if target not in first:continue
                    value['page']=first[target]
                    if link.get('to') is not None:value['to']=pdf.Point(link['to'])*snapshot[target].derotation_matrix
                if link['kind'] in (pdf.LINK_GOTO,pdf.LINK_URI,pdf.LINK_GOTOR,pdf.LINK_LAUNCH,pdf.LINK_NAMED):
                    previous={item[0] for item in page.annot_xrefs()}
                    page.insert_link(value)
                    if link['kind']==pdf.LINK_GOTO:
                        # Preserve the original PDF destination coordinates exactly.
                        # Rotated CropBoxes make the high-level round trip lossy.
                        for key in ('A/D','Dest'):
                            kind,destination=snapshot.xref_get_key(link['xref'],key)
                            if kind=='array' and re.match(r'\[\s*\d+\s+\d+\s+R',destination):
                                destination=re.sub(r'(?<=\[)\s*\d+\s+\d+\s+R',f'{doc.page_xref(first[link["page"]])} 0 R',destination,count=1)
                                added=next(item[0] for item in page.annot_xrefs() if item[0] not in previous)
                                doc.xref_set_key(added,'A/D',destination)
                                break
    finally:
        snapshot.close()


def place_text(page: pdf.Page, rect: pdf.Rect, text: str, size: float, color: tuple = (0,0,0), rotation: int = 0) -> float:
    if not 1 <= size <= 300:
        raise PDFError('Choose a font size between 1 and 300 points.')
    if any(ord(character) > 255 for character in text):
        raise PDFError('This initial text editor supports Latin text. Extended font shaping is still in development.')
    font = pdf.Font('helv')
    if not rotation and '\n' not in text and pdf.get_text_length(text,fontsize=size) <= rect.width:
        if (font.ascender-font.descender)*size > rect.height:
            return -1
        page.insert_text((rect.x0,rect.y0+font.ascender*size),text,fontsize=size,color=color)
        return 0
    return page.insert_textbox(rect,text,fontsize=size,color=color,rotate=rotation)


class Engine:
    def __init__(self, data_dir: str | Path, progress: Callable | None = None):
        self.root = Path(data_dir).resolve()
        self.sessions_dir = self.root / 'sessions'
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: dict[str, dict] = {}
        self.progress = progress or (lambda *_: None)

    def persist(self, session: dict):
        folder = self.sessions_dir / session['id']
        temporary = folder / 'session.pending.json'
        temporary.write_text(json.dumps(session, ensure_ascii=False), encoding='utf-8')
        os.replace(temporary, folder / 'session.json')

    def session(self, identifier: str) -> dict:
        if identifier not in self.sessions:
            # UUID validation prevents traversing the session root.
            try:
                uuid.UUID(identifier)
                self.sessions[identifier] = json.loads((self.sessions_dir / identifier / 'session.json').read_text(encoding='utf-8'))
            except (ValueError, OSError, json.JSONDecodeError):
                raise PDFError('Document session was not found.')
        return self.sessions[identifier]

    def current(self, session: dict) -> Path:
        return self.sessions_dir / session['id'] / session['history'][session['cursor']]

    def info(self, session: dict) -> dict:
        with pdf.open(self.current(session)) as doc:
            return {
                'id': session['id'], 'name': session['name'], 'source': session['source'],
                'path': str(self.current(session)), 'revision': session['revision'],
                'dirty': fingerprint(self.current(session)) != session.get('saved_hash'),
                'page_count': len(doc), 'can_undo': session['cursor'] > 0,
                'can_redo': session['cursor'] < len(session['history']) - 1,
                'metadata': doc.metadata, 'bookmarks': doc.get_toc(),
                'signature_fields': doc.get_sigflags() > 0,
                'pages': [{'width': p.rect.width, 'height': p.rect.height, 'rotation': p.rotation,
                           'cropbox': list(p.cropbox)} for p in doc],
            }

    def open_file(self, args: dict) -> dict:
        path = Path(args['path']).resolve()
        if not path.is_file():
            raise PDFError('The selected file does not exist.')
        with pdf.open(path) as doc:
            if not doc.is_pdf:
                raise PDFError('Choose a PDF file. Use image import for pictures.')
            encrypted = bool(doc.needs_pass)
            if encrypted and not doc.authenticate(args.get('password', '')):
                raise PDFError('PASSWORD_REQUIRED: Enter the PDF password.')
            if len(doc) == 0:
                raise PDFError('This PDF contains no pages.')
            identifier = str(uuid.uuid4())
            folder = self.sessions_dir / identifier
            folder.mkdir()
            destination = folder / 'r0.pdf'
            if encrypted:
                doc.save(destination, encryption=pdf.PDF_ENCRYPT_NONE)
            else:
                shutil.copyfile(path, destination)
        session = {'id': identifier, 'name': path.name, 'source': str(path),
                   'source_hash': fingerprint(path), 'saved_hash': fingerprint(destination),
                   'history': ['r0.pdf'], 'cursor': 0, 'revision': 0}
        self.sessions[identifier] = session
        self.persist(session)
        return self.info(session)

    def create(self, args: dict) -> dict:
        identifier = str(uuid.uuid4())
        folder = self.sessions_dir / identifier
        folder.mkdir()
        doc = pdf.open()
        images = args.get('images', [])
        if images:
            for image in images:
                with pdf.open(image) as original:
                    converted = pdf.open('pdf', original.convert_to_pdf())
                    doc.insert_pdf(converted)
                    converted.close()
        else:
            doc.new_page(width=595, height=842)
        doc.save(folder / 'r0.pdf')
        doc.close()
        session = {'id': identifier, 'name': 'Untitled.pdf', 'source': None, 'source_hash': None,
                   'saved_hash': None, 'history': ['r0.pdf'], 'cursor': 0, 'revision': 0}
        self.sessions[identifier] = session
        self.persist(session)
        return self.info(session)

    def check_revision(self, session: dict, request: dict):
        if request.get('revision') != session['revision']:
            raise PDFError('The document changed. Refresh it before editing.')

    def commit(self, session: dict, mutate: Callable[[pdf.Document], None]) -> dict:
        revision = session['revision'] + 1
        name = f'r{revision}-{uuid.uuid4().hex[:8]}.pdf'
        destination = self.sessions_dir / session['id'] / name
        try:
            with pdf.open(self.current(session)) as doc:
                mutate(doc)
                if len(doc) == 0:
                    raise PDFError('A PDF must retain at least one page.')
                doc.save(destination, garbage=3, deflate=True)
            with pdf.open(destination) as check:
                if len(check) == 0 or check.needs_pass:
                    raise PDFError('The new revision could not be validated.')
            session['history'] = session['history'][:session['cursor'] + 1] + [name]
            session['cursor'] += 1
            session['revision'] = revision
            self.persist(session)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        return self.info(session)

    def apply(self, session: dict, args: dict) -> dict:
        operation = args['operation']

        def mutate(doc: pdf.Document):
            if doc.get_sigflags() > 0 and not args.get('allow_signature_changes'):
                raise PDFError('This PDF has signature fields. Confirm editing a separate working copy; signatures may become invalid.')
            selected = pages_arg(args.get('pages'), len(doc))
            if operation == 'rotate':
                for n in selected:
                    doc[n].set_rotation((doc[n].rotation + int(args.get('degrees', 90))) % 360)
            elif operation == 'reorder':
                select_independent(doc,selected)
            elif operation == 'delete_pages':
                keep = [n for n in range(len(doc)) if n not in selected]
                if not keep:
                    raise PDFError('Keep at least one page.')
                doc.select(keep)
            elif operation == 'insert_blank':
                doc.new_page(pno=int(args.get('after', len(doc))), width=595, height=842)
            elif operation == 'merge':
                for filename in args['paths']:
                    with pdf.open(filename) as other:
                        if other.needs_pass:
                            raise PDFError('Unlock the added PDF before merging it.')
                        doc.insert_pdf(other, widgets=True, links=True, annots=True)
            elif operation == 'crop':
                for n in selected:
                    page = doc[n]
                    margin = float(args.get('margin', 20))
                    rect = pdf.Rect(page.cropbox)
                    rect.x0 += margin; rect.y0 += margin
                    rect.x1 -= margin; rect.y1 -= margin
                    if rect.is_empty:
                        raise PDFError('Crop margins are larger than the page.')
                    page.set_cropbox(rect)
            elif operation in ('page_numbers', 'watermark'):
                for offset, n in enumerate(selected):
                    page = doc[n]
                    text = str(int(args.get('start', 1)) + offset) if operation == 'page_numbers' else args.get('text', 'DRAFT')
                    size = float(args.get('size', 11 if operation == 'page_numbers' else 48))
                    if operation == 'page_numbers':
                        rect = pdf.Rect(24, page.rect.height - 35, page.rect.width - 24, page.rect.height - 12)
                    else:
                        y = page.rect.height / 2 - size
                        rect = pdf.Rect(24, y, page.rect.width - 24, y + size * 2)
                    if page.insert_textbox(rect*page.derotation_matrix, text, fontsize=size, align=1, rotate=page.rotation, color=rgb(args.get('color')), fill_opacity=float(args.get('opacity', .3 if operation == 'watermark' else 1))) < 0:
                        raise PDFError('Text does not fit. Reduce the font size.')
            elif operation == 'fill_forms':
                values = args['values']
                for page in doc:
                    for field in page.widgets() or []:
                        if str(field.xref) in values:
                            if field.field_type == pdf.PDF_WIDGET_TYPE_SIGNATURE:
                                raise PDFError('Use certificate signing for signature fields.')
                            field.field_value = values[str(field.xref)]
                            field.update()
            elif operation == 'flatten_forms':
                doc.bake(annots=False, widgets=True)
            elif operation == 'metadata':
                metadata = doc.metadata
                for key in ('title','author','subject','keywords'):
                    if key in args:
                        metadata[key] = args[key]
                doc.set_metadata(metadata)
            elif operation == 'ocr':
                data = tessdata_dir()
                language = str(args.get('language', 'eng'))
                if language not in ('eng',):
                    raise PDFError('This build includes English OCR only.')
                if not (data / f'{language}.traineddata').is_file():
                    raise PDFError('OCR language data is missing. Run the asset preparation script.')
                dpi = int(args.get('dpi', 200))
                if not 100 <= dpi <= 400:
                    raise PDFError('OCR resolution must be between 100 and 400 DPI.')
                for offset, n in enumerate(selected):
                    self.progress(offset / len(selected), f'OCR page {n + 1} ({offset + 1}/{len(selected)})')
                    page = doc[n]
                    # Keep digital text pages intact and prevent duplicate OCR text.
                    if page.get_text().strip():
                        continue
                    rotation = page.rotation
                    page.set_rotation(0)
                    try:
                        raster = page.get_pixmap(dpi=dpi, colorspace=pdf.csRGB, alpha=False)
                        with pdf.open('pdf', raster.pdfocr_tobytes(language=language, tessdata=str(data))) as recognized:
                            if not recognized[0].get_text().strip():
                                continue
                            # Import only invisible recognized text, preserving original images/vectors.
                            for item in recognized[0].get_images():
                                recognized[0].delete_image(item[0])
                            page.show_pdf_page(page.rect, recognized, 0)
                    finally:
                        page.set_rotation(rotation)
            else:
                n = int(args.get('page', 1)) - 1
                if n < 0 or n >= len(doc):
                    raise PDFError('Choose a page in this document.')
                page = doc[n]
                # Map visual UI rectangles through derotation without altering CropBox/Rotate.
                rect = page.rect if operation in ('replace_image','delete_image','edit_annotation','delete_annotation','ink') else valid_rect(args.get('rect', [40, 40, 240, 100]), page)
                if operation in ('add_text', 'replace_text'):
                    size = float(args.get('size', 12))
                    text = str(args.get('text', ''))
                    # Fit on a scratch page before deleting original content.
                    bounds=page.rect*page.derotation_matrix
                    scratch = pdf.open(); trial = scratch.new_page(width=bounds.width, height=bounds.height)
                    fits = place_text(trial, rect, text, size, rotation=page.rotation)
                    scratch.close()
                    if fits < 0:
                        raise PDFError('Replacement text does not fit in this box. Increase the box or reduce the font size.')
                    if operation == 'replace_text':
                        if any(rect.intersects(pdf.Rect(image['bbox'])) for image in page.get_image_info()):
                            raise PDFError('This selection overlaps an image or scan. Use OCR and a supported scan-edit workflow.')
                        page.add_redact_annot(rect, fill=False)
                        page.apply_redactions(images=0, graphics=0, text=0)
                    if place_text(page, rect, text, size, rgb(args.get('color')), rotation=page.rotation) < 0:
                        raise PDFError('The text could not be placed.')
                elif operation == 'add_image':
                    page.insert_image(rect, filename=args['path'], keep_proportion=True,rotate=page.rotation)
                elif operation in ('highlight','underline','strikeout'):
                    quads=[]
                    for block in page.get_text('dict')['blocks']:
                        for line in block.get('lines',[]):
                            for span in line['spans']:
                                if rect.contains(pdf.Rect(span['bbox'])):
                                    quads.append(pdf.recover_quad(line['dir'],span))
                    # Support smaller word selections on ordinary horizontal lines.
                    if not quads:
                        quads = [pdf.Rect(word[:4]).quad for word in page.get_text('words') if rect.contains(pdf.Rect(word[:4]))]
                    if not quads:
                        raise PDFError('Select searchable text for a text markup annotation.')
                    annotation = {'highlight':page.add_highlight_annot,'underline':page.add_underline_annot,'strikeout':page.add_strikeout_annot}[operation](quads)
                    annotation.set_colors(stroke=rgb(args.get('color'), (1, .83, .2)))
                    annotation.update()
                elif operation == 'rectangle':
                    annotation = page.add_rect_annot(rect)
                    annotation.set_colors(stroke=rgb(args.get('color')))
                    annotation.update()
                elif operation == 'ink':
                    strokes = args.get('strokes', [])
                    if not isinstance(strokes, list) or not 1 <= len(strokes) <= 100:
                        raise PDFError('Draw between 1 and 100 strokes before applying ink.')
                    if sum(len(stroke) for stroke in strokes if isinstance(stroke, list)) > 20000:
                        raise PDFError('This ink selection has too many points. Apply smaller groups of strokes.')
                    mapped = []
                    for stroke in strokes:
                        if not isinstance(stroke, list) or len(stroke) < 2:
                            raise PDFError('Each ink stroke needs at least two points.')
                        points = []
                        for value in stroke:
                            if not isinstance(value, list) or len(value) != 2:
                                raise PDFError('Ink points must contain two coordinates.')
                            point = pdf.Point(float(value[0]), float(value[1]))
                            if not all(math.isfinite(v) for v in point) or not page.rect.contains(point):
                                raise PDFError('Ink strokes must stay inside the page.')
                            points.append(tuple(point * page.derotation_matrix))
                        mapped.append(points)
                    width = float(args.get('width', 2))
                    if not math.isfinite(width) or not .5 <= width <= 20:
                        raise PDFError('Ink width must be between 0.5 and 20 points.')
                    annotation = page.add_ink_annot(mapped)
                    annotation.set_colors(stroke=rgb(args.get('color')))
                    annotation.set_border(width=width)
                    annotation.set_info(content=str(args.get('text', '')))
                    annotation.update()
                elif operation == 'stamp':
                    stamps = {'approved':pdf.STAMP_Approved, 'draft':pdf.STAMP_Draft,
                              'confidential':pdf.STAMP_Confidential, 'final':pdf.STAMP_Final,
                              'not_approved':pdf.STAMP_NotApproved}
                    kind = str(args.get('stamp', 'approved'))
                    if kind not in stamps:
                        raise PDFError('Choose a supported PDF stamp.')
                    annotation = page.add_stamp_annot(rect, stamp=stamps[kind])
                    annotation.set_colors(stroke=rgb(args.get('color')))
                    annotation.set_rotation(page.rotation)
                    annotation.update()
                elif operation == 'comment':
                    page.add_text_annot(rect.tl, args.get('text','Comment'))
                elif operation in ('delete_annotation','edit_annotation'):
                    annotation = page.load_annot(int(args['id']))
                    if annotation is None:
                        raise PDFError('This annotation no longer exists.')
                    if operation == 'delete_annotation':
                        page.delete_annot(annotation)
                    else:
                        annotation.set_info(content=str(args.get('text','')))
                        annotation.update()
                elif operation in ('replace_image','delete_image'):
                    xref = int(args['id'])
                    if xref not in [item[0] for item in page.get_images()]:
                        raise PDFError('Select an image on this page.')
                    if operation == 'replace_image':
                        page.replace_image(xref,filename=args['path'])
                    else:
                        page.delete_image(xref)
                elif operation == 'redact':
                    page.add_redact_annot(rect, fill=(0,0,0))
                    page.apply_redactions(images=2, graphics=2, text=0)
                    # Remove auxiliary content that can leak original content.
                    doc.set_metadata({})
                    doc.del_xml_metadata()
                    for name in doc.embfile_names():
                        doc.embfile_del(name)
                    for other in doc:
                        for annotation in list(other.annots() or []):
                            other.delete_annot(annotation)
                    doc.scrub(attached_files=True, clean_pages=True, embedded_files=True, hidden_text=True,
                              javascript=True, metadata=True, redactions=True, remove_links=True,
                              reset_fields=True, reset_responses=True, thumbnails=True, xml_metadata=True)
                elif operation == 'add_form':
                    widget = pdf.Widget(); widget.rect = rect
                    widget.field_name = args.get('name', f'field_{uuid.uuid4().hex[:8]}')
                    if any(w.field_name == widget.field_name for p in doc for w in p.widgets() or []):
                        raise PDFError('A form field already uses that name.')
                    kind = args.get('field_type','text')
                    types = {'text':pdf.PDF_WIDGET_TYPE_TEXT,'checkbox':pdf.PDF_WIDGET_TYPE_CHECKBOX,'combo':pdf.PDF_WIDGET_TYPE_COMBOBOX,'list':pdf.PDF_WIDGET_TYPE_LISTBOX}
                    if kind not in types:
                        raise PDFError('Unsupported form field type.')
                    widget.field_type = types[kind]
                    if kind in ('combo','list'):
                        widget.choice_values = [line.strip() for line in args.get('choices','').splitlines() if line.strip()]
                        if not widget.choice_values:
                            raise PDFError('Enter at least one choice, one per line.')
                        widget.field_value = widget.choice_values[0]
                    else:
                        widget.field_value = False if kind == 'checkbox' else args.get('text', '')
                    widget.text_fontsize = float(args.get('size', 12))
                    page.add_widget(widget)
                else:
                    raise PDFError(f'Unknown operation: {operation}')
        return self.commit(session, mutate)

    def inspect_page(self, session: dict, args: dict) -> dict:
        with pdf.open(self.current(session)) as doc:
            page = doc[int(args.get('page', 1)) - 1]
            blocks = []
            for block in page.get_text('dict')['blocks']:
                if block['type'] == 0:
                    for line in block['lines']:
                        blocks.append({'rect': list(pdf.Rect(line['bbox'])*page.rotation_matrix), 'text': ''.join(span['text'] for span in line['spans']),
                                       'size': line['spans'][0]['size'] if line['spans'] else 12})
            return {'text': page.get_text(), 'blocks': blocks,
                    'forms': [{'id': str(w.xref), 'name': w.field_name, 'type': w.field_type_string,
                               'value': w.field_value, 'rect': list(w.rect), 'choices':w.choice_values,
                               'states':w.button_states()} for w in page.widgets() or []],
                    'annotations': [{'id': a.xref, 'type': a.type[1], 'rect': list(a.rect), 'content': a.info.get('content','')}
                                    for a in page.annots() or []],
                    'images': [{'id':item['xref'],'rect':list(item['bbox']),'width':item['width'],'height':item['height']} for item in page.get_image_info(xrefs=True) if item['xref']],
                    'links': [{'rect':list(link['from']),'page':link.get('page',-1)+1,'uri':link.get('uri','')} for link in page.get_links() if link['kind'] in (pdf.LINK_GOTO,pdf.LINK_URI)]}

    def export(self, session: dict, args: dict) -> dict:
        destination = Path(args['path']).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = Path(session['source']).resolve() if session['source'] else None
        if source == destination:
            if not args.get('overwrite_original'):
                raise PDFError('Choose a new name to preserve the original document.')
            if fingerprint(source) != session['source_hash']:
                raise PDFError('The original file changed in another application. Save a separate copy.')
        if destination.exists() and not args.get('overwrite'):
            raise PDFError('This output already exists. Confirm replacement or choose a different name.')
        mode = args.get('mode', 'pdf')
        validation = None
        temporary = destination.parent / f'.folio-{uuid.uuid4().hex}{destination.suffix}'
        try:
            with pdf.open(self.current(session)) as doc:
                selected = pages_arg(args.get('pages'), len(doc))
                if doc.get_sigflags()>0 and mode in ('extract','compress','compress_screen','compress_print','protect','unlock','repair','pdfa_2b') and not args.get('allow_signature_changes'):
                    raise PDFError('This PDF has signature fields. Confirm exporting a rewritten copy; existing signatures may become invalid.')
                if mode in ('pdf', 'extract', 'compress', 'compress_screen', 'compress_print', 'protect', 'unlock', 'repair'):
                    if mode == 'extract':
                        select_independent(doc,selected)
                    if mode.startswith('compress_'):
                        target, quality = (100, 65) if mode == 'compress_screen' else (200, 85)
                        doc.rewrite_images(dpi_threshold=int(target*1.25), dpi_target=target, quality=quality, bitonal=False)
                    settings = {'garbage': 4, 'deflate': True, 'encryption': pdf.PDF_ENCRYPT_NONE}
                    if mode == 'protect':
                        password = args.get('password', '')
                        if len(password) < 1:
                            raise PDFError('Enter a password for encryption.')
                        settings.update(encryption=pdf.PDF_ENCRYPT_AES_256, user_pw=password, owner_pw=args.get('owner_password') or password,
                                        permissions=pdf.PDF_PERM_PRINT | pdf.PDF_PERM_COPY | pdf.PDF_PERM_ANNOTATE | pdf.PDF_PERM_FORM)
                    if mode == 'pdf':
                        # A plain copy preserves existing signatures and exact bytes.
                        shutil.copyfile(self.current(session),temporary)
                    else:
                        doc.save(temporary, **settings)
                    with pdf.open(temporary) as check:
                        if check.needs_pass:
                            if not check.authenticate(args.get('password','')):
                                raise PDFError('Encrypted output verification failed.')
                        if len(check) != len(doc):
                            raise PDFError('Export page-count verification failed.')
                elif mode == 'pdfa_2b':
                    from archival import convert
                    report=self.sessions_dir/session['id']/('archive-'+uuid.uuid4().hex)/'validation.xml'
                    validation=convert(self.current(session),temporary,self.root,report,self.progress)
                elif mode in ('txt','markdown'):
                    separator = '\n\n---\n\n' if mode == 'markdown' else '\n\f\n'
                    temporary.write_text(separator.join(doc[n].get_text(sort=True) for n in selected), encoding='utf-8')
                elif mode == 'docx':
                    from docx import Document
                    output = Document()
                    for i,n in enumerate(selected):
                        if i:
                            output.add_page_break()
                        for block in doc[n].get_text('blocks', sort=True):
                            if block[6] == 0:
                                output.add_paragraph(block[4])
                    output.save(temporary)
                elif mode in ('pptx','pptx_images'):
                    from pptx import Presentation
                    from pptx.util import Pt
                    import io
                    output = Presentation()
                    output.slide_width = Pt(doc[selected[0]].rect.width)
                    output.slide_height = Pt(doc[selected[0]].rect.height)
                    for n in selected:
                        page = doc[n]; slide = output.slides.add_slide(output.slide_layouts[6])
                        if mode == 'pptx_images':
                            image = page.get_pixmap(matrix=pdf.Matrix(1.5,1.5)).tobytes('png')
                            slide.shapes.add_picture(io.BytesIO(image), 0, 0, output.slide_width, output.slide_height)
                        else:
                            sx = output.slide_width / Pt(page.rect.width); sy = output.slide_height / Pt(page.rect.height)
                            for block in page.get_text('dict')['blocks']:
                                x0,y0,x1,y1 = block['bbox']
                                if block['type'] == 0:
                                    box = slide.shapes.add_textbox(int(Pt(x0)*sx), int(Pt(y0)*sy), int(Pt(x1-x0+6)*sx), int(Pt(y1-y0+6)*sy))
                                    box.text_frame.margin_left = box.text_frame.margin_right = 0
                                    box.text_frame.margin_top = box.text_frame.margin_bottom = 0
                                    for j,line in enumerate(block['lines']):
                                        paragraph = box.text_frame.paragraphs[0] if j == 0 else box.text_frame.add_paragraph()
                                        for span in line['spans']:
                                            run = paragraph.add_run(); run.text = span['text']; run.font.size = Pt(span['size'])
                                elif block['type'] == 1:
                                    slide.shapes.add_picture(io.BytesIO(block['image']), int(Pt(x0)*sx), int(Pt(y0)*sy), int(Pt(x1-x0)*sx), int(Pt(y1-y0)*sy))
                    output.save(temporary)
                elif mode == 'xlsx':
                    from openpyxl import Workbook
                    output = Workbook(); output.remove(output.active)
                    for n in selected:
                        tables = doc[n].find_tables()
                        for i, table in enumerate(tables.tables):
                            sheet = output.create_sheet(f'Page {n+1} Table {i+1}')
                            for row in table.extract():
                                # Untrusted PDF strings must never become spreadsheet formulas.
                                safe = ["'" + cell if isinstance(cell,str) and cell.startswith(('=','+','-','@')) else cell for cell in row]
                                sheet.append(safe)
                    if not output.sheetnames:
                        raise PDFError('No tables detected. Select a text PDF with clear table boundaries.')
                    output.save(temporary)
                else:
                    raise PDFError('Unsupported export format.')
            if source == destination:
                shutil.copy2(source, source.with_name(f'{source.stem}.backup-{uuid.uuid4().hex[:8]}.pdf'))
            os.replace(temporary, destination)
            if mode == 'pdf':
                session['saved_hash'] = fingerprint(self.current(session))
                self.persist(session)
            return {'path': str(destination), 'bytes': destination.stat().st_size, 'mode': mode, 'validation':validation}
        finally:
            temporary.unlink(missing_ok=True)

    def export_images(self, session: dict, args: dict) -> dict:
        folder = Path(args['folder']).resolve(); folder.mkdir(parents=True,exist_ok=True)
        written = []
        with pdf.open(self.current(session)) as doc:
            selected = pages_arg(args.get('pages'), len(doc))
            dpi = int(args.get('dpi',150))
            if dpi < 36 or dpi > 600:
                raise PDFError('Choose an image resolution between 36 and 600 DPI.')
            format = args.get('format','png')
            if format not in ('png','jpg','embedded'):
                raise PDFError('Choose PNG, JPG, or embedded image extraction.')
            seen = set()
            for index,n in enumerate(selected):
                self.progress(index / len(selected), f'Exporting page {n+1}')
                if format == 'embedded':
                    for image in doc[n].get_images():
                        if image[0] in seen:
                            continue
                        seen.add(image[0]); extracted=doc.extract_image(image[0])
                        destination=folder / f'image-{image[0]}-{uuid.uuid4().hex[:6]}.{extracted["ext"]}'
                        destination.write_bytes(extracted['image']);written.append(str(destination))
                else:
                    destination = folder / f'{Path(session["name"]).stem}-page-{n+1}-{uuid.uuid4().hex[:6]}.{format}'
                    raster=doc[n].get_pixmap(dpi=dpi, colorspace=pdf.csRGB,alpha=False)
                    if format == 'jpg':
                        raster.save(destination,jpg_quality=85)
                    else:
                        raster.save(destination)
                    written.append(str(destination))
        return {'paths': written}

    def dispatch(self, request: dict) -> Any:
        command = request['command']; args = request.get('args', {})
        if command == 'startup':
            return None
        if command.startswith('preset_') or command.startswith('batch_'):
            from workflows import list_presets,save_preset,delete_preset,run_batch,history
            if command=='preset_list':return list_presets(self.root)
            if command=='preset_save':return save_preset(self.root,args)
            if command=='preset_delete':delete_preset(self.root,args['id']);return None
            if command=='batch_run':return run_batch(self,args)
            if command=='batch_history':return history(self.root)
        if command == 'open':
            return self.open_file(args)
        if command == 'create':
            return self.create(args)
        if command == 'create_identity':
            from signatures import create_identity
            return create_identity(args)
        if command == 'export_certificate':
            from signatures import export_certificate
            return export_certificate(args)
        if command == 'import_office':
            from office import locate, convert
            runtime=locate(self.root)
            if runtime is None:
                raise PDFError('Free LibreOffice runtime is not configured. See docs/SETUP.md.')
            source=Path(args['path']).resolve()
            with tempfile.TemporaryDirectory(prefix='folio-office-',dir=self.root) as temporary:
                converted=convert(source,runtime,Path(temporary),self.progress)
                opened=self.open_file({'path':str(converted)})
                session=self.session(opened['id'])
                session.update(source=str(source),source_hash=fingerprint(source),name=source.stem+'.pdf',saved_hash=None)
                self.persist(session)
                return self.info(session)
        if command == 'recoverable':
            result = []
            for file in self.sessions_dir.glob('*/session.json'):
                try:
                    session = json.loads(file.read_text(encoding='utf-8'))
                    result.append({'id':session['id'],'name':session['name'],'source':session['source']})
                except (OSError, ValueError):
                    continue
            return result
        if command == 'capabilities':
            from office import locate
            office=locate(self.root)
            return {'engine':pdf.VersionBind,'app_data':str(self.root),'office_runtime':str(office) if office else None, 'ocr_languages':['eng'] if (tessdata_dir() / 'eng.traineddata').is_file() else [], 'tools':{name:shutil.which(name) for name in ['tesseract','ocrmypdf','qpdf','soffice','verapdf']}}
        session = self.session(request['session'])
        if command == 'info':
            return self.info(session)
        if command == 'inspect_page':
            return self.inspect_page(session,args)
        if command == 'inspect_pdfa':
            from archival import locate, validate
            runtime=locate(self.root)
            if runtime is None:raise PDFError('Free archival tools are not configured. See docs/SETUP.md.')
            report=self.sessions_dir/session['id']/('archive-'+uuid.uuid4().hex)/'validation.xml'
            return validate(self.current(session),runtime,report,self.progress)
        if command == 'save_validation_report':
            report=Path(args['report']).resolve()
            folder=(self.sessions_dir/session['id']).resolve()
            if not report.is_relative_to(folder) or report.name!='validation.xml' or not report.parent.name.startswith('archive-'):
                raise PDFError('Choose a validation report belonging to this session.')
            destination=Path(args['path']).resolve()
            if destination.suffix.lower()!='.xml':raise PDFError('Save the conformance report as an XML file.')
            if destination.exists() and not args.get('overwrite'):raise PDFError('The report output already exists.')
            destination.parent.mkdir(parents=True,exist_ok=True)
            pending=destination.parent/('.folio-report-'+uuid.uuid4().hex+'.xml')
            try:
                shutil.copyfile(report,pending);os.replace(pending,destination)
            finally:pending.unlink(missing_ok=True)
            return {'path':str(destination)}
        if command == 'inspect_signatures':
            from signatures import inspect_signatures
            return inspect_signatures(self.current(session), args.get('trust_path'))
        if command == 'sign_copy':
            if request.get('revision') != session['revision']:
                raise PDFError('The working document changed. Review it before signing.')
            from signatures import sign_copy
            return sign_copy(self.current(session), session['source'], args)
        if command == 'thumbnail':
            number = int(args.get('page',1)) - 1
            destination = self.sessions_dir / session['id'] / f'thumb-{session["revision"]}-{number}.png'
            if not destination.exists():
                with pdf.open(self.current(session)) as doc:
                    page = doc[number]
                    page.get_pixmap(matrix=pdf.Matrix(80/page.rect.width,80/page.rect.width)).save(destination)
            return {'path':str(destination)}
        if command == 'search':
            query = args.get('text','')
            if not query:
                return []
            with pdf.open(self.current(session)) as doc:
                return [{'page':n+1, 'rect':list(rect*page.rotation_matrix)} for n,page in enumerate(doc) for rect in page.search_for(query)]
        if command in ('apply','undo','redo'):
            self.check_revision(session,request)
        if command == 'apply':
            return self.apply(session,args)
        if command in ('undo','redo'):
            cursor = session['cursor'] + (-1 if command == 'undo' else 1)
            if cursor < 0 or cursor >= len(session['history']):
                raise PDFError('No further history is available.')
            session['cursor'] = cursor; session['revision'] += 1
            self.persist(session)
            return self.info(session)
        if command == 'export':
            return self.export(session,args)
        if command == 'split':
            self.check_revision(session,request)
            from splitting import split
            return split(self,session,args)
        if command == 'export_images':
            return self.export_images(session,args)
        if command == 'prepare_print':
            with pdf.open(self.current(session)) as doc:
                selected=pages_arg(args.get('pages'),len(doc))
                if len(selected)>100:
                    raise PDFError('Print up to 100 pages per job. Choose a smaller page range.')
                folder=self.sessions_dir / session['id'] / ('print-'+uuid.uuid4().hex)
                folder.mkdir();result=[]
                for offset,n in enumerate(selected):
                    self.progress(offset/len(selected),f'Preparing print page {n+1}')
                    page=doc[n];scale=min(150/72,3500/max(page.rect.width,page.rect.height))
                    output=folder / f'page-{offset+1}.png'
                    page.get_pixmap(matrix=pdf.Matrix(scale,scale),colorspace=pdf.csRGB,alpha=False).save(output)
                    result.append({'page':n+1,'path':str(output),'width':page.rect.width,'height':page.rect.height,'dpi':round(scale*72)})
                return result
        if command == 'compare':
            from comparison import compare
            folder=self.sessions_dir / session['id'] / ('compare-'+uuid.uuid4().hex)
            folder.mkdir()
            snapshot=folder/'other.pdf'
            shutil.copyfile(Path(args['path']),snapshot)
            return compare(self.current(session),snapshot,folder,self.progress)
        if command == 'save_report':
            report=Path(args['report']).resolve()
            if not report.is_relative_to(self.sessions_dir / session['id']) or report.name!='report.html':
                raise PDFError('Choose a comparison report from this working session.')
            destination=Path(args['path']).resolve()
            if destination.suffix.lower()!='.html':
                raise PDFError('Save comparison reports as HTML.')
            if destination.exists() and not args.get('overwrite'):
                raise PDFError('Choose a new name or confirm replacement.')
            temporary=destination.parent / ('.folio-'+uuid.uuid4().hex+'.html')
            try:
                shutil.copyfile(report,temporary);os.replace(temporary,destination)
            finally:
                temporary.unlink(missing_ok=True)
            return {'path':str(destination)}
        raise PDFError(f'Unknown command: {command}')
