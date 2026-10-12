import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worker'))
import cv2
import numpy as np
from PIL import Image
import pytest
import pypdfium2 as pdfium
from engine import Engine,PDFError,fingerprint
from scanning import prepare,process,straighten,suggest_angle


def tilted_photo(path,angle):
    image=np.full((600,800,3),255,np.uint8)
    for y in range(100,520,70):
        cv2.putText(image,'Local scan reference 57391',(80,y),cv2.FONT_HERSHEY_SIMPLEX,.9,(20,20,20),2)
    matrix=cv2.getRotationMatrix2D((400,300),angle,1)
    Image.fromarray(cv2.warpAffine(image,matrix,(800,600),borderValue=(255,255,255))).save(path)


@pytest.mark.parametrize('angle',[-9,-4,4,9])
def test_suggestion_corrects_tilt_and_saved_pdf_preserves_source(tmp_path,angle):
    path=tmp_path/'tilted.png';tilted_photo(path,angle);before=fingerprint(path)
    photo=prepare({'path':str(path)});photo.update(corners=[[0,0],[1,0],[1,1],[0,1]],filter='color')
    engine=Engine(tmp_path/'data')
    proposed=engine.dispatch({'command':'scan_straighten','args':photo})
    assert proposed['detected'] and abs(proposed['angle']+angle)<.6
    corrected=process({**photo,'straighten':proposed['angle']})
    residual=suggest_angle(corrected)
    assert abs(residual['angle'])<.5
    created=engine.dispatch({'command':'scan_create','args':{'pages':[{**photo,'straighten':proposed['angle']}]}})
    output=tmp_path/'saved.pdf';engine.dispatch({'command':'export','session':created['id'],'args':{'path':str(output)}})
    with pdfium.PdfDocument(output) as doc:
        rendered=np.array(doc[0].render(scale=150/72).to_pil().convert('RGB'))
        assert rendered.shape[0]>=corrected.shape[0]-1 and rendered.shape[1]>=corrected.shape[1]-1
        assert (rendered<80).sum()>5000
    assert fingerprint(path)==before


def test_blank_page_has_no_suggestion_and_rotation_retains_edge_content():
    assert suggest_angle(np.full((400,600,3),255,np.uint8))['detected'] is False
    image=np.full((200,300,3),255,np.uint8);image[1:8,1:8]=0;image[-8:-1,-8:-1]=0
    rotated=straighten(image,12)
    assert rotated.shape[0]>200 and rotated.shape[1]>300
    assert (rotated[:,:,0]<128).sum()>=80


def test_straightening_then_black_white_filter_stays_binary_and_quarter_turns(tmp_path):
    path=tmp_path/'tilted.png';tilted_photo(path,5);photo=prepare({'path':str(path)})
    photo.update(corners=[[0,0],[1,0],[1,1],[0,1]],filter='black_white',straighten=-5)
    corrected=process(photo)
    assert set(np.unique(corrected))=={0,255}
    assert np.array_equal(process({**photo,'rotation':90}),np.rot90(corrected,-1))


@pytest.mark.parametrize('angle',[16,-16,float('nan'),float('inf'),'invalid',None])
def test_invalid_angle_rejects_without_partial_session(tmp_path,angle):
    path=tmp_path/'photo.png';Image.new('RGB',(300,400),'white').save(path)
    photo=prepare({'path':str(path)});engine=Engine(tmp_path/'data')
    with pytest.raises(PDFError,match='straightening angle'):
        engine.dispatch({'command':'scan_create','args':{'pages':[{**photo,'straighten':angle}]}})
    assert not list(engine.sessions_dir.glob('*/session.json'))
