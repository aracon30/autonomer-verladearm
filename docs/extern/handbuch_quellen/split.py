import re
def split(body):
    pos=0;out=[]
    pat=re.compile(r'<w:(p|tbl|sectPr)\b')
    while True:
        m=pat.search(body,pos)
        if not m: break
        tag=m.group(1); d=0
        tok=re.compile(r'<(/?)w:%s\b[^>]*?(/?)>'%tag)
        for n in tok.finditer(body,m.start()):
            if n.group(2)=='/':
                if d==0: end=n.end();break
                continue
            d+= -1 if n.group(1)=='/' else 1
            if d==0: end=n.end();break
        out.append((tag,body[m.start():end])); pos=end
    return out
def load(path='x/word/document.xml'):
    t=open(path,encoding='utf-8').read()
    a=t.index('<w:body>')+8; b=t.index('</w:body>')
    return t[:a], split(t[a:b]), t[b:]
