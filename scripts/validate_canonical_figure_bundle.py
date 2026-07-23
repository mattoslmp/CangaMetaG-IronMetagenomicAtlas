#!/usr/bin/env python3
"""Validate the final 80-record canonical figure manifest and runtime bundle."""
from __future__ import annotations
from pathlib import Path
import hashlib,json,re,sys
import pandas as pd
from PIL import Image
from lxml import etree
ROOT=Path(__file__).resolve().parents[1]
FIG=ROOT/'outputs/final_publication_figures'; MAN=ROOT/'data/final_figure_script_manifest.csv'
OUT=ROOT/'validation/CANONICAL_BUNDLE_VALIDATION.json'; OUT.parent.mkdir(parents=True,exist_ok=True)
checks=[]
def check(name,condition,evidence=None): checks.append({'check':name,'passed':bool(condition),'evidence':evidence})
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
for p in [ROOT/'app.py',ROOT/'requirements.txt',ROOT/'environment.yml',MAN,ROOT/'scripts/regenerate_module_figures_filtered_v9.py',ROOT/'scripts/figures/generate_s6_s7.py']:
 check(f'runtime asset {p.relative_to(ROOT)}',p.exists() and p.stat().st_size>0,str(p))
if MAN.exists():
 df=pd.read_csv(MAN).fillna('')
 check('manifest has 80 records',len(df)==80,len(df))
 check('manifest has 8 main figures',df['Figure'].astype(str).str.fullmatch(r'Figure [1-8]').sum()==8,int(df['Figure'].astype(str).str.fullmatch(r'Figure [1-8]').sum()))
 check('manifest has 72 supplementary records',df['Figure'].astype(str).str.startswith('Supplementary Figure').sum()==72,int(df['Figure'].astype(str).str.startswith('Supplementary Figure').sum()))
 check('manifest Figure labels unique',df['Figure'].is_unique,df['Figure'][df['Figure'].duplicated()].tolist())
 for _,r in df.iterrows():
  for col,hcol in [('PNG','SHA256_PNG'),('PDF','SHA256_PDF'),('SVG','SHA256_SVG')]:
   name=str(r[col]).strip(); p=FIG/name
   ok=bool(name) and p.exists() and p.stat().st_size>0
   check(f"{r['Figure']} {col} exists",ok,name)
   expected=str(r.get(hcol,'')).strip()
   if ok and expected: check(f"{r['Figure']} {col} SHA256",sha(p)==expected,{'expected':expected,'actual':sha(p)})
   if ok and col=='PNG':
    try:
     with Image.open(p) as im: im.verify(); size=Image.open(p).size
     check(f"{r['Figure']} PNG dimensions",size[0]>=800 and size[1]>=500,size)
    except Exception as e: check(f"{r['Figure']} PNG readable",False,str(e))
# Runtime safety and syntax-oriented assertions
app_text=(ROOT/'app.py').read_text(errors='ignore') if (ROOT/'app.py').exists() else ''
check('no hard-coded /mnt/data or /home runtime path',not re.search(r'["\']/(?:mnt/data|home)/',app_text),None)
check('canonical module statuses in app','KEGG_MODULE_DISPLAY_STATUSES = ["Complete", "1 block missing"]' in app_text,None)
# Taxonomy palette uniqueness
pal=ROOT/'data/taxonomy_palette.json'
if pal.exists():
 data=json.loads(pal.read_text()); vals=[str(v).upper() for v in data.values()]
 check('taxonomy palette values unique',len(vals)==len(set(vals)),{'entries':len(vals),'unique':len(set(vals))})
passed=sum(x['passed'] for x in checks); report={'status':'VALIDATED' if passed==len(checks) else 'FAILED','checks_total':len(checks),'checks_passed':passed,'checks_failed':len(checks)-passed,'manifest_rows':80 if MAN.exists() else 0,'final_figure_counts_including_panels':{e:len(list(FIG.glob(f'*.{e}'))) for e in ('png','pdf','svg')},'checks':checks}
OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({k:report[k] for k in ('status','checks_total','checks_passed','checks_failed','final_figure_counts_including_panels')},indent=2))
raise SystemExit(0 if report['status']=='VALIDATED' else 1)
