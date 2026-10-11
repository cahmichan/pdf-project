"""Static PDF/A-2b export gated by independent veraPDF validation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import pymupdf as pdf


def locate(root: Path) -> dict | None:
    try:
        settings=json.loads((root/'settings.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):
        settings={}
    project=Path(__file__).resolve().parents[1]
    defaults={}
    if not getattr(sys,'frozen',False):
        defaults={'ghostscript_runtime':project/'tools/Ghostscript/bin/gswin64c.exe',
                  'java_runtime':next((project/'tools/Java').glob('**/bin/java.exe'),Path('missing-java')),
                  'verapdf_jar':next((project/'tools/veraPDF/bin').glob('cli-*.jar'),Path('missing-verapdf'))}
    paths={name:Path(settings.get(name,defaults.get(name,'missing-runtime'))).resolve()
           for name in ('ghostscript_runtime','java_runtime','verapdf_jar')}
    paths['icc']=paths['ghostscript_runtime'].parent.parent/'iccprofiles/srgb.icc'
    return paths if all(path.is_file() for path in paths.values()) else None


def run(arguments: list[str], scratch: Path, timeout=180) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(arguments,cwd=scratch,capture_output=True,text=True,encoding='utf-8',
                              errors='replace',timeout=timeout,
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
    except subprocess.TimeoutExpired:
        raise ValueError('The archival tool timed out; the original and working revision remain intact.') from None


def parse_report(data: str) -> dict:
    tree=ET.fromstring(data)
    reports=[e for e in tree.iter() if e.tag.rsplit('}',1)[-1]=='validationReport']
    if len(reports)!=1:
        raise ValueError('The validator did not return one PDF conformance report.')
    report=reports[0]
    details=next((e for e in report if e.tag.rsplit('}',1)[-1]=='details'),None)
    failures=[]
    for rule in report.iter():
        if rule.tag.rsplit('}',1)[-1]=='rule' and rule.get('status')=='failed':
            failures.append(' '.join((rule.get('specification',''),rule.get('clause',''),rule.get('testNumber',''),
                                     next((e.text or '' for e in rule if e.tag.rsplit('}',1)[-1]=='description'),''))).strip())
    return {'compliant':report.get('isCompliant')=='true' and report.get('jobEndStatus')=='normal' and details is not None and int(details.get('failedRules',0))==0 and int(details.get('passedRules',0))>0,
            'profile':report.get('profileName','Unknown'), 'statement':report.get('statement',''),
            'passed_rules':int(details.get('passedRules',0)) if details is not None else 0,
            'failed_rules':int(details.get('failedRules',0)) if details is not None else 0,
            'failures':failures[:20]}


def validate(source: Path, runtime: dict, report: Path, progress=lambda *args:None) -> dict:
    progress(.6,'Checking PDF/A-2b conformance with veraPDF')
    report.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='validator-',dir=report.parent) as temporary:
        scratch=Path(temporary)
        result=run([str(runtime['java_runtime']),'-Xmx512m',f'-Duser.home={scratch}',f'-Djava.io.tmpdir={scratch}',
                    '-jar',str(runtime['verapdf_jar']),'--format','xml','--flavour','2b',
                    '--maxfailures','20','--maxfailuresdisplayed','5',str(source)],scratch)
    if result.returncode not in (0,1) or not result.stdout.lstrip().startswith('<?xml'):
        raise ValueError('veraPDF could not inspect this PDF: '+result.stderr[-1200:])
    summary=parse_report(result.stdout)
    report.write_text(result.stdout,encoding='utf-8')
    summary['report']=str(report)
    return summary


def convert(source: Path, destination: Path, root: Path, report: Path, progress=lambda *args:None) -> dict:
    runtime=locate(root)
    if runtime is None:
        raise ValueError('Free archival tools are not configured. Run scripts/setup_archival.py; see docs/SETUP.md.')
    progress(.05,'Preparing a static archival copy')
    with tempfile.TemporaryDirectory(prefix='folio-archive-',dir=root) as temporary:
        scratch=Path(temporary);prepared=scratch/'prepared.pdf'
        with pdf.open(source) as document:
            page_count=len(document)
            dimensions=[(p.rect.width,p.rect.height) for p in document]
            document.bake(annots=True,widgets=True)
            for page in document:
                for link in page.get_links():page.delete_link(link)
            for name in document.embfile_names():document.embfile_del(name)
            document.scrub(javascript=True,attached_files=True,embedded_files=True,clean_pages=False,
                           hidden_text=False,metadata=False,redactions=False,remove_links=False,
                           reset_fields=False,reset_responses=False,thumbnails=False,xml_metadata=False)
            document.save(prepared,garbage=4,deflate=True)
        # A fixed prefix contains only the bundled sRGB profile path, never user PDF text.
        icc=runtime['icc'].as_posix().replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
        prefix=scratch/'prefix.ps'
        prefix.write_text('''%!
/ICCProfile (ICC_PATH) def
[ /_objdef {icc_PDFA} /type /stream /OBJ pdfmark
[ {icc_PDFA} << /N 3 >> /PUT pdfmark
[ {icc_PDFA} ICCProfile (r) file /PUT pdfmark
[ /_objdef {OutputIntent_PDFA} /type /dict /OBJ pdfmark
[ {OutputIntent_PDFA} << /Type /OutputIntent /S /GTS_PDFA1 /DestOutputProfile {icc_PDFA} /OutputConditionIdentifier (sRGB) >> /PUT pdfmark
[ {Catalog} << /OutputIntents [{OutputIntent_PDFA}] >> /PUT pdfmark
'''.replace('ICC_PATH',icc),encoding='utf-8')
        progress(.25,'Converting a static PDF/A-2b copy with Ghostscript')
        result=run([str(runtime['ghostscript_runtime']),'-dSAFER','-dBATCH','-dNOPAUSE','-dPDFA=2',
                    '-dPDFACompatibilityPolicy=2','-sColorConversionStrategy=RGB','-sBlendConversionStrategy=Managed',
                    '-dAutoRotatePages=/None','-dUseCropBox','-sDEVICE=pdfwrite',
                    '-sOutputFile='+str(destination),'--permit-file-read='+str(runtime['icc']),
                    str(prefix),str(prepared)],scratch)
        if result.returncode or 'aborting conversion' in result.stderr.lower():
            raise ValueError('Ghostscript could not produce an archival copy: '+result.stderr[-1500:])
        with pdf.open(destination) as output:
            if len(output)!=page_count or any(abs(p.rect.width-w)>1 or abs(p.rect.height-h)>1 for p,(w,h) in zip(output,dimensions)):
                raise ValueError('The archival output changed the visible page count or dimensions.')
        summary=validate(destination,runtime,report,progress)
        summary['conversion_notes']=result.stderr[-1500:]
        if not summary['compliant'] or summary['failed_rules']:
            raise ValueError('The archival copy failed PDF/A-2b conformance. '+summary['statement'])
        progress(1,'PDF/A-2b conformance passed')
        return summary
