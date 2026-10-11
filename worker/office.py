"""Free local LibreOffice conversion using an isolated disposable profile."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import pymupdf as pdf

FORMATS={'.docx','.xlsx','.pptx','.odt','.ods','.odp','.rtf','.txt'}


def locate(data_dir: Path) -> Path | None:
    settings=data_dir/'settings.json'
    try:
        configured=json.loads(settings.read_text(encoding='utf-8')).get('office_runtime')
    except (OSError,ValueError):
        configured=None
    candidates=[Path(configured)] if configured else []
    if not getattr(sys,'frozen',False):
        candidates.append(Path(__file__).resolve().parents[1]/'tools'/'LibreOffice'/'program'/'soffice.com')
        candidates.append(Path(__file__).resolve().parents[1]/'tools'/'LibreOffice'/'SourceDir'/'LibreOffice'/'program'/'soffice.com')
    candidates += [data_dir/'tools'/'LibreOffice'/'program'/'soffice.com']
    if shutil.which('soffice'):
        candidates.append(Path(shutil.which('soffice')))
    for directory in ('ProgramFiles','ProgramFiles(x86)'):
        if os.environ.get(directory):
            candidates.append(Path(os.environ[directory])/'LibreOffice'/'program'/'soffice.com')
    return next((path for path in candidates if path.is_file()),None)


def reject_active_links(source: Path):
    if source.suffix.lower() not in ('.docx','.xlsx','.pptx','.odt','.ods','.odp'):return
    with zipfile.ZipFile(source) as archive:
        for name in archive.namelist():
            if name.endswith('vbaProject.bin'):
                raise ValueError('Macro-containing documents are not supported by this import path.')
            if name.endswith('.rels'):
                for element in ET.fromstring(archive.read(name)):
                    if element.get('TargetMode')=='External' and not element.get('Type','').endswith('/hyperlink'):
                        raise ValueError('This Office file contains external linked content. Embed it before importing.')
            elif name=='content.xml':
                for element in ET.fromstring(archive.read(name)).iter():
                    for attribute,value in element.attrib.items():
                        if attribute.endswith('}href') and value.startswith(('http:','https:','ftp:','file:')) and not element.tag.endswith('}a'):
                            raise ValueError('This document contains linked external content. Embed it before importing.')


def convert(source: Path, runtime: Path, scratch: Path, progress) -> Path:
    if source.suffix.lower() not in FORMATS:
        raise ValueError('Import DOCX, XLSX, PPTX, ODT, ODS, ODP, RTF, or TXT.')
    reject_active_links(source)
    scratch.mkdir(parents=True,exist_ok=True)
    profile=scratch/'profile';(profile/'user').mkdir(parents=True)
    (profile/'user'/'registrymodifications.xcu').write_text('''<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry"><item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop><prop oor:name="DisableMacrosExecution" oor:op="fuse"><value>true</value></prop></item></oor:items>''',encoding='utf-8')
    input_dir=scratch/'input';input_dir.mkdir(); copied=input_dir/('document'+source.suffix.lower());shutil.copyfile(source,copied)
    output=scratch/'output';output.mkdir()
    progress(0,'Converting with local LibreOffice')
    flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    process=subprocess.Popen([str(runtime),f'-env:UserInstallation={profile.as_uri()}','--headless','--nologo','--nodefault','--norestore','--convert-to','pdf','--outdir',str(output),str(copied)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=flags)
    try:
        stdout,stderr=process.communicate(timeout=240)
    except subprocess.TimeoutExpired:
        if os.name=='nt':
            subprocess.run([str(Path(os.environ['SystemRoot'])/'System32'/'taskkill.exe'),'/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=flags)
        else:process.kill()
        process.communicate()
        raise ValueError('Office conversion timed out. The source may be encrypted or unsupported.')
    destination=output/'document.pdf'
    if process.returncode or not destination.is_file():
        raise ValueError('LibreOffice could not convert this document: '+(stderr or stdout).decode('utf-8',errors='replace')[-1000:])
    with pdf.open(destination) as check:
        if check.needs_pass or not len(check):raise ValueError('Converted PDF verification failed.')
    return destination
