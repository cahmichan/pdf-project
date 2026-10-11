"""Prepare free project-local archival tools without registering applications."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT/'tools'
DOWNLOADS = TOOLS/'downloads'
ASSETS = [
    ('7z2604-x64.msi', 'https://github.com/ip7z/7zip/releases/download/26.04/7z2604-x64.msi', '0b01334a418654293513449f61d6bfc99e5196ca371e3c3dc961eda57cd535c6'),
    ('gs10080w64.exe', 'https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10080/gs10080w64.exe', '52a91b8bf09298788d7a57b9206127026c23eacd75405f0a131e26dc381dce50'),
    ('OpenJDK21-jre.zip', 'https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/OpenJDK21U-jre_x64_windows_hotspot_21.0.12.1_1.zip', 'd35f31e712f0fcf6ac5a093edc90204fbff22f720ba3950bd09d331d5e621636'),
]
VERA_KEY = '13DD102B4DD69354D12DE5A83184863278B17FE7'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def download(name,url,expected=None):
    path=DOWNLOADS/name
    if not path.exists():
        subprocess.run(['curl.exe','-L','--fail','--silent','--show-error','--output',str(path),url],check=True)
    actual=digest(path)
    if expected and actual!=expected:
        raise ValueError(f'Hash mismatch for {name}: {actual}')
    return {'name':name,'url':url,'sha256':actual}


def unzip(source,destination):
    destination.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(source) as archive:
        for item in archive.infolist():
            target=(destination/item.filename).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError('Archive path leaves its extraction folder.')
        archive.extractall(destination)


def main():
    DOWNLOADS.mkdir(parents=True,exist_ok=True)
    receipt=ROOT/'artifacts'/'archival';receipt.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        downloads=list(executor.map(lambda args:download(*args),ASSETS))
    lessmsi=TOOLS/'lessmsi'/'lessmsi.exe'
    if not lessmsi.is_file():
        downloads.append(download('lessmsi-v2.12.9.zip','https://github.com/activescott/lessmsi/releases/download/v2.12.9/lessmsi-v2.12.9.zip','5b4e187e74b184ad3a63ccf06c3d17dae2b8c4b6c298a996dbd51a9f6db29d21'))
        unzip(DOWNLOADS/'lessmsi-v2.12.9.zip',lessmsi.parent)
    seven=TOOLS/'7zip'
    if not list(seven.glob('**/7z.exe')):
        subprocess.run([str(lessmsi),'x',str(DOWNLOADS/ASSETS[0][0]),str(seven.resolve())+'\\'],check=True)
    seven_exe=next(seven.glob('**/7z.exe'))
    ghost=TOOLS/'Ghostscript'
    if not list(ghost.glob('**/gswin64c.exe')):
        subprocess.run([str(seven_exe),'x',str(DOWNLOADS/ASSETS[1][0]),'-o'+str(ghost),'-y'],check=True)
    ghost_exe=next(ghost.glob('**/gswin64c.exe'))
    java=TOOLS/'Java'
    if not list(java.glob('**/bin/java.exe')):
        unzip(DOWNLOADS/ASSETS[2][0],java)
    java_exe=next(java.glob('**/bin/java.exe'))
    # Verify the stable veraPDF package with the documented publisher key.
    for name,url in [('verapdf-installer.zip','https://software.verapdf.org/releases/verapdf-installer.zip'),
                     ('verapdf-installer.zip.asc','https://software.verapdf.org/releases/verapdf-installer.zip.asc'),
                     ('verapdf-key.asc','https://software.verapdf.org/keys/KEY')]:
        downloads.append(download(name,url,'b512bf24945503a33fc10738ecffc1f2dccaaf8593a448e94ee9ac86a9559a59' if name=='verapdf-installer.zip' else None))
    gpg=Path('C:/Program Files/Git/usr/bin/gpg.exe')
    if not gpg.is_file():
        raise ValueError('A free GPG verifier is required for the signed veraPDF download.')
    keyring=receipt/'gnupg';keyring.mkdir(exist_ok=True)
    base=[str(gpg),'--batch','--homedir',keyring.relative_to(ROOT).as_posix(),'--no-auto-key-retrieve']
    subprocess.run(base+['--import',(DOWNLOADS/'verapdf-key.asc').relative_to(ROOT).as_posix()],check=True,capture_output=True,cwd=ROOT)
    fingerprints=subprocess.check_output(base+['--with-colons','--fingerprint'],text=True,cwd=ROOT)
    if VERA_KEY not in fingerprints:
        raise ValueError('The veraPDF publisher key does not match the documented fingerprint.')
    verified=subprocess.run(base+['--status-fd','1','--verify',(DOWNLOADS/'verapdf-installer.zip.asc').relative_to(ROOT).as_posix(),(DOWNLOADS/'verapdf-installer.zip').relative_to(ROOT).as_posix()],capture_output=True,text=True,check=True,cwd=ROOT)
    if not any('[GNUPG:] VALIDSIG' in line and VERA_KEY in line for line in verified.stdout.splitlines()):
        raise ValueError('The veraPDF signature does not belong to the expected publisher.')
    installer=TOOLS/'veraPDF-installer'
    unzip(DOWNLOADS/'verapdf-installer.zip',installer)
    installer_jar=next(installer.glob('**/verapdf-izpack-installer-*.jar'))
    vera=TOOLS/'veraPDF'
    if not list(vera.glob('bin/cli-*.jar')):
        configuration=ET.Element('AutomatedInstallation',langpack='eng')
        ET.SubElement(configuration,'com.izforge.izpack.panels.htmlhello.HTMLHelloPanel',id='welcome')
        target=ET.SubElement(configuration,'com.izforge.izpack.panels.target.TargetPanel',id='install_dir')
        ET.SubElement(target,'installpath').text=str(vera)
        packs=ET.SubElement(configuration,'com.izforge.izpack.panels.packs.PacksPanel',id='sdk_pack_select')
        for index,name,selected in [(0,'veraPDF GUI','true'),(1,'veraPDF Mac and *nix Scripts','true'),(2,'veraPDF Validation model','false'),(3,'veraPDF Documentation','false'),(4,'veraPDF Sample Plugins','false')]:
            ET.SubElement(packs,'pack',index=str(index),name=name,selected=selected)
        ET.SubElement(configuration,'com.izforge.izpack.panels.install.InstallPanel',id='install')
        ET.SubElement(configuration,'com.izforge.izpack.panels.finish.FinishPanel',id='finish')
        configuration_path=receipt/'install.xml';ET.ElementTree(configuration).write(configuration_path,encoding='utf-8',xml_declaration=True)
        subprocess.run([str(java_exe),'-jar',str(installer_jar),str(configuration_path)],check=True,timeout=180)
    jars=list(vera.glob('bin/cli-*.jar'))
    if not jars:
        raise ValueError('The veraPDF application jar was not extracted.')
    result={'downloads':downloads,'publisher_fingerprint':VERA_KEY,
            'ghostscript_runtime':str(ghost_exe),'java_runtime':str(java_exe),
            'verapdf_jars':[str(path) for path in jars],
            'note':'Extracted local files only. No registry or system PATH changes.'}
    (receipt/'runtime.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    settings_dir=Path(os.environ['APPDATA'])/'personal.folio.pdf'
    settings_dir.mkdir(parents=True,exist_ok=True);settings_path=settings_dir/'settings.json'
    try:settings=json.loads(settings_path.read_text(encoding='utf-8'))
    except FileNotFoundError:settings={}
    settings.update(ghostscript_runtime=str(ghost_exe),java_runtime=str(java_exe),verapdf_jar=str(jars[0]))
    pending=settings_dir/'settings.archival-pending.json';pending.write_text(json.dumps(settings,indent=2),encoding='utf-8');os.replace(pending,settings_path)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
