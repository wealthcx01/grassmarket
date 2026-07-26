import httpx, zipfile, io, re, json
API="https://grassmarket-api-staging.up.railway.app"
s=httpx.Client(timeout=60)
s.headers["Authorization"]="Bearer "+s.post(f"{API}/auth/login",json={"email":"advisor@bruntsfieldcapital.com","password":"grassmarket-demo"}).json()["access_token"]
def paras(docx_bytes):
    x=zipfile.ZipFile(io.BytesIO(docx_bytes)).read('word/document.xml').decode('utf8','ignore')
    # split into paragraphs, strip tags
    out=[]
    for p in re.findall(r'<w:p[ >].*?</w:p>', x, re.S):
        t=re.sub('<[^>]+>','',p)
        t=re.sub(r'\s+',' ',t).strip()
        if t: out.append(t)
    return out
want={"Revolut":{}, "Hargreaves Lansdown":{}}
for e in s.get(f"{API}/engagements").json():
    title=e.get('title','')
    subj=next((k for k in want if title.startswith(k)), None)
    if not subj: continue
    for d in s.get(f"{API}/engagements/{e['id']}/deliverables").json():
        if d['type'] in ('executive_summary','platform_power_report','infrastructure_heatmap'):
            b=s.get(f"{API}/deliverables/{d['id']}/download").content
            want[subj][d['type']]=paras(b)
json.dump(want, open("scratch/stage/report_text.json","w"), indent=1)
for subj in want:
    for t in want[subj]:
        print(subj, t, len(want[subj][t]), "paras")
