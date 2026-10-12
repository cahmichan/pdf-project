import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'worker'))
import cv2
import numpy as np
import pytest
from PIL import Image
import pypdfium2 as pdfium
from engine import Engine, PDFError, fingerprint
from scanning import prepare, process, preview


def photo(path):
    page = np.full((700, 500, 3), 245, np.uint8)
    cv2.putText(page, 'SCAN TEST', (40, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (20, 20, 20), 3)
    for y in range(140, 600, 45):cv2.line(page, (40, y), (440, y), (60, 60, 60), 3)
    points = np.float32([[130, 100], [700, 145], [650, 850], [90, 790]])
    matrix = cv2.getPerspectiveTransform(np.float32([[0, 0], [499, 0], [499, 699], [0, 699]]), points)
    warped = cv2.warpPerspective(page, matrix, (800, 950), borderValue=(35, 50, 65))
    Image.fromarray(warped).save(path)
    return points / [799, 949]


@pytest.mark.parametrize('mode', ['color', 'grayscale', 'document', 'black_white'])
def test_photo_scan_perspective_enhancement_and_independent_reopen(tmp_path, mode):
    source = tmp_path / 'phone.png'; expected = photo(source); original = fingerprint(source)
    scanned = prepare({'path': str(source)})
    assert scanned['detected'] and np.abs(np.array(scanned['corners']) - expected).max() < .035
    args = {**scanned, 'filter': mode, 'rotation': 0}
    corrected = process(args)
    assert corrected.shape[0] > corrected.shape[1]
    assert corrected[200:500, 200:300].mean() > 190
    assert (corrected < 90).sum() > 5000
    if mode == 'black_white':assert set(np.unique(corrected)) == {0, 255}
    assert preview(args)['preview'].startswith('data:image/jpeg;base64,')
    rotated = process({**args, 'rotation': 90}); assert rotated.shape[:2] == corrected.shape[:2][::-1]
    engine = Engine(tmp_path / 'data')
    result = engine.dispatch({'command': 'scan_create', 'args': {'pages': [args, {**args, 'rotation': 90}]}})
    assert result['source'] is None and result['dirty'] and result['page_count'] == 2
    output = tmp_path / 'scan.pdf'
    engine.dispatch({'command': 'export', 'session': result['id'], 'args': {'path': str(output), 'mode': 'pdf'}})
    independent = pdfium.PdfDocument(output)
    assert len(independent) == 2
    for page in independent:
        pixels = np.array(page.render(scale=2).to_pil().convert('RGB'))
        assert (pixels < 90).sum() > 5000
        page.close()
    independent.close()
    assert engine.dispatch({'command': 'open', 'args': {'path': str(output)}})['page_count'] == 2
    assert fingerprint(source) == original


def test_scan_rejects_crossed_corners_changed_sources_and_partial_sessions(tmp_path):
    source = tmp_path / 'photo.png'; photo(source); args = prepare({'path': str(source)})
    engine = Engine(tmp_path / 'data')
    for points in ([[0, 0], [1, 1], [1, 0], [0, 1]], [[0, 0], [2, 0], [1, 1], [0, 1]], [[0, 0]]):
        with pytest.raises(PDFError):engine.dispatch({'command': 'scan_create', 'args': {'pages': [args, {**args, 'corners': points}]}})
        assert not list(engine.sessions_dir.glob('*/session.json'))
    Image.new('RGB', (800, 950), 'white').save(source)
    with pytest.raises(PDFError, match='source photo changed'):process(args)


def test_exif_orientation_and_no_boundary_fallback(tmp_path):
    path = tmp_path / 'rotated.jpg'; image = Image.new('RGB', (300, 500), 'white')
    exif = Image.Exif(); exif[274] = 6; image.save(path, exif=exif)
    scanned = prepare({'path': str(path)})
    assert (scanned['width'], scanned['height']) == (500, 300)
    assert not scanned['detected']
    assert scanned['corners'] == [[0, 0], [1, 0], [1, 1], [0, 1]]
