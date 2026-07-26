import httpx
API="https://grassmarket-api-staging.up.railway.app"
def tok(email,pw):
    return httpx.post(f"{API}/auth/login",json={"email":email,"password":pw},timeout=30).json()["access_token"]
adv=httpx.Client(timeout=60,headers={"Authorization":f"Bearer {tok('advisor@bruntsfieldcapital.com','grassmarket-demo')}"})
advisor_id=adv.get(f"{API}/auth/me").json().get("id") or adv.get(f"{API}/me").json().get("id")
print("advisor_id:",advisor_id)
admin=httpx.Client(timeout=60,headers={"Authorization":f"Bearer {tok('admin@bruntsfieldcapital.com','grassmarket-reviewer')}"})
deals=[("Revolut","97cf26a5-1687-4c89-91ad-838e47680dc8","benzinga",10000000),
       ("Hargreaves Lansdown","92521aa1-e741-45c6-af3a-3137c2f24eb5","openbb",15000000),
       ("WeBull","017cbc49-b735-4734-aae4-b681fd4ef977","connecttrade",8000000)]
for name,eid,prod,minor in deals:
    r=admin.post(f"{API}/earnings/commissions/product",json={
        "advisor_id":advisor_id,"engagement_id":eid,"product_id":prod,
        "base_value_minor":minor,"currency":"GBP","base_value_ref":"brokerage sim — illustrative Y1 deal",
        "contract_year":1,"earned_on":"2026-07-21"},timeout=30)
    print(f"  {name:22} sold {prod:12} -> {r.status_code} {('line '+r.json().get('id','') ) if r.status_code<300 else r.text[:160]}")
print("\n=== EARNINGS as advisor ===")
summ=adv.get(f"{API}/earnings/summary").json()
print("summary:",{k:summ.get(k) for k in summ if any(t in k.lower() for t in ('earn','pend','paid','invoic','ytd','project','total'))})
print("commission lines:")
for l in adv.get(f"{API}/earnings/commissions").json():
    print("  ", {k:l.get(k) for k in ('product_id','stream','status','gross','amount','amount_minor','commission_minor','engagement_id') if k in l})
