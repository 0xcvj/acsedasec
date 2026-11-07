#!/usr/bin/env python3
"""Generate a FigCraft script for the Acseda Cybersecurity landing page, run it, verify ids."""
import json, subprocess, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = "/home/jace/apps/figcraft/current/bin/figcraft-cli"

ROYAL="#1C4FB8"; SIGNAL="#2F6EE0"; NAVY="#0D1F45"; NAVY2="#16306A"; DEEP="#081430"
SUN="#F4B63F"; BG="#F3F6FB"; WHITE="#FFFFFF"; INK="#0F1A30"; MUTED="#566583"; LINE="#D8DFEC"
SOFT="#E6EDF8"; ONDARK="#C3D2F0"; ONDARK2="#93A6CC"; RED="#F0616D"; GREEN="#34D399"; LIGHTBLUE="#8FB3FF"
DISPLAY="Montserrat"; BODY="Source Sans 3"; MONO="Liberation Mono"

cmds=[]; nid=[1]; GROUPS={}
def reg(g,i): GROUPS.setdefault(g,[]).append(i); return i
FIT=[]
IMG=os.path.join(HERE,"landing-photos")+"/"
def do(command, params): cmds.append({"command":command,"params":params})
def image(parent, name, w, h, fill_w=False, radius=0):
    i=add("image.place",{"path":IMG+name,"parent":parent,"width":w,"height":h,"mode":"fill"})
    props={"name":"Photo / "+name}
    if fill_w: props["sizingH"]="fill"
    if radius: props["cornerRadius"]=radius
    do("node.set",dict(ids=[i],**props))
    return i
def add(command, params):
    cmds.append({"command":command,"params":params}); nid[0]+=1; return nid[0]

def frame(parent, name, **p):
    props=dict(p)
    params={"type":"frame","name":name,"props":props}
    if parent is not None: params["parent"]=parent
    for k in ("x","y","width","height"):
        if k in props: params[k]=props.pop(k)
    if "fill" not in props and "fills" not in props: props["fills"]=[]
    sides=("strokeTopWeight","strokeRightWeight","strokeBottomWeight","strokeLeftWeight")
    if any(k in props for k in sides):
        for k in sides: props.setdefault(k,0)
        props.pop("strokeWeight",None)
    return add("node.create",params)

def row(parent,name,gap=0,**p):  return frame(parent,name,layout="horizontal",gap=gap,sizingH=p.pop("sizingH","hug"),sizingV=p.pop("sizingV","hug"),**p)
def col(parent,name,gap=0,**p):  return frame(parent,name,layout="vertical",gap=gap,sizingH=p.pop("sizingH","hug"),sizingV=p.pop("sizingV","hug"),**p)

def text(parent, s, size=16, font=BODY, style="Regular", color=INK, fill_w=False, **p):
    props={"fontSize":size,"fontFamily":font,"fontStyle":style,"fill":color}
    props.update(p)
    if fill_w: props.update(sizingH="fill",textAutoResize="height")
    return add("text.create",{"text":s,"x":0,"y":0,"parent":parent,"props":props})

def vec(parent, path, w, h, x=0, y=0, **p):
    return add("vector.create",{"path":path,"closed":p.pop("closed",True),"parent":parent,"x":x,"y":y,"props":dict(width=w,height=h,**p)})

def ellipse(parent,x,y,w,h,color):
    return add("shape.ellipse",{"x":x,"y":y,"width":w,"height":h,"parent":parent,"props":{"fill":color}})


import re as _re
def xform(path,k,dx=0,dy=0):
    """Scale an SVG path by k and translate absolute coords by (dx,dy)."""
    toks=_re.findall(r"[A-Za-z]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?",path)
    out=[];cmd=None;buf=[]
    arity={"M":2,"L":2,"T":2,"H":1,"V":1,"C":6,"S":4,"Q":4,"A":7,"Z":0}
    def flush(c,nums):
        U=c.upper();ab=c.isupper();n=arity[U];res=[]
        for i,v in enumerate(nums):
            v=float(v);j=i%n if n else 0
            if U=="A":
                if j in (0,1,5,6): v=v*k
                if ab and j==5: v+=dx
                if ab and j==6: v+=dy
            elif U=="H": v=v*k+(dx if ab else 0)
            elif U=="V": v=v*k+(dy if ab else 0)
            else:
                v=v*k
                if ab: v+= dx if j%2==0 else dy
            res.append(f"{v:.3f}".rstrip("0").rstrip("."))
        return res
    for t in toks:
        if t.isalpha():
            if cmd: out+= [cmd]+flush(cmd,buf)
            cmd=t;buf=[]
            if t in "Zz": out.append(t);cmd=None
        else: buf.append(t)
    if cmd: out+=[cmd]+flush(cmd,buf)
    return " ".join(out)

def vecp(parent,path,**p):
    """Vector placed at its natural (already transformed) coordinates."""
    return add("vector.create",{"path":path,"closed":p.pop("closed",True),"parent":parent,"props":p})

HEAD="M7 4 15 11Q24 7 33 11L41 4 40 18Q44 24 41 32Q36 44 24 45Q12 44 7 32Q4 24 8 18Z"
def owl(parent, s, head=ROYAL, eye=WHITE, iris=SIGNAL, pupil=NAVY, beak=SUN, glint=True, name="Owl"):
    k=s/48
    f=frame(parent,name,width=s,height=s)
    # head path spans x 4..44, y 4..45
    vecp(f,xform(HEAD,k),fill=head)
    for cx in (16.5,31.5):
        ellipse(f,(cx-7.5)*k,(23-7.5)*k,15*k,15*k,eye)
        ellipse(f,(cx-4.6)*k,(23-4.6)*k,9.2*k,9.2*k,iris)
        ellipse(f,(cx-2.2)*k,(23-2.2)*k,4.4*k,4.4*k,pupil)
        if glint: ellipse(f,(cx+1.1-0.9)*k,(21.8-0.9)*k,1.8*k,1.8*k,WHITE)
    vecp(f,xform("M21.5 30 26.5 30 24 36Z",k),fill=beak)
    return f

def logo(parent, word=ROYAL, sub=NAVY, owl_kw=None, size=40):
    r=row(parent,"Logo",gap=12,crossAlign="center")
    owl(r,size,**(owl_kw or {}))
    c=col(r,"Wordmark",gap=1)
    text(c,"ACSEDA",size*0.5,DISPLAY,"ExtraBold",word,letterSpacing="6%")
    text(c,"CYBERSECURITY",size*0.235,DISPLAY,"SemiBold",sub,letterSpacing="22%")
    return r

def button(parent,label,bg=ROYAL,fg=WHITE,stroke=None,size=16,pad=(15,24),shadow=False):
    p=dict(fill=bg,cornerRadius=10,padding=[pad[0],pad[1],pad[0],pad[1]],crossAlign="center",mainAlign="center")
    if bg is None: p.pop("fill"); p["fills"]=[]
    if stroke: p.update(strokes=[stroke],strokeWeight=1.5,strokeAlign="inside")
    if shadow: p["effects"]=[{"type":"dropShadow","color":"#0D1F4540","offset":[0,10],"radius":24}]
    b=row(parent,"Button / "+label,**p)
    text(b,label,size,DISPLAY,"Bold",fg)
    return b

def eyebrow(parent,s,color=ROYAL):
    return text(parent,s.upper(),13,DISPLAY,"Bold",color,letterSpacing="14%")

def h2(parent,s,color=INK,size=44,fill_w=True):
    return text(parent,s,size,DISPLAY,"ExtraBold",color,fill_w=fill_w,lineHeight="115%")

def body(parent,s,color=MUTED,size=18,fill_w=True):
    return text(parent,s,size,BODY,"Regular",color,fill_w=fill_w,lineHeight="155%")

def check_list(parent,items,color=INK,tick=ROYAL,size=15):
    c=col(parent,"List",gap=10,sizingH="fill")
    for it in items:
        r=row(c,"Item",gap=10,sizingH="fill",crossAlign="min")
        ic=frame(r,"Tick",width=18,height=18)
        vecp(ic,"M3 9.5 7.5 14 15 4.5",closed=False,fills=[],strokes=[tick],strokeWeight=2.4,strokeCap="round",strokeJoin="round")
        text(r,it,size,BODY,"Regular",color,fill_w=True,lineHeight="140%")
    return c

ICONS={
 "eye":"M2 12C5 6.5 8.5 4 12 4s7 2.5 10 8c-3 5.5-6.5 8-10 8S5 17.5 2 12Z M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 1 0 0-7Z",
 "mail":"M3 5h18v14H3Z M3 6l9 7 9-7",
 "lock":"M5 11h14v10H5Z M8 11V8a4 4 0 0 1 8 0v3",
 "phone":"M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2Z",
 "shield":"M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5Z",
 "card":"M2 6h20v13H2Z M2 10h20",
 "clock":"M12 3a9 9 0 1 0 0 18 9 9 0 1 0 0-18Z M12 7v5l3 2",
 "pin":"M12 22s7-6.3 7-12a7 7 0 0 0-14 0c0 5.7 7 12 7 12Z M12 7.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 1 0 0-5Z",
 "bed":"M3 18V7 M3 14h18v4 M21 14v-2a3 3 0 0 0-3-3h-7v5",
 "scale":"M12 3v18 M5 21h14 M4 7h16 M4 7l-3 7a3 3 0 0 0 6 0Z M20 7l-3 7a3 3 0 0 0 6 0Z",
 "cross":"M9 3h6v6h6v6h-6v6H9v-6H3V9h6Z",
 "bank":"M3 9 12 4l9 5 M5 10v8 M9.5 10v8 M14.5 10v8 M19 10v8 M3 20h18",
 "fan":"M12 3a9 9 0 1 0 0 18 9 9 0 1 0 0-18Z M12 12c0-3 .8-5 3.5-5.5 M12 12c3 0 5 .8 5.5 3.5 M12 12c0 3-.8 5-3.5 5.5 M12 12c-3 0-5-.8-5.5-3.5",
 "truck":"M2 6h12v10H2Z M14 9h4l3 3.5V16h-7 M6.5 19.5a2 2 0 1 0 0-4 2 2 0 1 0 0 4Z M17 19.5a2 2 0 1 0 0-4 2 2 0 1 0 0 4Z",
 "helmet":"M2.5 17.5h19 M5 17.5V14a7 7 0 0 1 14 0v3.5 M10 7.2V5h4v2.2 M12 7v5",
}
def icon(parent,key,box=48,bg=ROYAL,fg=WHITE,radius=12,stroke=2):
    f=frame(parent,"Icon / "+key,width=box,height=box,fill=bg,cornerRadius=radius)
    s=box*0.5
    vecp(f,xform(ICONS[key],s/24,(box-s)/2,(box-s)/2),closed=False,fills=[],strokes=[fg],strokeWeight=stroke,strokeCap="round",strokeJoin="round")
    return f

PADX=120
def section(parent,name,bg=None,pad=(112,PADX,112,PADX),gap=48,layout="vertical",**p):
    kw=dict(layout=layout,gap=gap,padding=list(pad),sizingH="fill",sizingV="hug")
    if isinstance(bg,dict) or isinstance(bg,list): kw["fills"]=bg if isinstance(bg,list) else [bg]
    elif bg: kw["fill"]=bg
    kw.update(p)
    return frame(parent,name,**kw)

def grad(stops,frm=(0,0),to=(1,1)):
    return {"type":"linearGradient","stops":stops,"from":list(frm),"to":list(to)}

# ===================================================================== PAGE
page=frame(None,"Acseda — Landing page (desktop 1440)",x=0,y=0,width=1440,height=900,
           layout="vertical",gap=0,sizingV="hug",fill=WHITE)

# ---------- NAV
nav=section(page,"Nav",bg=WHITE,pad=(20,PADX,20,PADX),layout="horizontal",gap=24,mainAlign="spaceBetween",crossAlign="center",
            strokes=[LINE],strokeBottomWeight=1)
logo(nav)
links=row(nav,"Links",gap=36,crossAlign="center")
for l in ["Services","Packages","How it works","Who we help","About"]:
    text(links,l,15,BODY,"SemiBold",INK)
right=row(nav,"Nav actions",gap=20,crossAlign="center")
text(right,"EN  ·  NL",14,BODY,"SemiBold",MUTED,letterSpacing="4%")
button(right,"Book a free Secure Check",size=14,pad=(12,18))

# ---------- HERO
hero=section(page,"Hero",bg=grad([DEEP,NAVY,NAVY2,ROYAL],(0,0),(1,1)),pad=(96,PADX,104,PADX),layout="horizontal",gap=72,crossAlign="center")
hbg=image(hero,"server.jpg",1440,800)
do("node.set",{"ids":[hbg],"absolute":True,"x":0,"y":0,"opacity":0.55})
hov=frame(hero,"Overlay",width=1440,height=800,fills=[grad(["#081430FA","#0D1F45E6","#16306AB3","#1C4FB880"],(0,0),(1,1))])
do("node.set",{"ids":[hov],"absolute":True,"x":0,"y":0})
FIT.append((hero,[hbg,hov]))
hl=col(hero,"Hero copy",gap=28,sizingH="fill")
pill=row(hl,"Pill",gap=10,crossAlign="center",fill="#FFFFFF14",cornerRadius=999,padding=[7,16,7,12],strokes=["#FFFFFF2E"],strokeWeight=1,strokeAlign="inside")
ellipse(pill,0,0,8,8,SUN)
text(pill,"Managed cybersecurity for businesses in Aruba and the Caribbean",14,BODY,"SemiBold",ONDARK)
hh=col(hl,"Headline",gap=0,sizingH="fill")
text(hh,"Your night watch.",62,DISPLAY,"ExtraBold",WHITE,fill_w=True,lineHeight="108%")
text(hh,"Always watching.",62,DISPLAY,"ExtraBold",LIGHTBLUE,fill_w=True,lineHeight="108%")
body(hl,"Many attacks on businesses begin after closing time. Acseda monitors every laptop, inbox and password around the clock, and a local specialist contacts you as soon as something happens.",ONDARK,20)
ctas=row(hl,"CTAs",gap=14,crossAlign="center")
button(ctas,"Book a free Secure Check",bg=SUN,fg=NAVY,shadow=True)
button(ctas,"See packages",bg=None,fg=WHITE,stroke="#FFFFFF59")
proof=row(hl,"Proof",gap=40,padding=[12,0,0,0])
for big,small in [("24/7","monitoring, nights and weekends"),("30 min","callback on critical alerts"),("Local","specialist support in Aruba")]:
    c=col(proof,"Stat",gap=2)
    text(c,big,26,DISPLAY,"ExtraBold",WHITE)
    text(c,small,14,BODY,"Regular",ONDARK2)

# night console card
card=col(hero,"Night console",gap=20,width=520,sizingH="fixed",fill="#0A1636",cornerRadius=24,padding=[28,28,28,28],
         strokes=["#FFFFFF1F"],strokeWeight=1,strokeAlign="inside",
         effects=[{"type":"dropShadow","color":"#00000066","offset":[0,30],"radius":60}])
ch=row(card,"Console header",gap=12,sizingH="fill",mainAlign="spaceBetween",crossAlign="center")
cl=row(ch,"Title",gap=10,crossAlign="center")
owl(cl,26,glint=False)
text(cl,"Acseda One  ·  Night console",14,BODY,"SemiBold",ONDARK)
st=row(ch,"Status",gap=8,crossAlign="center",fill="#34D39922",cornerRadius=999,padding=[5,12,5,10])
ellipse(st,0,0,8,8,GREEN)
text(st,"Watching 42 devices",13,BODY,"SemiBold",GREEN)
ct=col(card,"Clock",gap=2)
text(ct,"03:12",48,DISPLAY,"Bold",WHITE)
text(ct,"Saturday night  ·  sample: boutique hotel, Oranjestad",14,BODY,"Regular",ONDARK2)
tl=col(card,"Timeline",gap=0,sizingH="fill")
events=[("03:12",RED,"Ransomware behaviour detected","FRONTDESK-02 started encrypting shared files"),
        ("03:12",SUN,"Device isolated automatically","Cut off from the network in 9 seconds"),
        ("03:19",LIGHTBLUE,"Acseda called the night manager","Explained what happened and what to do"),
        ("07:40",GREEN,"Clean and back online","Ready before morning check-in")]
for i,(t,c,a,b) in enumerate(events):
    r=row(tl,"Event",gap=16,sizingH="fill",padding=[14,0,14,0],crossAlign="min",
          **({"strokes":["#FFFFFF14"],"strokeTopWeight":1} if i else {}))
    text(r,t,13,MONO,"Regular",ONDARK2)
    dot=frame(r,"Dot",width=10,height=18)
    ellipse(dot,0,5,10,10,c)
    cc=col(r,"Text",gap=2,sizingH="fill")
    text(cc,a,16,BODY,"SemiBold",WHITE,fill_w=True)
    text(cc,b,14,BODY,"Regular",ONDARK2,fill_w=True)
cf=row(card,"Console footer",gap=10,sizingH="fill",fill="#FFFFFF0D",cornerRadius=12,padding=[12,14,12,14],crossAlign="center")
text(cf,"Morning report sent to the owner at 08:00. No guest data left the building.",14,BODY,"Regular",ONDARK,fill_w=True)

# ---------- TRUST STRIP
trust=section(page,"Trust strip",bg=WHITE,pad=(28,PADX,28,PADX),layout="horizontal",gap=24,mainAlign="spaceBetween",crossAlign="center",
              strokes=[LINE],strokeBottomWeight=1)
for k,t in [("shield","GDPR-grade data handling"),("card","PCI-DSS ready reports"),("clock","24/7 security operations centre"),("pin","Local support on Aruba")]:
    r=row(trust,"Trust item",gap=12,crossAlign="center")
    icon(r,k,box=36,bg=SOFT,fg=ROYAL,radius=10,stroke=2)
    text(r,t,16,BODY,"SemiBold",INK)

# ---------- WHY NOW
why=section(page,"Why now",bg=BG,layout="horizontal",gap=80,crossAlign="center")
wl=col(why,"Why copy",gap=18,sizingH="fill")
image(wl,"laptopdark.jpg",560,280,fill_w=True,radius=18)
eyebrow(wl,"Why now")
h2(wl,"Attackers don't keep office hours.")
body(wl,"Small and mid-sized businesses use the same laptops, email and booking systems as large companies, and attackers target them the same way. The difference is that most have no one monitoring their systems outside office hours.")
wr=col(why,"Why cards",gap=16,width=620,sizingH="fixed")
for tag,title,desc in [("July 2025","The region is a target","Attacks hit the Curaçao tax office, the Joint Court of Justice and email accounts of the Aruban parliament."),
                       ("After hours","Ransomware runs at night","Attackers launch when offices are empty, so the damage spreads for hours before anyone notices."),
                       ("One click","Email is still the way in","A fake booking, invoice or password reset is all it takes for one staff member to let them in.")]:
    c=row(wr,"Why card",gap=20,sizingH="fill",fill=WHITE,cornerRadius=16,padding=[22,24,22,24],strokes=[LINE],strokeWeight=1,strokeAlign="inside",crossAlign="min")
    tg=col(c,"Tag",width=110,sizingH="fixed")
    text(tg,tag,14,DISPLAY,"Bold",ROYAL)
    cc=col(c,"Body",gap=4,sizingH="fill")
    text(cc,title,18,DISPLAY,"Bold",INK,fill_w=True)
    text(cc,desc,15,BODY,"Regular",MUTED,fill_w=True,lineHeight="150%")

# ---------- SERVICES
svc=section(page,"Services",bg=WHITE)
sh=col(svc,"Services header",gap=14,width=760,sizingH="fixed")
eyebrow(sh,"What we do")
h2(sh,"One local partner. Four layers of protection.")
grid=row(svc,"Service cards",gap=20,sizingH="fill",crossAlign="min")
services=[("eye","Acseda One","24/7 monitoring & response","An agent on every device and a security operations centre watching day and night.",["Every laptop, PC and server","Threats isolated automatically","Call within 30 minutes on critical alerts"],True),
          ("mail","Acseda Aware","Phishing training","Your staff learn to spot fake emails by practising on safe ones.",["Monthly fake phishing tests","5-minute lessons for whoever clicks","Results per team"],False),
          ("lock","Acseda Browse","Passwords & safe browsing","One install that makes passwords and links safe for the whole team.",["Company password vault","Scam and malware link filter","Encrypted file sharing"],False),
          ("phone","Acseda Desk","Your local expert","A dedicated specialist who knows your environment and is reachable when it matters.",["One number to call","Incidents explained in plain language","Monthly review with the owner"],False)]
for k,name,tag,desc,items,feat in services:
    p=dict(gap=16,sizingH="fill",cornerRadius=20,padding=[28,26,30,26])
    if feat: p.update(fills=[grad([ROYAL,NAVY2],(0,0),(1,1))],effects=[{"type":"dropShadow","color":"#1C4FB840","offset":[0,20],"radius":40}])
    else: p.update(fill=WHITE,strokes=[LINE],strokeWeight=1,strokeAlign="inside")
    c=reg("svc",col(grid,"Service / "+name,**p))
    icon(c,k,bg=(WHITE if feat else ROYAL),fg=(ROYAL if feat else WHITE))
    cc=col(c,"Title",gap=4,sizingH="fill")
    text(cc,name,22,DISPLAY,"Bold",WHITE if feat else INK,fill_w=True)
    text(cc,tag,14,DISPLAY,"SemiBold",SUN if feat else ROYAL,fill_w=True)
    text(c,desc,15,BODY,"Regular",ONDARK if feat else MUTED,fill_w=True,lineHeight="150%")
    check_list(c,items,color=WHITE if feat else INK,tick=SUN if feat else ROYAL,size=14)

# ---------- DESK SPLIT
dsec=section(page,"Desk feature",bg=WHITE,pad=(0,PADX,112,PADX))
dcard=row(dsec,"Desk card",gap=0,sizingH="fill",fill=NAVY,cornerRadius=28,clip=True,crossAlign="center")
image(dcard,"encrypt.jpg",600,480)
dr=col(dcard,"Desk copy",gap=20,sizingH="fill",padding=[48,56,48,56])
eyebrow(dr,"Acseda Desk",SUN)
h2(dr,"A dedicated local specialist, not a ticket queue.",WHITE,36)
body(dr,"When an incident occurs, you speak with a specialist who knows your business, your systems and your team. We explain what happened in clear language and set out the next steps.",ONDARK,17)
check_list(dr,["One number for questions and incidents","Monthly review with the owner, in person or by video","Help in English and Dutch"],color=WHITE,tick=SUN)
button(dr,"Contact us",bg=SUN,fg=NAVY)

# ---------- HOW IT WORKS
how=section(page,"How it works",bg=BG)
hh2=col(how,"How header",gap=14,width=760,sizingH="fixed")
eyebrow(hh2,"How it works")
h2(hh2,"From first call to fully watched in about three weeks.")
steps=row(how,"Steps",gap=20,sizingH="fill",crossAlign="min")
for i,(t,d,w) in enumerate([("Free Secure Check","We assess your devices, accounts and email setup, and present the risks in one meeting.","Week 1  ·  free"),
                            ("Clear proposal","One fixed monthly price based on your users and devices. No setup fees.","Within 2 days"),
                            ("Setup on site","We install the agents, roll out the vault and filter, and brief your staff.","Week 2–3"),
                            ("Live and watched","Monitoring is active. You receive a direct contact number and your first report after one month.","From day one")],1):
    c=reg("steps",col(steps,"Step",gap=14,sizingH="fill",fill=WHITE,cornerRadius=18,padding=[26,24,26,24],strokes=[LINE],strokeWeight=1,strokeAlign="inside"))
    n=row(c,"Number",width=40,height=40,sizingH="fixed",sizingV="fixed",fill=ROYAL,cornerRadius=999,mainAlign="center",crossAlign="center")
    text(n,str(i),17,DISPLAY,"Bold",WHITE)
    text(c,t,19,DISPLAY,"Bold",INK,fill_w=True)
    text(c,d,15,BODY,"Regular",MUTED,fill_w=True,lineHeight="150%")
    tg=row(c,"When",fill=SOFT,cornerRadius=6,padding=[4,10,4,10])
    text(tg,w,13,BODY,"SemiBold",ROYAL)

# ---------- THE ACSEDA STACK (from the service-stack design)
def tbox(parent,s,x,y,w,size=14,font=BODY,style="Regular",color=INK,align="left",**p):
    props={"fontSize":size,"fontFamily":font,"fontStyle":style,"fill":color,"textAlign":align,"textAutoResize":"height"}
    props.update(p)
    return add("text.create",{"text":s,"x":x,"y":y,"width":w,"parent":parent,"props":props})

stk=section(page,"The Acseda stack",bg=BG,layout="horizontal",gap=72,crossAlign="center")
D=frame(stk,"Stack diagram",width=580,height=800)
X0=10
# hero panel
hp=frame(D,"Acseda One panel",x=X0,y=64,width=560,height=376,cornerRadius=[28,28,0,0],
         fills=[grad([SIGNAL,ROYAL,NAVY2],(0,0),(1,1))],clip=True)
ellipse(hp,380,250,260,260,"#FFFFFF0A")
items=["24/7 monitoring, nights and weekends","Infected devices isolated automatically","Local escalation call when it matters","Incidents explained in clear language","Monthly report for owner, insurer, brand"]
lst=col(hp,"Checklist",gap=10,width=300,sizingH="fixed",x=24,y=176)
for it in items:
    r=row(lst,"Item",gap=10,sizingH="fill",crossAlign="min")
    ic=frame(r,"Tick",width=16,height=16)
    vecp(ic,xform("M3 8.5 6.5 12 13 4.5",1),closed=False,fills=[],strokes=[SUN],strokeWeight=2.2,strokeCap="round",strokeJoin="round")
    text(r,it,14,BODY,"Regular",WHITE,fill_w=True,lineHeight="140%")
# shield tab
sh_=frame(D,"Shield",x=X0+24,y=0,width=200,height=212)
vecp(sh_,"M0 0 200 0 200 152 100 212 0 152Z",fill=WHITE,effects=[{"type":"dropShadow","color":"#081E2D2E","offset":[0,6],"radius":14}])
o=owl(sh_,46); do("node.set",{"ids":[o],"x":77,"y":18})
tbox(sh_,"Acseda One",0,70,200,26,DISPLAY,"ExtraBold",INK,"center")
tbox(sh_,"Managed SOC\n24/7 off-hours alarm",20,104,160,12.5,BODY,"Regular",MUTED,"center",lineHeight="135%")
# side pills
for i,(nm,sub) in enumerate([("Acseda Aware","Phishing training & simulations"),("Acseda Browse","Vault · link scan · safe transfer"),("Secure Check","Free GDPR-grade risk assessment")]):
    pl=row(D,"Pill / "+nm,gap=12,crossAlign="center",fill=WHITE,cornerRadius=999,padding=[10,18,10,10],width=256,sizingH="fixed",
           x=580-256,y=84+i*66,effects=[{"type":"dropShadow","color":"#081E2D29","offset":[0,6],"radius":16}])
    lk=row(pl,"Link",width=30,height=30,sizingH="fixed",sizingV="fixed",fill=NAVY,cornerRadius=999,mainAlign="center",crossAlign="center")
    lf=frame(lk,"Arrows",width=14,height=14)
    vecp(lf,xform("M2 6h10l-3-3M14 10H4l3 3",14/16),closed=False,fills=[],strokes=[WHITE],strokeWeight=1.8,strokeCap="round",strokeJoin="round")
    tc=col(pl,"Text",gap=0,sizingH="fill")
    text(tc,nm,15,DISPLAY,"Bold",INK)
    text(tc,sub,12,BODY,"Regular",MUTED)
# desk layer
dl=frame(D,"Acseda Desk layer",x=0,y=412,width=580,height=66,fill=NAVY,cornerRadius=16)
tbox(dl,"ACSEDA DESK",0,9,580,15,DISPLAY,"Bold",WHITE,"center",letterSpacing="8%")
tbox(dl,"Local point of contact · English and Dutch",0,29,580,12,BODY,"Regular",ONDARK2,"center")
hub=frame(D,"Hub",x=290-17,y=480-17,width=34,height=34,fill=WHITE,cornerRadius=999,effects=[{"type":"dropShadow","color":"#00000033","offset":[0,2],"radius":6}])
vecp(hub,xform("M3 6a5 5 0 0 1 9-2l1 1M13 10a5 5 0 0 1-9 2l-1-1M13 2v3h-3M3 14v-3h3",1,9,9),closed=False,fills=[],strokes=[NAVY],strokeWeight=1.6,strokeCap="round",strokeJoin="round")
# split layer
sp=frame(D,"Platform layer",x=0,y=482,width=580,height=88,fill=NAVY2,cornerRadius=[0,0,22,22])
frame(sp,"Divider",x=289,y=0,width=3,height=88,fill=ROYAL)
tbox(sp,"DETECTION PLATFORM",0,28,290,14,DISPLAY,"Bold",WHITE,"center",letterSpacing="6%")
tbox(sp,"Partner MDR · EDR, XDR",0,50,290,12,BODY,"Regular",ONDARK2,"center")
tbox(sp,"COMPLIANCE LAYER",290,28,290,14,DISPLAY,"Bold",WHITE,"center",letterSpacing="6%")
tbox(sp,"GDPR-grade · PCI-DSS · EU guests",290,50,290,12,BODY,"Regular",ONDARK2,"center")
# sensors
cw=(548-20)/3
for i,(b,s2) in enumerate([("Agent","On every laptop, PC, server"),("Inbox","Phishing tests & report button"),("Extension","In the staff browser")]):
    x=16+i*(cw+10)
    sc=frame(D,"Sensor / "+b,x=x,y=554,width=cw,height=72,fill=WHITE,cornerRadius=10,effects=[{"type":"dropShadow","color":"#081E2D1F","offset":[0,4],"radius":12}])
    tbox(sc,b,0,12,cw,17,DISPLAY,"Bold",INK,"center")
    tbox(sc,s2,8,36,cw-16,11.5,BODY,"Regular",MUTED,"center")
    ar=frame(D,"Arrow",x=x+cw/2-13,y=554+72-13,width=26,height=26,fill=NAVY,cornerRadius=999)
    vecp(ar,xform("M4 1v10M4 11 2 9M8 11V1M8 1l2 2",1,7,7),closed=False,fills=[],strokes=[WHITE],strokeWeight=1.4,strokeCap="round",strokeJoin="round")
# surfaces
SURF=[("Devices","M3 5h17v11H3Z M1 20h21"),("Staff","M13 4.5a4.5 4.5 0 1 0 0 9 4.5 4.5 0 1 0 0-9Z M4.5 22c1-4.5 4.4-7 8.5-7s7.5 2.5 8.5 7"),
      ("Email","M3 6h20v14H3Z M4 8l9 6.5L22 8"),("Passwords","M7 11h12v10H7Z M9.5 11V8a3.5 3.5 0 0 1 7 0v3"),("Payments","M3 7h20v13H3Z M3 11h20 M7 16h5")]
sw=580/5
for i,(lab,pth) in enumerate(SURF):
    cx=i*sw+sw/2
    ci=frame(D,"Surface / "+lab,x=cx-29,y=664,width=58,height=58,fill=WHITE,cornerRadius=999,effects=[{"type":"dropShadow","color":"#081E2D1A","offset":[0,3],"radius":10}])
    vecp(ci,xform(pth,1,16,16),closed=False,fills=[],strokes=[ROYAL],strokeWeight=1.8,strokeCap="round",strokeJoin="round")
    tbox(D,lab,cx-50,728,100,12,DISPLAY,"SemiBold",INK,"center")
tbox(D,"YOUR NIGHT WATCH. ALWAYS WATCHING.",0,770,580,12,DISPLAY,"SemiBold",MUTED,"center",letterSpacing="14%")

# legend
lg=col(stk,"Stack legend",gap=18,sizingH="fill")
eyebrow(lg,"How it fits together")
h2(lg,"Every layer, top to bottom.",INK,40)
body(lg,"You choose what sits at the top. Everything underneath is enterprise-grade technology from our security partners, with Acseda as the local layer that owns the relationship.",MUTED,17)
rows=col(lg,"Rows",gap=0,sizingH="fill",strokes=[LINE],strokeTopWeight=1)
for dt,dd in [("Acseda One","24/7 monitoring and response. An alarm system for the hours nobody is in the office."),
              ("Acseda Aware","Monthly simulated phishing, with short training for whoever clicks."),
              ("Acseda Browse","Password vault, link filter and secure file transfer in one install."),
              ("Secure Check","The free assessment that starts every engagement: devices, accounts and a prioritised fix list."),
              ("Acseda Desk","Escalations, incident explanations and the monthly review, handled locally."),
              ("Platform layers","Partner detection technology, and compliance reporting for GDPR-grade, PCI-DSS and EU-guest requirements.")]:
    r=row(rows,"Row",gap=20,sizingH="fill",padding=[14,0,14,0],strokes=[LINE],strokeBottomWeight=1,crossAlign="min")
    t=col(r,"Term",width=150,sizingH="fixed"); text(t,dt,15,DISPLAY,"Bold",INK)
    text(r,dd,15,BODY,"Regular",INK,fill_w=True,lineHeight="150%")

# ---------- PACKAGES (from the packages design)
pk=section(page,"Packages",bg=grad([DEEP,NAVY],(0,0),(0,1)))
ph=col(pk,"Packages header",gap=14,width=820,sizingH="fixed")
eyebrow(ph,"Packages",SUN)
h2(ph,"Two ways to work with Acseda.",WHITE)
body(ph,"Essentials protects your people: their inbox, their passwords and the links they click. One adds a team that watches every device day and night, and a local specialist who calls you when something happens. No setup fees; the Secure Check is always free.",ONDARK)
cards=row(pk,"Package cards",gap=24,sizingH="fill",crossAlign="min")

def layer(parent,title,sub,kind):
    p=dict(gap=2,sizingH="fill",padding=[12,14,12,14],crossAlign="center",cornerRadius=12)
    if kind=="watch": p.update(fills=[grad([SIGNAL,ROYAL,NAVY2],(0,0),(1,1))],cornerRadius=[16,16,6,6],padding=[16,14,16,14]); tc,sc=WHITE,ONDARK
    elif kind=="off": p.update(fill=SOFT,strokes=[ "#B9C5DA"],strokeWeight=1.2,strokeAlign="inside",dashes=[5,4]); tc,sc=MUTED,MUTED
    else: p.update(fill=NAVY); tc,sc=WHITE,ONDARK2
    l=col(parent,"Layer / "+title,**p)
    text(l,title.upper(),12.5,DISPLAY,"Bold",tc,letterSpacing="8%",textAlign="center")
    text(l,sub,12,BODY,"Regular",sc,textAlign="center")
    return l

def chips(parent,on,off):
    r=row(parent,"Protects",gap=6,sizingH="fill",wrap=True,mainAlign="center",padding=[4,0,0,0])
    for c in on:
        ch=row(r,"Chip",fill=WHITE,cornerRadius=999,padding=[5,11,5,11],strokes=[LINE],strokeWeight=1,strokeAlign="inside")
        text(ch,c,12,BODY,"SemiBold",INK)
    for c in off:
        ch=row(r,"Chip off",cornerRadius=999,padding=[5,11,5,11],strokes=[LINE],strokeWeight=1,strokeAlign="inside")
        text(ch,c,12,BODY,"Regular",MUTED,textDecoration="strikethrough")

def svc_tiles(parent,a,b):
    r=row(parent,"Services",gap=6,sizingH="fill")
    for nm,sub in (a,b):
        t=col(r,"Tile",gap=1,sizingH="fill",fill=SOFT,cornerRadius=10,padding=[9,8,9,8],crossAlign="center")
        text(t,nm,13,DISPLAY,"Bold",INK,textAlign="center")
        text(t,sub,11.5,BODY,"Regular",MUTED,textAlign="center")

def pkg2(name,badge,feat,desc,price_parts,mini,incl_head,incl,excluded=None):
    p=dict(gap=0,sizingH="fill",cornerRadius=22,fill=WHITE,clip=True)
    if feat: p.update(strokes=[ROYAL],strokeWeight=3,strokeAlign="inside",effects=[{"type":"dropShadow","color":"#00000055","offset":[0,24],"radius":48}])
    c=reg("pkg",col(cards,"Package / "+name,**p))
    hd=col(c,"Head",gap=8,sizingH="fill",padding=[26,26,18,26])
    t=row(hd,"Top",sizingH="fill",mainAlign="spaceBetween",crossAlign="center")
    text(t,name,24,DISPLAY,"ExtraBold",INK)
    b=row(t,"Badge",fill=SUN if feat else SOFT,cornerRadius=5,padding=[4,8,4,8])
    text(b,badge.upper(),10.5,DISPLAY,"Bold","#3A2700" if feat else MUTED,letterSpacing="8%")
    text(hd,desc,14,BODY,"Regular",MUTED,fill_w=True)
    pr=row(hd,"Price",gap=12,crossAlign="baseline",wrap=True,padding=[6,0,0,0])
    text(pr,price_parts[0],32,DISPLAY,"ExtraBold",ROYAL)
    for x in price_parts[1:]: text(pr,x,13,BODY,"Regular",MUTED)
    mn=col(c,"Mini stack",gap=6,sizingH="fill",padding=[0,20,22,20])
    mini(mn)
    inc=col(c,"Included",gap=12,sizingH="fill",padding=[18,26,26,26],strokes=[LINE],strokeTopWeight=1)
    text(inc,incl_head,14,DISPLAY,"Bold",INK,letterSpacing="3%")
    check_list(inc,incl,color=INK,tick=ROYAL,size=14)
    if excluded:
        r=row(inc,"Excluded",gap=10,sizingH="fill")
        mi=frame(r,"Minus",width=18,height=18)
        vecp(mi,"M4 9h10",closed=False,fills=[],strokes=[MUTED],strokeWeight=2.2,strokeCap="round")
        text(r,excluded,14,BODY,"Regular",MUTED,fill_w=True,lineHeight="140%")
    bt=button(inc,"Book a free Secure Check" if feat else "Start with Essentials",**(dict(bg=SUN,fg=NAVY,shadow=True) if feat else dict(bg=None,fg=ROYAL,stroke=ROYAL)))

def mini_ess(m):
    layer(m,"No 24/7 monitoring","Devices are not watched at night. Upgrade to One for that.","off")
    layer(m,"Acseda Desk · office hours","Questions by email or phone · additional support $100/h","desk")
    svc_tiles(m,("Acseda Aware","Phishing tests & training"),("Acseda Browse","Vault · link filter · transfer"))
    chips(m,["Staff","Email","Passwords","Web"],["Devices","Servers"])
def mini_one(m):
    layer(m,"24/7 monitoring & response","Watched every night and weekend · infected devices cut off automatically","watch")
    layer(m,"Acseda Desk · 2 hours included","Local contact · night escalation call · monthly report","desk")
    pl=row(m,"Platform",gap=0,sizingH="fill",fill=NAVY2,cornerRadius=12,clip=True)
    for i,(a,b) in enumerate([("DETECTION","Partner MDR · EDR"),("COMPLIANCE","GDPR-grade · PCI-DSS")]):
        cc=col(pl,"Half",gap=1,sizingH="fill",padding=[11,8,11,8],crossAlign="center",**({"strokes":[ROYAL],"strokeLeftWeight":2} if i else {}))
        text(cc,a,12.5,DISPLAY,"Bold",WHITE,letterSpacing="8%")
        text(cc,b,12,BODY,"Regular",ONDARK2)
    svc_tiles(m,("Acseda Aware","Included"),("Acseda Browse","Included"))
    chips(m,["Devices","Servers","Staff","Email","Passwords","Web"],[])

pkg2("Acseda Essentials","Entry",False,"For small offices that want to start with staff training and safe passwords.",
     ["$15","per user / month","+ $99 base fee per month"],mini_ess,"WHAT'S INCLUDED",
     ["Free Secure Check before you sign","Monthly phishing simulation for every user","Short training modules in English, Dutch or Spanish","Company password vault with shared team vaults","Link and website filter for scam and malware sites","Encrypted file and password sharing","Quarterly report"],
     "No device monitoring, no night response, no included Desk hours")
pkg2("Acseda One","Recommended",True,"For hotels, clinics and offices that cannot afford a night of downtime.",
     ["$32","per user / month","+ $299 base fee  ·  + $60 per server"],mini_one,"EVERYTHING IN ESSENTIALS, PLUS",
     ["Security agent on every laptop, PC and server","24/7 security analysts, threats contained automatically","Phone call within 30 minutes of a critical incident","Every incident explained in clear language","2 Desk hours a month for questions and small fixes","Monthly report for owner, insurer and brand","Yearly re-run of the Secure Check"])

# example quotes
qh=col(pk,"Quotes header",gap=6,sizingH="fill",padding=[16,0,0,0])
text(qh,"Example monthly quotes",22,DISPLAY,"Bold",WHITE)
text(qh,"Prices in USD per month, excluding local tax. A user is one staff member with their own account and device.",15,BODY,"Regular",ONDARK2,fill_w=True)
qs=row(pk,"Quotes",gap=16,sizingH="fill",crossAlign="min")
for nm,pkgn,lines,total in [("Law office","Essentials",[("Base fee","$99"),("8 users × $15","$120")],"$219"),
                            ("Dental clinic","One",[("Base fee","$299"),("10 users × $32","$320"),("1 server × $60","$60")],"$679"),
                            ("Boutique hotel","One",[("Base fee","$299"),("20 users × $32","$640"),("2 servers × $60","$120")],"$1,059"),
                            ("Resort","One",[("Base fee","$299"),("45 users × $32","$1,440"),("4 servers × $60","$240")],"$1,979")]:
    q=reg("quote",col(qs,"Quote / "+nm,gap=10,sizingH="fill",fill="#FFFFFF0F",cornerRadius=14,padding=[18,18,18,18],strokes=["#FFFFFF1F"],strokeWeight=1,strokeAlign="inside"))
    h=row(q,"Head",sizingH="fill",mainAlign="spaceBetween",crossAlign="baseline")
    text(h,nm,15,DISPLAY,"Bold",WHITE); text(h,pkgn,13,BODY,"Regular",ONDARK2)
    for a,b in lines:
        r=row(q,"Line",sizingH="fill",mainAlign="spaceBetween")
        text(r,a,13.5,BODY,"Regular",ONDARK2); text(r,b,13.5,BODY,"Regular",WHITE,features={"tnum":True})
    tt=row(q,"Total",sizingH="fill",mainAlign="spaceBetween",crossAlign="baseline",padding=[8,0,0,0],strokes=["#FFFFFF26"],strokeTopWeight=1)
    text(tt,"per month",12.5,BODY,"Regular",ONDARK2); text(tt,total,22,DISPLAY,"ExtraBold",SUN)


# ---------- WHO WE HELP
who=section(page,"Who we help",bg=WHITE)
wh=col(who,"Who header",gap=14,width=820,sizingH="fixed")
eyebrow(wh,"Who we help")
h2(wh,"Built for organisations that depend on their systems.")
wgrid=col(who,"Sectors",gap=40,sizingH="fill")
PHOTOS={"bed":"curacao.jpg","scale":"handshake.jpg","cross":"clinic4.jpg","bank":"meeting.jpg",
        "fan":"hvac.jpg","truck":"distribution.jpg","helmet":"construction.jpg"}
SECTORS=[("bed","Hotels & resorts","Guest data, card payments and brand security requirements, monitored around the clock."),
         ("scale","Law & notary offices","Client files and confidential email protected from phishing and data leaks."),
         ("cross","Clinics & dentists","Patient records kept secure, with systems that stay available during opening hours."),
         ("bank","Finance & insurance","Reporting that answers the questions banks, partners and regulators ask."),
         ("fan","HVAC & technical services","Customer records, service schedules and field-team laptops and phones protected."),
         ("truck","Distribution & logistics","Ordering, inventory and supplier systems kept running, with payment fraud stopped at the inbox."),
         ("helmet","Construction","Project files, tenders and site laptops secured, including fake supplier invoices.")]
for r0 in (0,4):
    wg=row(wgrid,"Sector row",gap=20,sizingH="fill",crossAlign="min")
    for k,t,d in SECTORS[r0:r0+4]:
        c=reg("sector",col(wg,"Sector",gap=14,sizingH="fill",padding=[0,4,0,0]))
        image(c,PHOTOS[k],280,190,fill_w=True,radius=16)
        icon(c,k,box=40,bg=SOFT,fg=ROYAL,radius=10)
        text(c,t,19,DISPLAY,"Bold",INK,fill_w=True)
        text(c,d,15,BODY,"Regular",MUTED,fill_w=True,lineHeight="150%")
    if r0==4:
        c=reg("sector",col(wg,"Sector / Your industry",gap=14,sizingH="fill",fill=NAVY,cornerRadius=16,padding=[28,26,28,26],mainAlign="max"))
        icon(c,"shield",box=40,bg=ROYAL,fg=WHITE,radius=10)
        text(c,"Your industry",19,DISPLAY,"Bold",WHITE,fill_w=True)
        text(c,"Not listed? Every Secure Check starts from your own systems and risks, whatever your sector.",15,BODY,"Regular",ONDARK,fill_w=True,lineHeight="150%")
        text(c,"Book a free Secure Check  →",15,DISPLAY,"Bold",SUN)

# ---------- CTA BAND
cta=section(page,"CTA band",bg=WHITE,pad=(0,PADX,112,PADX))
band=row(cta,"Band",gap=48,sizingH="fill",cornerRadius=28,padding=[56,64,56,64],crossAlign="center",
         fills=[grad([SIGNAL,ROYAL,NAVY2],(0,0),(1,1))])
bl=col(band,"Band copy",gap=18,sizingH="fill")
text(bl,"Know where you stand. Start with a free Secure Check.",40,DISPLAY,"ExtraBold",WHITE,fill_w=True,lineHeight="115%")
body(bl,"A Secure Check takes about an hour of your time. You receive a clear overview of your risks and priorities, with no obligation to sign up.",ONDARK,18)
bb=row(bl,"Band CTAs",gap=14,crossAlign="center")
button(bb,"Book a free Secure Check",bg=SUN,fg=NAVY,shadow=True)
text(bb,"or call us to schedule an appointment",15,BODY,"Regular",ONDARK)
owl(band,180,head=WHITE,eye=ROYAL,iris=WHITE,pupil=NAVY,name="Owl large")

# ---------- FOOTER
ft=section(page,"Footer",bg=DEEP,pad=(64,PADX,40,PADX),gap=48)
top=row(ft,"Footer top",gap=48,sizingH="fill",crossAlign="min")
fl=col(top,"Brand",gap=16,sizingH="fill")
logo(fl,word=WHITE,sub=ONDARK2,owl_kw=dict(head=WHITE,eye=ROYAL,iris=WHITE,pupil=NAVY),size=44)
text(fl,"Your night watch. Always watching.",16,BODY,"SemiBold",ONDARK)
for title,items in [("Services",["Acseda One","Acseda Aware","Acseda Browse","Acseda Desk"]),
                    ("Company",["How it works","Packages","Who we help","About"]),
                    ("Contact",["hello@acsedasec.com","+297 000 0000","Oranjestad, Aruba"])]:
    c=col(top,title,gap=12,width=200,sizingH="fixed")
    text(c,title.upper(),12,DISPLAY,"Bold",ONDARK2,letterSpacing="14%")
    for it in items: text(c,it,15,BODY,"Regular",ONDARK)
bot=row(ft,"Footer bottom",sizingH="fill",mainAlign="spaceBetween",padding=[20,0,0,0],strokes=["#FFFFFF1A"],strokeTopWeight=1)
text(bot,"© 2026 Acseda Cybersecurity",13,BODY,"Regular",ONDARK2)
text(bot,"Privacy  ·  Terms  ·  Responsible disclosure",13,BODY,"Regular",ONDARK2)

# ===================================================================== RUN
script=os.path.join(HERE,"landing.json"); out=os.path.join(HERE,"acseda-landing.figcraft")
json.dump(cmds,open(script,"w"),indent=0)
res=subprocess.run([CLI,"--no-system-fonts","run",script,"--out",out],capture_output=True,text=True)
lines=[l for l in res.stdout.splitlines() if l.startswith("{")]
bad=0; expect=1
for i,l in enumerate(lines):
    j=json.loads(l)
    if not j.get("ok"): print("FAIL",i,cmds[i]["command"],j.get("error"),json.dumps(cmds[i]["params"])[:300]); bad+=1; break
    rid=(j.get("result") or {}).get("id")
    if rid is not None: expect+=1
    if rid is not None and rid!=expect: print("ID MISMATCH at",i,rid,expect); bad+=1; break
print(res.stdout.splitlines()[-1] if res.stdout else "", res.stderr[-500:])
print("steps",len(cmds),"ok" if not bad else "errors")

# ---- equalise card heights per row
def runlines(cmdlist,extra):
    f=os.path.join(HERE,"tmp_step.json"); json.dump(cmdlist,open(f,"w"))
    r=subprocess.run([CLI,"--no-system-fonts","run",f]+extra,capture_output=True,text=True)
    return [json.loads(l) for l in r.stdout.splitlines() if l.startswith("{")], r
ids=[i for g in GROUPS.values() for i in g]+[c for c,_ in FIT]
res,_=runlines([{"command":"node.get","params":{"id":i}} for i in ids],["--in",out])
h={i:(r["result"].get("height") or r["result"].get("props",{}).get("height")) for i,r in zip(ids,res)}
print("heights",h)
sets=[]
for g,members in GROUPS.items():
    m=max(h[i] for i in members)
    for i in members: sets.append({"command":"node.set","params":{"ids":[i],"sizingV":"fixed","height":m}})
for c,members in FIT:
    for i in members: sets.append({"command":"node.set","params":{"ids":[i],"height":h[c],"width":1440}})
res,r=runlines(sets,["--in",out,"--out",out])
print("equalised", all(x.get("ok") for x in res), r.stderr[-300:])
