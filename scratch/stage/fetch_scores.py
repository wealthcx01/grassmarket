import httpx, re, zipfile, io
API="https://grassmarket-api-staging.up.railway.app"
s=httpx.Client(timeout=60.0)
s.headers["Authorization"]="Bearer "+s.post(f"{API}/auth/login",json={"email":"advisor@bruntsfieldcapital.com","password":"grassmarket-demo"}).json()["access_token"]
print("=== PORTFOLIO (assessments) ===")
for a in s.get(f"{API}/assessments").json():
    print(f"  {a.get('subject'):22} state={a.get('state')} score={a.get('v_index') or a.get('score') or a.get('last_score')} keys={[k for k in a if 'ind' in k or 'score' in k]}")
# engagements -> deliverables -> download exec summary, extract headline
print("\n=== DELIVERABLE HEADLINES ===")
for e in s.get(f"{API}/engagements").json():
    subj=e.get('title','')
    dl=s.get(f"{API}/engagements/{e['id']}/deliverables").json()
    ex=[d for d in dl if d['type']=='executive_summary']
    if not ex: continue
    b=s.get(f"{API}/deliverables/{ex[0]['id']}/download").content
    x=zipfile.ZipFile(io.BytesIO(b)).read('word/document.xml').decode('utf8','ignore')
    t=re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',x))
    m=re.search(r'Platform value V = [\d.]+ \(range [\d.]+.[\d.]+\)', t)
    c=re.search(r'Customer Proposition[^.]{0,60}?[\d.]+', t)
    print(f"  {subj:34} {m.group(0) if m else '(V not found)'}")
