"""Wrap name-keyed CFF outlines in OpenType with verified Unicode advances."""
import io
import math
import pymupdf as pdf
from fontTools import agl
from fontTools.cffLib import CFFFontSet
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import newTable


def convert(content):
    cff=CFFFontSet();cff.decompile(io.BytesIO(content),None)
    if len(cff.topDictIndex)!=1:raise ValueError('CFF collections need further mapping support.')
    top=cff.topDictIndex[0]
    if hasattr(top,'ROS'):raise ValueError('CID-keyed CFF requires explicit Unicode mapping.')
    matrix=top.FontMatrix
    if len(matrix)!=6 or matrix[0]<=0 or abs(matrix[0]-matrix[3])>1e-8 or any(abs(matrix[i])>1e-8 for i in (1,2,4,5)):
        raise ValueError('Transformed CFF fonts need further preview support.')
    units=round(1/matrix[0])
    if not 16<=units<=16384 or len(top.charset)>12000:raise ValueError('CFF preview exceeds supported font bounds.')
    source=pdf.Font(fontbuffer=content);metrics={};cmap={}
    for name in top.charset:
        charstring=top.CharStrings[name];pen=BoundsPen(None);charstring.draw(pen)
        metrics[name]=(round(charstring.width),round(pen.bounds[0]) if pen.bounds else 0)
        text=agl.toUnicode(name,isZapfDingbats='dingbat' in cff.fontNames[0].lower())
        glyph=source.has_glyph(ord(text)) if len(text)==1 else 0
        if glyph and glyph<len(top.charset) and top.charset[glyph]==name:
            if abs(source.glyph_advance(ord(text))*units-charstring.width)<1:
                cmap.setdefault(ord(text),name)
    if not cmap:raise ValueError('CFF has no verified Unicode glyph mapping.')
    ascent=math.ceil(source.ascender*units);descent=math.floor(source.descender*units)
    builder=FontBuilder(units,isTTF=False);builder.font.sfntVersion='OTTO'
    builder.setupGlyphOrder(top.charset);builder.setupCharacterMap(cmap)
    builder.setupHorizontalMetrics(metrics);builder.setupHorizontalHeader(ascent=ascent,descent=descent)
    builder.setupNameTable({'familyName':cff.fontNames[0],'styleName':'Regular','fullName':cff.fontNames[0],'psName':cff.fontNames[0]})
    builder.setupOS2(sTypoAscender=ascent,sTypoDescender=descent,usWinAscent=max(0,ascent),usWinDescent=max(0,-descent))
    builder.setupPost(italicAngle=getattr(top,'ItalicAngle',0))
    table=newTable('CFF ');table.cff=cff;builder.font['CFF ']=table;builder.setupMaxp()
    builder.font.recalcTimestamp=False
    builder.font['head'].created=builder.font['head'].modified=2082844800
    output=io.BytesIO();builder.save(output);converted=output.getvalue()
    # Verify the resulting font's Unicode cmap/advances through a separate engine.
    checked=pdf.Font(fontbuffer=converted)
    if any(not checked.has_glyph(code) or abs(checked.glyph_advance(code)-source.glyph_advance(code))>.001 for code in cmap):
        raise ValueError('Converted CFF glyph advances do not match the source.')
    return converted
