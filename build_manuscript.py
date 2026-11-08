from pathlib import Path
import re,json,csv,zipfile,hashlib,shutil
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
from collections import Counter
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import manuscript_content as C

ROOT=Path(__file__).resolve().parent; OUT=ROOT.parent/'output'
OUT.mkdir(exist_ok=True)
S=json.loads((ROOT/'data/summary.json').read_text())
R={
'DAPPER':('B. H. Sigelman et al., “Dapper, a large-scale distributed systems tracing infrastructure,” Google, technical report, 2010.','https://research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure/'),
'TRACE':('W3C, “Trace Context,” W3C Recommendation, Nov. 23, 2021.','https://www.w3.org/TR/trace-context-1/'),
'OTEL':('OpenTelemetry Authors, “Overview,” OpenTelemetry Specification, accessed Nov. 3, 2026.','https://opentelemetry.io/docs/specs/otel/overview/'),
'MICRORCA':('L. Wu, J. Tordsson, E. Elmroth, and O. Kao, “MicroRCA: Root cause localization of performance issues in microservices,” in Proc. IEEE/IFIP NOMS, 2020, pp. 1–9, doi: 10.1109/NOMS47738.2020.9110353.','https://doi.org/10.1109/NOMS47738.2020.9110353'),
'YRCA':('J. Soldani, S. Forti, and A. Brogi, “yRCA: An explainable failure root cause analyser,” Science of Computer Programming, vol. 230, Art. no. 102997, 2023, doi: 10.1016/j.scico.2023.102997.','https://doi.org/10.1016/j.scico.2023.102997'),
'CASCADES':('J. Soldani, S. Forti, L. Roveroni, and A. Brogi, “Explaining microservices’ cascading failures from their logs,” Software: Practice and Experience, vol. 55, no. 5, pp. 809–828, 2025, doi: 10.1002/spe.3400.','https://doi.org/10.1002/spe.3400'),
'MICRORANK':('G. Yu et al., “MicroRank: End-to-end latency issue localization with extended spectrum analysis in microservice environments,” in Proc. The Web Conference, 2021, pp. 3087–3098, doi: 10.1145/3442381.3449905.','https://doi.org/10.1145/3442381.3449905'),
'XAI':('P. J. Phillips et al., “Four principles of explainable artificial intelligence,” NISTIR 8312, 2021, doi: 10.6028/NIST.IR.8312.','https://doi.org/10.6028/NIST.IR.8312'),
'PROV':('L. Moreau and P. Missier, Eds., “PROV-DM: The PROV data model,” W3C Recommendation, Apr. 30, 2013.','https://www.w3.org/TR/prov-dm/'),
'IR':('A. Nelson, S. Rekhi, M. Souppaya, and K. Scarfone, “Incident response recommendations and considerations for cybersecurity risk management: A CSF 2.0 community profile,” NIST SP 800-61 Rev. 3, 2025, doi: 10.6028/NIST.SP.800-61r3.','https://doi.org/10.6028/NIST.SP.800-61r3'),
'GOV':('A. Ologun, O. M. Ikeakaonwu, A. F. Ibidunmoye, G. A. Eneano, C. C. Chuwa, and L. O. Kolawole, “AI governance and ethical frameworks for public-sector AI decision systems: An institutional operationalisation model,” AI and Ethics, vol. 6, Art. no. 294, 2026, doi: 10.1007/s43681-026-01143-x.','https://doi.org/10.1007/s43681-026-01143-x'),
'TRUST':('E. I. Igbodor, I. C. Mordi, N. B. Umoru, S. C. Akaelu, S. O. Akaelu, and F. T. Omigbodun, “Trust calibration in human-AI collaborative decision-making: A cross-domain investigation of climate intelligence and organisational governance systems,” Human-Intelligent Systems Integration, 2026, doi: 10.1007/s42454-026-00111-4.','https://doi.org/10.1007/s42454-026-00111-4'),
'SHA':('National Institute of Standards and Technology, “Secure Hash Standard,” FIPS PUB 180-4, Aug. 2015, doi: 10.6028/NIST.FIPS.180-4.','https://doi.org/10.6028/NIST.FIPS.180-4'),
'DSS':('National Institute of Standards and Technology, “Digital Signature Standard,” FIPS PUB 186-5, Feb. 2023, doi: 10.6028/NIST.FIPS.186-5.','https://doi.org/10.6028/NIST.FIPS.186-5'),
'JCS':('A. Rundgren, B. Jordan, and S. Erdtman, “JSON Canonicalization Scheme (JCS),” RFC 8785, Jun. 2020, doi: 10.17487/RFC8785.','https://www.rfc-editor.org/rfc/rfc8785.html'),
'EDDSA':('S. Josefsson and I. Liusvaara, “Edwards-Curve Digital Signature Algorithm (EdDSA),” RFC 8032, Jan. 2017, doi: 10.17487/RFC8032.','https://www.rfc-editor.org/rfc/rfc8032.html'),
'CT':('B. Laurie, E. Messeri, and R. Stradling, “Certificate Transparency Version 2.0,” RFC 9162, Dec. 2021, doi: 10.17487/RFC9162.','https://www.rfc-editor.org/rfc/rfc9162.html'),
'SELECTIVE':('R. El-Yaniv and Y. Wiener, “On the foundations of noise-free selective classification,” Journal of Machine Learning Research, vol. 11, pp. 1605–1641, 2010.','https://jmlr.org/papers/v11/el-yaniv10a.html'),
'CLASSIFY':('Y. Geifman and R. El-Yaniv, “Selective classification for deep neural networks,” in Advances in Neural Information Processing Systems, vol. 30, 2017.','https://papers.nips.cc/paper_files/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html'),
'SELECTIVENET':('Y. Geifman and R. El-Yaniv, “SelectiveNet: A deep neural network with an integrated reject option,” in Proc. 36th Int. Conf. Machine Learning, PMLR, vol. 97, 2019, pp. 2151–2159.','https://proceedings.mlr.press/v97/geifman19a.html'),
'BENCH':('Y. Gan et al., “An open-source benchmark suite for microservices and their hardware-software implications for cloud & edge systems,” in Proc. ASPLOS, 2019, pp. 3–18, doi: 10.1145/3297858.3304013.','https://doi.org/10.1145/3297858.3304013'),
'BOOT':('B. Efron, “Bootstrap methods: Another look at the jackknife,” The Annals of Statistics, vol. 7, no. 1, pp. 1–26, 1979, doi: 10.1214/aos/1176344552.','https://doi.org/10.1214/aos/1176344552'),
'RMF':('National Institute of Standards and Technology, “Artificial Intelligence Risk Management Framework (AI RMF 1.0),” NIST AI 100-1, Jan. 2023, doi: 10.6028/NIST.AI.100-1.','https://doi.org/10.6028/NIST.AI.100-1')}
order=[]
for text in C.INTRO+C.METHOD+C.RESULTS:
    for key in re.findall(r'\[([A-Z]+)\]',text):
        if key not in order:order.append(key)
assert set(order)==set(R) and len(order)==23
refno={k:i+1 for i,k in enumerate(order)}
def cite(text):return re.sub(r'\[([A-Z]+)\]',lambda m:f'[{refno[m[1]]}]',text)
def words(text):return len(re.sub(r'\[[A-Z]+\]','',text).split())
wordcounts={k:words(' '.join(getattr(C,k)) if isinstance(getattr(C,k),list) else getattr(C,k)) for k in ['TITLE','ABSTRACT','INTRO','METHOD','RESULTS','CONCLUSION']}
assert wordcounts['INTRO']==650 and wordcounts['RESULTS']==750

doc=Document();sec=doc.sections[0]
sec.page_height=Inches(11.7);sec.page_width=Inches(8.3)
sec.top_margin=sec.bottom_margin=Inches(.72);sec.left_margin=sec.right_margin=Inches(.8)
sec.header_distance=sec.footer_distance=Inches(.3)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3','Caption']:
    st=doc.styles[name];st.font.name='Times New Roman';st.font.color.rgb=RGBColor(0,0,0)
    for tag in ['w:asciiTheme','w:hAnsiTheme','w:eastAsiaTheme','w:cstheme']:
        rf=st.element.find('.//'+qn('w:rFonts'))
        if rf is not None and qn(tag) in rf.attrib:del rf.attrib[qn(tag)]
for st in doc.styles:
    for el in list(st.element.iter(qn('w:pBdr'))):el.getparent().remove(el)
normal=doc.styles['Normal'];normal.font.size=Pt(11)
normal.paragraph_format.line_spacing=1.08;normal.paragraph_format.space_after=Pt(7)
for name,size in [('Title',19),('Heading 1',13),('Heading 2',11.5)]:
    doc.styles[name].font.size=Pt(size);doc.styles[name].font.bold=True
    doc.styles[name].paragraph_format.space_before=Pt(12)
    doc.styles[name].paragraph_format.space_after=Pt(7)
doc.styles['Title'].paragraph_format.space_before=Pt(0)
doc.styles['Caption'].font.size=Pt(9);doc.styles['Caption'].font.italic=False
doc.styles['Caption'].paragraph_format.space_after=Pt(9)
for name in ['Reference','Audit note']:
    st=doc.styles.add_style(name,1);st.font.name='Times New Roman';st.font.size=Pt(9.5 if name=='Reference' else 9)
    st.paragraph_format.space_after=Pt(5);st.paragraph_format.line_spacing=1.02
doc.styles['Reference'].paragraph_format.left_indent=Inches(.30)
doc.styles['Reference'].paragraph_format.first_line_indent=Inches(-.30)
header=sec.header.paragraphs[0];header.text='EVIDENCE GATED DIAGNOSIS  |  COMPUTATIONAL STUDY'
header.runs[0].font.size=Pt(8)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');fr=OxmlElement('w:r');ft=OxmlElement('w:t');ft.text='1';fr.append(ft);fld.append(fr);footer._p.append(fld)

def p(text,style=None):
    q=doc.add_paragraph(cite(text),style);q.paragraph_format.widow_control=True;return q
def heading(text,level=1):return doc.add_heading(text,level)
def table(caption,heads,rows,widths):
    c=p(caption,'Caption');c.paragraph_format.keep_with_next=True
    t=doc.add_table(rows=1,cols=len(heads));t.autofit=False;t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,w in enumerate(widths):t.columns[i].width=Inches(w)
    for i,h in enumerate(heads):t.rows[0].cells[i].text=h
    for row in rows:
        for cell,txt in zip(t.add_row().cells,row):cell.text=str(txt)
    for i,row in enumerate(t.rows):
        trpr=row._tr.get_or_add_trPr(); no=OxmlElement('w:cantSplit');trpr.append(no)
        if i==0:
            repeat=OxmlElement('w:tblHeader');trpr.append(repeat)
        for j,cell in enumerate(row.cells):
            cell.width=Inches(widths[j]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            props=cell._tc.get_or_add_tcPr();shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'DDE7EE' if i==0 else ('F5F7F9' if i%2==0 else 'FFFFFF'));props.append(shade)
            margins=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                el=OxmlElement('w:'+side);el.set(qn('w:w'),'85');el.set(qn('w:type'),'dxa');margins.append(el)
            props.append(margins);border=OxmlElement('w:tcBorders')
            for side in ['top','left','bottom','right']:
                el=OxmlElement('w:'+side);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'D9D9D9');border.append(el)
            props.append(border)
            for pp in cell.paragraphs:
                pp.paragraph_format.space_after=Pt(0);pp.paragraph_format.line_spacing=1.0
                pp.alignment=WD_ALIGN_PARAGRAPH.LEFT if j==0 else WD_ALIGN_PARAGRAPH.CENTER
                for run in pp.runs:run.font.size=Pt(9);run.bold=(i==0)
    doc.add_paragraph().paragraph_format.space_after=Pt(0)
    return t
def figure(filename,caption):
    q=doc.add_paragraph();q.alignment=WD_ALIGN_PARAGRAPH.CENTER;q.paragraph_format.keep_with_next=True
    q.add_run().add_picture(str(ROOT/'figures'/filename),width=Inches(6.35))
    p(caption,'Caption')
def mathrun(text):
    r=OxmlElement('m:r');pr=OxmlElement('m:rPr');sty=OxmlElement('m:sty');sty.set(qn('m:val'),'p');pr.append(sty);r.append(pr)
    wpr=OxmlElement('w:rPr');sz=OxmlElement('w:sz');sz.set(qn('w:val'),'21');wpr.append(sz);r.append(wpr)
    t=OxmlElement('m:t');t.text=text;r.append(t);return r
def elements(parent,value):
    if isinstance(value,str):parent.append(mathrun(value))
    elif isinstance(value,list):
        for v in value:elements(parent,v)
    else:parent.append(value)
def sub(base,index):
    el=OxmlElement('m:sSub');e=OxmlElement('m:e');elements(e,base);el.append(e)
    b=OxmlElement('m:sub');elements(b,index);el.append(b);return el
def sup(base,index):
    el=OxmlElement('m:sSup');e=OxmlElement('m:e');elements(e,base);el.append(e)
    b=OxmlElement('m:sup');elements(b,index);el.append(b);return el
def ss(base,index,power):
    el=OxmlElement('m:sSubSup')
    for name,value in [('e',base),('sub',index),('sup',power)]:
        b=OxmlElement('m:'+name);elements(b,value);el.append(b)
    return el
def frac(top,bottom):
    el=OxmlElement('m:f')
    for name,value in [('num',top),('den',bottom)]:
        b=OxmlElement('m:'+name);elements(b,value);el.append(b)
    return el
def hat(base):
    el=OxmlElement('m:acc');pr=OxmlElement('m:accPr');ch=OxmlElement('m:chr');ch.set(qn('m:val'),'̂');pr.append(ch);el.append(pr)
    e=OxmlElement('m:e');elements(e,base);el.append(e);return el
def eq(text,num):
    q=doc.add_paragraph();q.paragraph_format.space_before=Pt(3);q.paragraph_format.space_after=Pt(6)
    q.paragraph_format.keep_together=True
    om=OxmlElement('m:oMath');elements(om,text);q._p.append(om)
    q.add_run('   ('+str(num)+')').font.size=Pt(10)
    return q
def hyperlink(q,text,url):
    rel=q.part.relate_to(url,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True)
    a=OxmlElement('w:hyperlink');a.set(qn('r:id'),rel);r=OxmlElement('w:r');props=OxmlElement('w:rPr')
    color=OxmlElement('w:color');color.set(qn('w:val'),'204D73');props.append(color);r.append(props)
    tx=OxmlElement('w:t');tx.text=text;r.append(tx);a.append(r);q._p.append(a)

doc.add_heading(C.TITLE,0)
p('Research article | Reproducible synthetic computational study','Subtitle')
heading('Abstract');p(C.ABSTRACT)
p('Keywords—'+ '; '.join(C.KEYWORDS)+'.')
heading('1 Introduction')
for para in C.INTRO:p(para)
heading('2 Methodology')
for i,para in enumerate(C.METHOD):
    p(para)
    if i==1:
        eq([sub('y','O'),' | r,f ∼ N(',sub('μ','O'),'(r,f), ',sub('Σ','O'),')'],1)
        eq(['Σ = diag(',ss('σ','a','2'),'I + ',ss('τ','a','2'),'1',sup('1','T'),', ',ss('σ','t','2'),'I + ',ss('τ','t','2'),'1',sup('1','T'),')'],'1a')
        eq([sub('p','r'),' = ',frac(['exp(',sub('ℓ','r'),')'],[sub('∑','k'),'exp(',sub('ℓ','k'),')'])],2)
        eq([sub('ℓ','r'),' = −',frac('1','2'),sup(['(',sub('y','O'),'−',sub('μ','r,O'),')'],'T'),ss('Σ','O','−1'),'(',sub('y','O'),'−',sub('μ','r,O'),') + log ',sub('π','r')],'2a')
    if i==2:
        eq(['g = 1{10(1−',sub('p',hat('r')),') ≤ 1} · 1{',hat('r'),' ∈ O} · 1{|O| ≥ 3} · ',sub('I','v'),',   ',hat('r'),' = arg ',sub('max','r'),sub('p','r')],3)
    if i==3:
        eq([sub('h','j'),' = SHA256(',sub('b','j'),'),    M = J(id, model, rule, ',hat('r'),', p, {j:',sub('h','j'),'}, review)'],4)
        eq('s = Ed25519.Sign(sk, domain ∥ M)', '4a')
        eq([sub('I','v'),' = Verify(pk,s,domain ∥ M) · ',sub('B','id'),' · ',sub('∏','j'),'1{SHA256(',sub('b','j'),')=',sub('h','j'),'}'], '4b')
        eq(['C = ',sup('n','−1'),sub('∑','i'),sub('g','i'),',    R = ',frac([sub('∑','i'),sub('g','i'),'1{',sub(hat('r'),'i'),'≠',sub('r','i'),'}'],[sub('∑','i'),sub('g','i')]),',    Y = ',sup('n','−1'),sub('∑','i'),sub('g','i'),'1{',sub(hat('r'),'i'),'=',sub('r','i'),'}'],5)
table('TABLE I  Experimental design and notation', ['Element','Specification'],[
('Nodes and edges','API→Auth; API→Account; Account→Ledger; Ledger→Payment, Audit, Database'),
('Observation set O','Observed service nodes; yₒ contains their amplitude and onset features'),
('Covariance parameters','σₐ=1.1; τₐ=0.35; σₜ=0.8; τₜ=0.30; πᵣ=1/7'),
('Samples and seed','3 families × 200 independent incidents × 4 masks; seed 20261103'),
('Evidence notation','bⱼ: evidence bytes; J: restricted encoding; sk/pk: signing/verification keys'),
('Integrity Iᵥ and Bᵢd','Bᵢd checks object-set, node and incident binding; Iᵥ also checks signature and digests'),
('Outcome notation','C: coverage; R: error among accepted cases; Y: correct accepted yield'),
('Primary threshold','0.90 fixed by an illustrative 10:1 error-to-deferral loss ratio'),
('Sensitivity thresholds','0.50, 0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 0.99')],[1.55,4.95])
heading('3 Empirical results from synthetic computation')
for i,para in enumerate(C.RESULTS):
    p(para)
    if i==1:
        figure('figure1_accuracy.png','Fig. 1. Diagnostic accuracy across nested missingness conditions. Evidence gate accuracy is conditional on acceptance; other curves use all 600 observations per condition. This is synthetic model performance, not measured production reliability.')
        rows=[]
        for k in ['0.0','0.15','0.3','0.45']:
            s=S[k];rows.append([f'{float(k)*100:.0f}',f'{s["anomaly_accuracy"]*100:.1f}',f'{s["posterior_accuracy"]*100:.1f}',f'{s["evidence_accepted"]}/600',f'{s["evidence_coverage"]*100:.1f}',str(s['evidence_wrong'])])
        table('TABLE II  Matched model results with a 0.90 acceptance threshold',['Missing %','Anomaly accuracy %','Graph accuracy %','Gate accepted','Gate coverage %','Gate errors'],rows,[.7,1.1,1.1,1.2,1.2,1.2])
    if i==4:
        figure('figure2_coverage.png','Fig. 2. Left: pooled risk versus coverage for fixed threshold sensitivity, with 0.90 labelled. Right: evidence gated coverage and correct accepted yield. Their equality reflects zero observed accepted errors in the matched model conditions, not guaranteed correctness.')
    if i==5:
        table('TABLE III  Model mismatch at 30 percent missingness',['Condition','Graph accuracy %','Gate accepted','Accepted correct','Accepted accuracy %'],[
            ['Matched model','81.7','325/600','325','100.0'],
            ['Weakened root and noisy onset','70.5','289/600','268','92.7']],[1.75,1.15,1.15,1.1,1.35])
    if i==6:
        figure('figure3_integrity.png','Fig. 3. Integrity verifier outcomes for 200 records per category. The five violation categories produce 1,000 rejections. Re-signed false claims pass because a valid signature authenticates the committed bytes and does not establish causal truth.')
heading('4 Conclusion')
for para in C.CONCLUSION.split('\n\n'):p(para)
heading('Data and code availability',2)
p('The accompanying reproducibility package contains the generator, incident and telemetry CSV files, integrity tests, model mismatch results, figure sources, a signed example, and the supplied-source crosswalk. All measurements are synthetic. No human participants, employer systems, customer records, or production incidents were studied.')
heading('References')
for key in order:
    t,u=R[key]
    if 'doi: ' in t:
        body,doi=t.rsplit('doi: ',1);q=p(f'[{refno[key]}] '+body,'Reference');hyperlink(q,'doi: '+doi,u)
    else:
        q=p(f'[{refno[key]}] '+t,'Reference');q.add_run(' Available: ');hyperlink(q,u,u)

# Preserve and assess every supplied reference, without asserting it supports unrelated findings.
source_path=ROOT.parent/'upload/Pasted markdown(20261103-102217).md'
source=source_path.read_text();entries=[];nref=24
def clean_url(u):
    u=u.replace('\\&','&');z=urlsplit(u)
    return urlunsplit((z.scheme,z.netloc,z.path,urlencode([(k,v) for k,v in parse_qsl(z.query) if not k.startswith('utm_')]),z.fragment))
def ieee_author(s):
    s=s.replace('*','')
    return re.sub(r'([A-Za-zÀ-ž-]+),\s*((?:[A-Z]\.)+)',lambda m:' '.join(re.findall('[A-Z]\\.',m[2]))+' '+m[1],s)
for line in source.splitlines():
    m=re.match(r'(\d+)\. (.*?) \((\d{4}|n\.d\.)\) ‘(.+?)’[,\.]? (.*)',line)
    assert m,line
    old=int(m[1]);authors=ieee_author(m[2]);year=m[3];title=m[4];rest=m[5]
    links=re.findall(r'\]\((https?://[^\s]+?)\)',rest)
    u=clean_url(links[0]) if links else ''
    # Preserve venue text before the first link / narrative provenance note.
    venue=re.split(r'Available at:|Repository record:|Repository DOI:|Bibliographic record:|\[https?://|\*\*',rest)[0]
    venue=venue.replace('*','').strip().rstrip('.')
    venue=re.sub(r'(\d+)\((\d+)\)',r'vol. \1, no. \2',venue)
    venue=venue.replace('article ','Art. no. ')
    if not venue:venue='[publication venue not verified]'
    bibliog=f'{authors}, “{title},” {venue}, {year.rstrip(".")}.'
    supplied_warning=' '.join(re.findall(r'\*\*(.*?)\*\*',rest))
    low=title.lower()
    if old in [40,68]:scope='Cited conceptual governance context';status='Publisher metadata and abstract checked';rid=refno['TRUST' if old==40 else 'GOV']
    else:
        rid=nref;nref+=1
        if any(k in low for k in ['governance','accountability','ethical','trust','agency','safeguard','sovereignty','whistleblowing','redress','metrics']):scope='Potential governance context; not RCA evidence'
        elif any(k in low for k in ['digital twin','iot','bim','cyber-physical','supply chain','synthetic','digital transformation']):scope='Adjacent systems or methods; not RCA validation'
        else:scope='Outside the direct diagnosis and evidence question'
        status='Supplied record; not independently verified'
    note=supplied_warning
    if old==68:note='Publisher page describes survey/interview data but its data-availability statement says no datasets were generated or analysed. Used only for the conceptual documentation argument; quantitative claims are not transferred.'
    if old==40:note='Used for the conceptual distinction between capability and calibrated reliance; no cross-domain effect sizes are transferred.'
    entries.append(dict(supplied_number=old,reference_number=rid,title=title,citation=bibliog,url=u,status=status,scope=scope,note=note,original_entry=line))
assert len(entries)==89 and nref==111
with (ROOT/'data/supplied_reference_audit.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(entries[0]));w.writeheader();w.writerows(entries)
(ROOT/'data/reference_inventory.json').write_text(json.dumps({'active_references':[{"number":refno[k],"key":k,"citation":R[k][0],"url":R[k][1]} for k in order],'supplied_references':entries},ensure_ascii=False,indent=2))

heading('Author review appendix').paragraph_format.page_break_before=True
p('This appendix is an editorial audit and should be resolved before journal submission. The collection contains 110 unique bibliographic records: 23 cited sources and 87 additional supplied records. All 89 attached entries are represented; supplied items 40 and 68 are already cited in the main bibliography. The remaining entries are preserved below rather than being used as unsupported or irrelevant citations. This is not a claim that the manuscript contains 110 verified research references.')
p('The source brief did not identify a target journal. General IEEE referencing was selected for this draft; no journal-specific fit or acceptance is asserted. The 89 supplied records were screened by their supplied titles and metadata. Two relevant records were checked against publisher pages and used for limited conceptual claims. Other entries require article-level verification and relevance assessment before inclusion in a submission bibliography.')
table('TABLE A1  Requested structure and delivered prose word counts',['Component','Words','Requested'],[[k,wordcounts[v],t] for k,v,t in [('Title','TITLE','10–12'),('Abstract','ABSTRACT','150–190'),('Introduction','INTRO','650'),('Methodology','METHOD','350–450'),('Empirical results','RESULTS','750'),('Conclusion','CONCLUSION','170–200')]],[2.8,1.2,2.5])
p('Counts exclude headings, citation markers, equations, tables, captions, references, and this appendix. The paper includes five keywords, three figures, and three main tables.')
heading('Assessment of the supplied research brief',2)
for txt in [
'The brief reports 50 trials and a 66.3% time reduction but supplies neither the claimed CSV nor event logs, investigator records, or an executable experiment producing those values. Those claims were not carried into the manuscript.',
'The brief describes 25 baseline trials with binary accuracy of 78%; that percentage is not an integer number of correct diagnoses out of 25. The supplied means and standard deviations cannot be authenticated from the available material.',
'Reproducing the supplied ranking arithmetic for a ledger failure gives the API gateway a score of 0.5882 and the ledger 0.1765. The caller-to-dependency graph is interpreted in the wrong direction for its originating-fault rule. The new model uses explicit reverse reachability.',
'The supplied signature is a text placeholder built from a digest and a literal string, not an asymmetric signature. The new study signs and verifies actual Ed25519 messages using an openly disclosed simulation-only fixture key.',
'The supplied generated payload differs from its own schema in required field names, environment values, and telemetry types. The new signed manifest explicitly describes its restricted scope and records that no human review occurred.',
'A preserved evidence object does not establish truthful collection, independent approval, append-only retention, trusted time, or compliance. The proposed method implements incident binding and integrity tests; it does not implement a full regulatory assurance system.'
]:p(txt)
heading('Use of the supplied literature',2)
p('The supplied corpus spans AI governance, business strategy, digital twins, health, education, agriculture, water treatment, and batteries. Its strongest conceptual connection is the need for accountable decisions and calibrated reliance. Much of it has no direct evidential role in microservice root cause localisation. The entries below therefore document inclusion decisions for the entire corpus rather than pad the paper with claims the sources cannot support.')
p(f'Supplied item 40 corresponds to reference [{refno["TRUST"]}]; supplied item 68 corresponds to reference [{refno["GOV"]}]. Both are preserved in the machine-readable crosswalk. For item 68, the publisher abstract describes survey and interview data while the data-availability statement says no datasets were generated or analysed. This discrepancy is flagged for author review, and no numerical findings from that source are used.')
heading('Supplied reference register',2)
p('Reference numbers continue from the main bibliography for inventory traceability only. “Not independently verified” describes the limits of this review; it does not establish that a publication is invalid. Original author abbreviations and missing fields are retained where authoritative details were unavailable. The complete original entries are preserved in the accompanying audit CSV.','Audit note')
for e in entries:
    if e['supplied_number'] in [40,68]:continue
    q=p(f'[{e["reference_number"]}] '+e['citation'],'Reference')
    if e['url']:
        q.add_run(' Available: ')
        # Keep very long ResearchGate slugs out of the displayed line, without losing the target.
        label=e['url'] if len(e['url'])<115 else urlsplit(e['url']).netloc+' — supplied record'
        hyperlink(q,label,e['url'])
    q.paragraph_format.keep_with_next=True
    status=f'Supplied item {e["supplied_number"]}. {e["status"]}. {e["scope"]}.'
    if e['note']:status+=' '+e['note']
    p(status,'Audit note')

doc.core_properties.title=C.TITLE
doc.core_properties.subject='Synthetic computational research manuscript with supplied-reference audit'
doc.core_properties.author=''
doc.core_properties.keywords='; '.join(C.KEYWORDS)
path=OUT/'Fintech_Evidence_Gated_Diagnosis_IEEE.docx';doc.save(path)
(ROOT/'data/word_counts.json').write_text(json.dumps(wordcounts,indent=2))
(ROOT/'technical_references.json').write_text(json.dumps(R,indent=2,ensure_ascii=False))
(ROOT/'README.md').write_text('''# Reproducible synthetic fintech diagnosis study

This package accompanies **Evidence Gated Root Cause Diagnosis for Fintech Microservices Under Telemetry Loss**.
No production traces, financial customer data, human participants, or measured incident-response times are included.

## Reproduction

Run `python run_study.py` in this directory. It writes the incident-level data, telemetry, summary, signature tests and figures. The recorded environment used Python 3.12.14 and NumPy 2.3.5. See requirements.txt for the packages used. `python build_manuscript.py` recreates the Word file if the two source attachments are placed under the relative `../upload/` paths referred to by the script. Manuscript text is in manuscript_content.py.

## Design

The six call edges are API→Auth, API→Account, Account→Ledger, Ledger→Payment, Ledger→Audit and Ledger→Database. Failure symptoms propagate through reverse reachability. There are 600 independent incident seeds, each observed under four nested masks. The 2,400 rows must not be treated as independent. Family names denote amplitude multipliers rather than executable fault injections. All priors are uniform. Likelihood parameters are known from the synthetic generator and are not fitted to operational data. The fixed threshold derives from an illustrative 10:1 wrong-acceptance to deferral loss. There was no preregistration or held-out model training.

Noise has a service-independent component plus a shared component within each feature block. The missingness stress masks remove entire service records independently of fault state. The mismatch study weakens the root amplitude by multiplying its realised value by 0.6 and adds independent onset noise with standard deviation 1.2. Neither the inference model nor threshold is retuned.

## Outputs

- data/incidents.csv: 2,400 incident/missingness observations, 600 independent clusters.
- data/telemetry.csv: 16,800 node-level rows with generated values and observed flags. Unobserved values are retained solely for reproduction and are not passed to inference.
- data/model_mismatch.csv: 600 deliberately misspecified observations at 30% missingness.
- data/integrity_checks.csv: 1,400 checks, including 1,000 integrity violations, 200 clean controls, and 200 signed false claims.
- data/summary.json: exact aggregate values and cluster-bootstrap intervals.
- data/example_bundle.json: one signed manifest, telemetry objects, signature and public test key.
- data/supplied_code_check.json: reproduction of the defective supplied ranking rule.
- data/supplied_reference_audit.csv: all 89 supplied references with original text, scope and status.
- data/reference_inventory.json: 110 unique bibliographic records; 23 active citations and 87 author-review entries.
- figures/: three graphs calculated from the simulation.

## Integrity profile

Ed25519 signs the domain prefix and serialized manifest. The manifest contains SHA-256 digests of exact evidence bytes. The signature is detached. JSON is a restricted ASCII encoding with integral metadata and decimal-string measurements, sorted keys and compact separators. This is not a claim of general RFC 8785 conformance. Verification checks the signature, evidence object set, each digest, and incident/node binding. It does not check causal truth. The public deterministic private-key fixture is intentionally included in the code only to make reproduction possible; it must never be used for real security. Five mutations are evaluated independently; this is not an exhaustive adversarial security assessment. Initial integrity fixtures are the first 200 full-observation incidents, all from the first family; cryptographic mutation checks do not depend on failure-family accuracy.

## Evidence limits

The source brief's claimed 50-trial outcomes and response-time gains were not used as data. No conclusion about actual engineer speed, cognitive load, regulatory compliance, or production performance follows. The perfect matched-model accepted accuracy is an observed simulation result with favourable assumptions. Under mismatch, accepted accuracy is 92.7%. All supplied bibliography entries are retained, but only two supplied entries are used as checked conceptual context. Other supplied records require verification and relevance review before journal submission.
''')
import importlib.metadata
names=['numpy','pandas','matplotlib','cryptography','python-docx']
(ROOT/'requirements.txt').write_text('\n'.join(n+'=='+importlib.metadata.version(n) for n in names)+'\n')
print(json.dumps({'docx':str(path),'word_counts':wordcounts,'active_references':len(order),'supplied_references':len(entries),'total_records':110},indent=2))
