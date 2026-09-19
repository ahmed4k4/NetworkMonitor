import json,sys,time,urllib.request,urllib.error
B="http://127.0.0.1:8000"
def req(m,p,b=None,t=None):
 d=json.dumps(b).encode() if b is not None else None
 r=urllib.request.Request(B+p,data=d,method=m)
 r.add_header("Content-Type","application/json")
 if t: r.add_header("Authorization","Bearer %s"%t)
 try:
  with urllib.request.urlopen(r,timeout=15) as e:
   return e.status,json.loads(e.read().decode())
 except urllib.error.HTTPError as e:
  try: return e.code,json.loads(e.read().decode())
  except: return e.code,{}
ok=fail=0
def ck(n,c,d=""):
 global ok,fail
 if c: ok+=1; print("  PASS ",n)
 else: fail+=1; print("  FAIL ",n,d)
st,r=req("POST","/api/auth/login",{"username":"admin","password":"admin"})
ck("login 200",st==200,"%s %s"%(st,r))
t=r.get("access_token") or r.get("token")
ck("token",bool(t),"%s"%r)
if not t: sys.exit(1)
nm="qa_rule_%d"%int(time.time())
st,c=req("POST","/api/control/rules",{"name":nm,"description":"qa","action":"BLOCK","enabled":True,"rule_type":"DOMAIN","domain":"example.com","priority":5},t)
ck("create 200",st==200,"%s %s"%(st,c))
rid=c.get("id"); ck("create id",bool(rid),"%s"%c)
st,rules=req("GET","/api/control/rules",t=t)
ck("list 200",st==200)
ck("list array",isinstance(rules,list))
ck("created in list",len([x for x in rules if x.get("id")==rid])==1)
body={"name":nm,"description":"edited","action":"ALLOW","enabled":True,"rule_type":"DOMAIN","domain":"upd.example.com","priority":9}
st,u=req("PUT","/api/control/rules/%s"%rid,body,t)
ck("edit 200",st==200,"%s %s"%(st,u))
ck("edit action",u.get("action")=="ALLOW","%s"%u)
body["enabled"]=False
st,d=req("PUT","/api/control/rules/%s"%rid,body,t)
ck("disable 200",st==200,"%s %s"%(st,d))
ck("disable reflected",d.get("enabled") is False,"%s"%d)
st,r2=req("GET","/api/control/rules",t=t)
f2=[x for x in r2 if x.get("id")==rid]
ck("disable persisted",len(f2)==1 and f2[0].get("enabled") is False,"%s"%f2)
body["enabled"]=True
st,e=req("PUT","/api/control/rules/%s"%rid,body,t)
ck("enable 200",st==200,"%s %s"%(st,e))
ck("enable reflected",e.get("enabled") is True,"%s"%e)
st,de=req("DELETE","/api/control/rules/%s"%rid,t=t)
ck("delete 200",st==200,"%s %s"%(st,de))
st,r3=req("GET","/api/control/rules",t=t)
ck("removed after delete",len([x for x in r3 if x.get("id")==rid])==0)
print("\nRESULT: %d passed, %d failed"%(ok,fail))
sys.exit(1 if fail else 0)