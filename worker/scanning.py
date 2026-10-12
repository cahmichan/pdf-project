"""Local photo document scanning. Source pixels are never written back."""
import base64
import io
import math
import uuid
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps
import pymupdf as pdf


def load(path):
    from engine import PDFError
    with Image.open(path) as source:
        if min(source.size) < 32:
            raise PDFError('Scan photos must be at least 32 pixels on each side.')
        if source.width * source.height > 40_000_000:
            raise PDFError('Scan photos must contain at most 40 million pixels.')
        if getattr(source, 'n_frames', 1) != 1:
            raise PDFError('Choose individual photos rather than a multi-frame image.')
        oriented = ImageOps.exif_transpose(source).convert('RGBA')
        background = Image.new('RGBA', oriented.size, 'white')
        background.alpha_composite(oriented)
        return np.array(background.convert('RGB'))


def thumbnail(image):
    picture = Image.fromarray(image)
    picture.thumbnail((1200, 1200))
    buffer = io.BytesIO(); picture.save(buffer, format='JPEG', quality=88)
    return 'data:image/jpeg;base64,' + base64.b64encode(buffer.getvalue()).decode('ascii')


def straighten(image, angle):
    """Rotate into an expanded white canvas so edge content is retained."""
    from engine import PDFError
    try:angle=float(angle)
    except (ValueError,TypeError):raise PDFError('Choose a straightening angle between -15 and 15 degrees.')
    if not math.isfinite(angle) or abs(angle)>15:
        raise PDFError('Choose a straightening angle between -15 and 15 degrees.')
    if angle==0:return image
    height,width=image.shape[:2]
    matrix=cv2.getRotationMatrix2D((width/2,height/2),angle,1)
    cosine,sine=abs(matrix[0,0]),abs(matrix[0,1])
    expanded_width=math.ceil(width*cosine+height*sine)
    expanded_height=math.ceil(height*cosine+width*sine)
    scale=min(1,4000/max(expanded_width,expanded_height),math.sqrt(16_000_000/(expanded_width*expanded_height)))
    matrix[:,:2]*=scale
    matrix[:,2]=[expanded_width*scale/2,expanded_height*scale/2]-matrix[:,:2]@np.array([width/2,height/2])
    return cv2.warpAffine(image,matrix,(math.ceil(expanded_width*scale),math.ceil(expanded_height*scale)),flags=cv2.INTER_CUBIC,borderValue=255 if image.ndim==2 else (255,255,255))


def suggest_angle(image):
    """Propose baseline alignment; low-confidence pages keep zero rotation."""
    height,width=image.shape[:2];scale=min(1,800/max(height,width))
    small=cv2.resize(image,(max(32,round(width*scale)),max(32,round(height*scale))))
    gray=cv2.cvtColor(small,cv2.COLOR_RGB2GRAY) if small.ndim==3 else small
    threshold=min(200,cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[0])
    ink=(gray<=threshold).astype(np.uint8)
    # Page borders are not evidence of text orientation.
    margin=max(1,round(min(ink.shape)*.04));ink[:margin]=0;ink[-margin:]=0;ink[:,:margin]=0;ink[:,-margin:]=0
    if ink.sum()<100:return {'angle':0,'confidence':0,'detected':False}
    center=(ink.shape[1]/2,ink.shape[0]/2)
    def score(angle):
        aligned=cv2.warpAffine(ink,cv2.getRotationMatrix2D(center,angle,1),(ink.shape[1],ink.shape[0]),flags=cv2.INTER_NEAREST)
        rows=aligned.sum(axis=1).astype(float)
        return float((rows@rows)/max(1,rows.sum()**2))
    angles=np.arange(-15,15.01,.5);scores=[score(angle) for angle in angles]
    best=float(angles[int(np.argmax(scores))])
    fine=np.arange(max(-15,best-.5),min(15,best+.5)+.01,.1)
    best=float(fine[int(np.argmax([score(angle) for angle in fine]))])
    confidence=score(best)/max(score(0),1e-12)
    detected=abs(best)>=.25 and abs(best)<14.9 and confidence>=1.08
    return {'angle':round(best,1) if detected else 0,'confidence':round(confidence,3),'detected':bool(detected)}


def detect(image):
    height, width = image.shape[:2]
    scale = min(1, 1200 / max(height, width))
    small = cv2.resize(image, (round(width * scale), round(height * scale)))
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    masks = [cv2.Canny(blurred, 40, 120), cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]]
    candidates = []
    for mask in masks:
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:30]:
            approx = cv2.approxPolyDP(contour, .025 * cv2.arcLength(contour, True), True)
            area = cv2.contourArea(approx) / (small.shape[0] * small.shape[1])
            if len(approx) == 4 and cv2.isContourConvex(approx) and .1 < area < .98:
                points = approx[:, 0, :].astype(float)
                center = points.mean(axis=0)
                points = points[np.argsort(np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0]))]
                points = np.roll(points, -np.argmin(points.sum(axis=1)), axis=0)
                candidates.append((area, (points / [small.shape[1] - 1, small.shape[0] - 1]).tolist()))
    if not candidates:
        return [[0, 0], [1, 0], [1, 1], [0, 1]], False
    return max(candidates, key=lambda candidate: candidate[0])[1], True


def prepare(args):
    from engine import fingerprint
    path = Path(args['path']).resolve()
    before = fingerprint(path)
    image = load(path)
    if fingerprint(path) != before:
        from engine import PDFError
        raise PDFError('The source photo changed while importing. Import it again.')
    corners, detected = detect(image)
    return {'path': str(path), 'hash': before, 'width': image.shape[1], 'height': image.shape[0],
            'corners': corners, 'detected': detected, 'preview': thumbnail(image)}


def capture(engine, args):
    from engine import PDFError
    value = args.get('image')
    if not isinstance(value, str) or len(value) > 24 * 1024 * 1024:
        raise PDFError('Camera frame is missing or too large.')
    header, separator, encoded = value.partition(',')
    formats = {'data:image/jpeg;base64': ('JPEG', '.jpg'), 'data:image/png;base64': ('PNG', '.png')}
    if not separator or header not in formats:raise PDFError('Capture a JPEG or PNG camera frame.')
    try:
        raw = base64.b64decode(encoded, validate=True)
        with Image.open(io.BytesIO(raw)) as frame:
            if frame.format != formats[header][0] or min(frame.size) < 32 or frame.width * frame.height > 40_000_000:
                raise ValueError('Invalid frame dimensions or format')
            frame.verify()
    except Exception as error:
        raise PDFError('The camera frame could not be decoded. Capture it again.') from error
    folder = engine.root / 'scan-captures'; folder.mkdir(exist_ok=True)
    destination = folder / ('Capture-' + uuid.uuid4().hex + formats[header][1])
    try:
        with destination.open('xb') as stream:stream.write(raw)
        return {**prepare({'path': str(destination)}), 'name': 'Camera photo'}
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def process(args):
    from engine import PDFError, fingerprint
    path = Path(args['path']).resolve()
    if args.get('hash') and fingerprint(path) != args['hash']:
        raise PDFError('The source photo changed. Import it again before scanning.')
    image = load(path); height, width = image.shape[:2]
    try:
        points = np.asarray(args['corners'], dtype=np.float32)
    except (ValueError, TypeError):
        raise PDFError('Choose four valid document corners.')
    if points.shape != (4, 2) or not np.isfinite(points).all() or (points < 0).any() or (points > 1).any():
        raise PDFError('Choose four document corners inside the photo.')
    points *= [width - 1, height - 1]
    if not cv2.isContourConvex(points) or cv2.contourArea(points, oriented=True) <= width * height * .02:
        raise PDFError('Corners must surround a document clockwise without crossing: top left, top right, bottom right, bottom left.')
    lengths = [float(np.linalg.norm(points[(i + 1) % 4] - points[i])) for i in range(4)]
    if min(lengths) < 10:
        raise PDFError('The selected document area is too small.')
    out_width, out_height = max(lengths[0], lengths[2]), max(lengths[1], lengths[3])
    scale = min(1, 4000 / max(out_width, out_height), math.sqrt(16_000_000 / (out_width * out_height)))
    out_width, out_height = max(2, round(out_width * scale)), max(2, round(out_height * scale))
    target = np.float32([[0, 0], [out_width - 1, 0], [out_width - 1, out_height - 1], [0, out_height - 1]])
    result = cv2.warpPerspective(image, cv2.getPerspectiveTransform(points, target), (out_width, out_height), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    result=straighten(result,args.get('straighten',0))
    out_height,out_width=result.shape[:2]
    mode = args.get('filter', 'color')
    if mode != 'color':
        gray = cv2.cvtColor(result, cv2.COLOR_RGB2GRAY)
        if mode == 'grayscale':
            result = gray
        elif mode in ('document', 'black_white'):
            background = cv2.GaussianBlur(gray, (0, 0), max(3, min(out_width, out_height) / 40))
            normalized = cv2.divide(gray, np.maximum(background, 1), scale=240)
            if mode == 'black_white':
                result = cv2.adaptiveThreshold(normalized, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 12)
            else:
                result = normalized
        else:
            raise PDFError('Choose color, grayscale, document or black and white enhancement.')
    rotation = args.get('rotation', 0)
    if rotation not in (0, 90, 180, 270):raise PDFError('Choose a quarter-turn rotation.')
    return np.rot90(result, -rotation // 90).copy()


def preview(args):
    image = process(args)
    return {'preview': thumbnail(image), 'width': image.shape[1], 'height': image.shape[0]}


def suggest(args):
    proposal=suggest_angle(process({**args,'straighten':0,'rotation':0}))
    return {**proposal,**preview({**args,'straighten':proposal['angle']})}


def create(engine, args):
    from engine import PDFError, fingerprint
    import tempfile
    pages = args.get('pages', [])
    if not isinstance(pages, list) or not 1 <= len(pages) <= 100:
        raise PDFError('Choose 1-100 scan photos.')
    with tempfile.TemporaryDirectory(prefix='folio-scan-', dir=engine.root) as temporary:
        destination = Path(temporary) / 'Scanned document.pdf'
        with pdf.open() as document:
            for index, item in enumerate(pages):
                engine.progress(index / len(pages), f'Processing scan {index + 1} of {len(pages)}')
                image = process(item)
                buffer = io.BytesIO(); Image.fromarray(image).save(buffer, format='PNG')
                height, width = image.shape[:2]
                # Preserve the corrected document proportions at a nominal 150 dpi.
                page = document.new_page(width=width * 72 / 150, height=height * 72 / 150)
                page.insert_image(page.rect, stream=buffer.getvalue())
                if item.get('hash') and fingerprint(Path(item['path'])) != item['hash']:
                    raise PDFError('A source photo changed during scanning. Import it again.')
            document.set_metadata({'title': 'Scanned document', 'producer': 'Folio local photo scanner'})
            document.save(destination, deflate=True)
        opened = engine.open_file({'path': str(destination)})
        session = engine.session(opened['id'])
        session.update(source=None, source_hash=None, saved_hash=None, name='Scanned document.pdf', scan_sources=[{'path': item['path'], 'hash': item.get('hash')} for item in pages])
        engine.persist(session)
        return engine.info(session)
