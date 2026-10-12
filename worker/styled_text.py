"""Retain source text-run styles while changing and wrapping a paragraph."""
from difflib import SequenceMatcher
import math
import re
import pymupdf as pdf


def source_styles(page, identifier):
    block=page.get_text('dict')['blocks'][identifier]
    text=[];styles=[]
    for number,line in enumerate(block['lines']):
        if number:
            text.append('\n');styles.append(styles[-1])
        baseline=line['spans'][0]['origin'][1]
        for span in line['spans']:
            style={'font':span['font'],'size':span['size'],'color':'#'+format(span['color'],'06x'),'flags':span['flags'],'offset':span['origin'][1]-baseline}
            text.extend(span['text']);styles.extend([style]*len(span['text']))
    return ''.join(text),styles


def mapped_styles(before,styles,after):
    """Unchanged characters retain styles; new text inherits the replaced/adjacent run."""
    output=[]
    for action,a,b,c,d in SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if action=='equal':output.extend(styles[a:b])
        elif action in ('replace','insert'):
            inherited=styles[a] if b>a else styles[max(0,a-1)]
            output.extend([inherited]*(d-c))
    return output


class StyledText:
    def __init__(self,doc,page,original,text,args):
        from direct_text import font_choice
        from engine import PDFError,rgb
        before,source=source_styles(page,original['id'])
        if len(before)>5000 or len(text)>5000:raise PDFError('Styled paragraphs currently support up to 5,000 characters per edit.')
        if not source:raise PDFError('The source paragraph has no editable style runs.')
        mapped=mapped_styles(before,source,text)
        self.characters=[];self.fonts={};self.baseline=original['origin'][1]
        ratio=float(args.get('size',original['size']))/original['size']
        self.default_size=original['size']*ratio
        color=args.get('color',original['color'])
        mode=args.get('color_mode','auto')
        override=mode=='uniform' or (mode=='auto' and (color.lower()!=original['color'].lower() if isinstance(color,str) else True))
        keys=[(item['font'],item['size'],item['color'],item['flags'],item['offset']) for item in mapped]
        for key in dict.fromkeys(keys):
            name,size,tint,flags,offset=key
            run_text=''.join(char for char,style_key in zip(text,keys) if style_key==key)
            font,fontname,buffer=font_choice(doc,page,{'font':'original'},{'font':name,'mixed_styles':False},run_text)
            scaled=size*ratio
            if not math.isfinite(scaled) or not 1<=scaled<=300:raise PDFError('Relative font sizes would be outside 1-300 points. Choose a smaller paragraph size.')
            self.fonts[key]={'font':font,'name':fontname,'buffer':buffer,'size':scaled,'color':rgb(color if override else tint),'offset':offset*ratio}
        self.characters=list(zip(text,keys))
        self.top=self.baseline+min(item['offset']-item['font'].ascender*item['size'] for item in self.fonts.values())
        gaps=[block['spans'][0]['origin'][1] for block in page.get_text('dict')['blocks'][original['id']]['lines']]
        self.line_ratio=max(1.2,min((b-a)/original['size'] for a,b in zip(gaps,gaps[1:]) if b>a)) if any(b>a for a,b in zip(gaps,gaps[1:])) else 1.2

    def place(self,page,region):
        from engine import PDFError
        for item in self.fonts.values():
            if item['buffer']:page.insert_font(fontname=item['name'],fontbuffer=item['buffer'])
        lines=[];line=[];width=0
        string=''.join(char for char,_ in self.characters)
        for match in re.finditer(r'\n|[^\S\n]+|[^\s]+',string):
            token=self.characters[match.start():match.end()]
            if match.group()=='\n':lines.append(line);line=[];width=0;continue
            token_width=sum(self.fonts[key]['font'].text_length(char,fontsize=self.fonts[key]['size']) for char,key in token)
            if line and width+token_width>region.width and not match.group().isspace():lines.append(line);line=[];width=0
            for char,key in token:
                item=self.fonts[key];advance=item['font'].text_length(char,fontsize=item['size'])
                if advance>region.width:raise PDFError('A character does not fit in the available line width.')
                if width+advance>region.width:
                    lines.append(line);line=[];width=0
                    if char.isspace():continue
                line.append((char,key));width+=advance
        if line:lines.append(line)
        baseline=self.baseline;bottom=region.y0
        for line in lines:
            if not line:baseline+=self.default_size*self.line_ratio;continue
            x=region.x0;groups=[]
            for char,key in line:
                if groups and groups[-1][0]==key:groups[-1][1]+=char
                else:groups.append([key,char])
            for key,content in groups:
                item=self.fonts[key];y=baseline+item['offset']
                if y-item['font'].ascender*item['size']<region.y0-.1 or y-item['font'].descender*item['size']>region.y1+.1:return -1
                page.insert_text((x,y),content,fontname=item['name'],fontsize=item['size'],color=item['color'])
                bottom=max(bottom,y-item['font'].descender*item['size'])
                x+=item['font'].text_length(content,fontsize=item['size'])
            baseline+=max(self.fonts[key]['size'] for _,key in line)*self.line_ratio
        return region.y1-bottom
