"""Generate Tikriva's angular, consumer-crypto product artwork."""
from __future__ import annotations
import hashlib, shutil
from html import escape
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BG="#10120f"; PANEL="#191c18"; PANEL_2="#252923"; AMBER="#d8fa63"; MINT="#75d8a8"; PINK="#ff7887"; TEXT="#f1f3ed"; MUTED="#a0a79b"; LINE="#30362e"
def font(kind):
    names={"sans":"arial.ttf","bold":"arialbd.ttf","mono":"consola.ttf"}; fallbacks={"sans":"DejaVuSans.ttf","bold":"DejaVuSans-Bold.ttf","mono":"DejaVuSansMono.ttf"}; p=Path("C:/Windows/Fonts")/names[kind]; return str(p if p.exists() else Path("/usr/share/fonts/truetype/dejavu")/fallbacks[kind])
class Scene:
    def __init__(self,w,h,title,desc,bg=BG):
        self.w,self.h,self.k=w,h,2; self.im=Image.new("RGB",(w*2,h*2),bg); self.d=ImageDraw.Draw(self.im); self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">',f'<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>',f'<rect width="{w}" height="{h}" fill="{bg}"/>']
    def rect(self,x,y,w,h,fill=PANEL,stroke=LINE,sw=1,r=8):
        r=min(r,6)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'); self.d.rounded_rectangle((x*2,y*2,(x+w)*2,(y+h)*2),radius=r*2,fill=fill,outline=stroke,width=max(1,round(sw*2)))
    def poly(self,pts,fill,stroke=None,sw=1):
        self.svg.append(f'<polygon points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="{sw}"/>'); self.d.polygon([(x*2,y*2) for x,y in pts],fill=fill,outline=stroke)
    def line(self,pts,color=LINE,sw=2):
        self.svg.append(f'<polyline points="{" ".join(f"{x},{y}" for x,y in pts)}" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>'); self.d.line([(x*2,y*2) for x,y in pts],fill=color,width=max(1,round(sw*2)),joint="curve")
    def text(self,x,y,s,size=24,color=TEXT,kind="sans",align="left"):
        anchor={"left":"start","center":"middle","right":"end"}[align]; self.svg.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{700 if kind=="bold" else 400}" text-anchor="{anchor}">{escape(s)}</text>'); self.d.text((x*2,y*2),s,fill=color,font=ImageFont.truetype(font(kind),round(size*2)),anchor={"left":"ls","center":"ms","right":"rs"}[align])
    def mark(self,cx,cy,size,bg=PANEL_2):
        """Angular faceted T/K monogram; no rings, orbits or pulses."""
        q=size*.5; self.poly([(cx-q*.84,cy-q*.84),(cx+q*.84,cy-q*.84),(cx+q*.84,cy-q*.58),(cx+q*.16,cy-q*.58),(cx+q*.16,cy+q*.84),(cx-q*.16,cy+q*.84),(cx-q*.16,cy-q*.58),(cx-q*.84,cy-q*.58)],bg,LINE,2); self.poly([(cx-q*.52,cy-q*.35),(cx+q*.60,cy-q*.35),(cx+q*.60,cy-q*.10),(cx+q*.08,cy-q*.10),(cx+q*.56,cy+q*.54),(cx+q*.25,cy+q*.54),(cx-q*.08,cy+q*.08),(cx-q*.40,cy+q*.54),(cx-q*.70,cy+q*.54),(cx-q*.18,cy-q*.10),(cx-q*.52,cy-q*.10)],MINT); self.poly([(cx+q*.60,cy-q*.35),(cx+q*.78,cy-q*.15),(cx+q*.22,cy+q*.62),(cx+q*.04,cy+q*.45)],AMBER); self.poly([(cx-q*.08,cy+q*.08),(cx+q*.08,cy+q*.08),(cx+q*.42,cy+q*.50),(cx+q*.25,cy+q*.54)],PINK)
    def save(self,path,vector=False):
        path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
        if vector: path.with_suffix(".svg").write_text("\n".join(self.svg+["</svg>"])+'\n',encoding="utf-8")
        if path.suffix==".svg": return
        out=self.im.resize((self.w,self.h),Image.Resampling.LANCZOS)
        if path.suffix==".webp": out.save(path,quality=95,method=6)
        elif path.suffix==".jpg": out.save(path,quality=95,subsampling=0,optimize=True)
        else: out.save(path,optimize=True)
def header(s,label,right="SOLANA / PREVIEW"):
    s.rect(48,35,52,52,AMBER,AMBER,1,6); s.mark(74,61,39,BG); s.text(120,61,"TIKRIVA",22,TEXT,"bold"); s.text(120,84,label,12,MUTED,"mono"); s.text(s.w-56,61,right,12,AMBER,"mono","right"); s.line([(48,108),(s.w-48,108)],LINE,1)
def hero():
    s=Scene(2000,1119,"Tikriva market terminal","Angular Tikriva Solana market terminal visual with watchlist, payoff and journal surfaces."); header(s,"MARKETS / BOARD","TKVA / SOLANA"); s.text(86,258,"READ THE",76,TEXT,"bold"); s.text(86,344,"MOVE.",92,AMBER,"bold"); s.text(90,406,"Build with intent.",42,MINT,"bold"); s.text(92,454,"A consumer crypto workspace for assumptions you can inspect.",22,MUTED); s.rect(88,522,520,280,PANEL,LINE,1,12); s.text(118,562,"TKVA / WATCHLIST SAMPLE",14,MUTED,"mono"); s.text(118,635,"$1.00",62,TEXT,"bold"); s.text(550,635,"+5.8%",24,MINT,"mono","right"); s.line([(118,678),(556,678)],LINE,1); s.text(118,723,"REFERENCE / USER ENTERED",13,MUTED,"mono"); s.text(118,764,"PREVIEW ONLY",13,PINK,"mono"); s.rect(760,205,1090,680,PANEL,LINE,1,14); s.text(804,258,"MARKET BOARD",16,MINT,"mono"); s.text(1810,258,"NO LIVE FEED",15,PINK,"mono","right")
    for t,x in [("ASSET",804),("REFERENCE",1205),("MOVE",1470),("STATE",1736)]: s.text(x,310,t,13,MUTED,"mono")
    for i,(a,p,m,state) in enumerate([("SOL","$250.00","+8.4%","WATCH"),("JUP","$0.92","-2.1%","REVIEW"),("TKVA","$1.00","+5.8%","LOCAL")]):
        y=365+i*132; s.line([(804,y-30),(1808,y-30)],LINE,1); s.poly([(804,y-4),(820,y-20),(836,y-4),(820,y+12)],[MINT,AMBER,PINK][i]); s.text(856,y,a,24,TEXT,"bold"); s.text(1205,y,p,22,TEXT,"mono"); s.text(1470,y,m,21,[MINT,PINK,AMBER][i],"mono"); s.text(1736,y,state,13,[MINT,AMBER,PINK][i],"mono")
    s.text(804,804,"WATCHLIST     PAYOFF MAP     JOURNAL",14,AMBER,"mono"); return s
def token():
    s=Scene(1800,1209,"Tikriva TKVA market card","Angular Tikriva TKVA card for a Solana consumer crypto workspace."); header(s,"ASSET / TKVA","SOLANA / CONTEXT"); s.rect(94,158,1612,890,PANEL,LINE,1,14); s.mark(900,426,440,PANEL_2); s.text(140,250,"TKVA",31,AMBER,"bold"); s.text(140,289,"Tikriva market unit",19,MUTED); s.text(140,414,"REFERENCE",13,MUTED,"mono"); s.text(140,472,"$1.00",54,TEXT,"bold"); s.text(140,520,"+5.8% illustrative move",17,MINT,"mono"); s.poly([(1294,252),(1578,252),(1578,524),(1294,524)],BG,LINE,1); s.text(1330,306,"SCENARIO",13,MUTED,"mono"); s.line([(1332,455),(1392,417),(1455,438),(1510,359),(1562,384)],AMBER,5); s.text(1330,490,"USER PRICED",13,AMBER,"mono");
    for x,t,v,c in [(140,"INCOME","$0.95",MINT),(560,"UPSIDE","$0.05",PINK),(980,"EPOCH","30D",AMBER),(1400,"STATUS","NO CA",PINK)]: s.rect(x,830,330,126,BG,LINE,1,8); s.text(x+26,872,t,13,MUTED,"mono"); s.text(x+26,930,v,32,c,"bold")
    return s
def stack():
    s=Scene(1200,1200,"Tikriva workflow stack","Angular Tikriva workflow from board to payoff to journal."); header(s,"WORKFLOW / THREE SURFACES"); s.text(82,204,"ONE BOARD.",55,TEXT,"bold"); s.text(82,266,"THREE CHECKS.",55,AMBER,"bold")
    for i,(n,t,b,c) in enumerate([("01","BOARD","Read the market surface.",MINT),("02","PAYOFF","Set the boundary.",AMBER),("03","JOURNAL","Keep the why visible.",PINK)]):
        y=360+i*188; s.rect(82,y,1036,142,PANEL,LINE,1,12); s.poly([(128,y+71),(154,y+45),(180,y+71),(154,y+97)],c); s.text(154,y+77,n,14,BG,"bold","center"); s.text(220,y+63,t,28,c,"bold"); s.text(220,y+101,b,18,TEXT); s.text(1050,y+81,"OPEN",12,c,"mono","right")
    s.text(82,1080,"SOLANA / LOCAL PREVIEW / NO EXECUTION",13,MUTED,"mono"); return s
def network():
    s=Scene(1200,1200,"Tikriva Solana workflow","Tikriva workflow for watchlist, payoff and local journal."); header(s,"SOLANA / WORKFLOW","TKVA / PREVIEW"); s.text(82,200,"SCAN.",54,TEXT,"bold"); s.text(82,260,"BUILD.",54,MINT,"bold"); s.text(82,320,"REVIEW.",54,AMBER,"bold"); s.text(82,374,"User-priced scenarios with a visible paper trail.",18,MUTED)
    for i,(t,b,c) in enumerate([("WATCHLIST","Read the signal",MINT),("PAYOFF","Set the boundary",AMBER),("JOURNAL","Export your view",PINK)]):
        y=460+i*170; s.rect(82,y,1036,120,PANEL,LINE,1,12); s.text(120,y+50,f"0{i+1}",15,c,"mono"); s.text(205,y+51,t,27,c,"bold"); s.text(205,y+87,b,17,TEXT); s.text(1050,y+67,"READY",12,c,"mono","right")
    s.mark(1000,215,140,PANEL_2); s.text(84,1110,"SCENARIOS ARE ASSUMPTIONS, NOT PREDICTIONS.",13,MUTED,"mono"); return s
def concept_backing():
    s=Scene(1200,675,"SPL asset backing model","Illustrative SPL unit flows to a model series and two example positions."); s.text(54,62,"MODEL / ASSET BACKING",13,AMBER,"mono"); s.text(54,126,"One market unit backs the model.",35,TEXT,"bold"); s.text(54,160,"Illustrative only / no asset is deposited by this preview.",15,MUTED)
    for x,label,value,sub,color in [(54,"SPL UNIT","SOL","Example asset",MINT),(432,"SERIES","K / 5% cap","Model boundary",AMBER),(810,"POSITIONS","Income + Upside","Example split",PINK)]:
        s.rect(x,238,330,250,PANEL,LINE,1,6); s.text(x+24,278,label,12,MUTED,"mono"); s.text(x+24,354,value,27,color,"bold"); s.text(x+24,395,sub,14,TEXT); s.line([(x+24,435),(x+306,435)],LINE,1); s.text(x+24,464,"LOCAL PREVIEW",11,MUTED,"mono")
    s.line([(384,362),(425,362)],AMBER,3); s.poly([(425,362),(414,355),(414,369)],AMBER)
    s.line([(762,362),(803,362)],AMBER,3); s.poly([(803,362),(792,355),(792,369)],AMBER)
    return s
def concept_cap():
    s=Scene(1200,675,"Defined cap model","An illustrative price path meets cap K at the model boundary."); s.text(54,62,"MODEL / CAP BOUNDARY",13,AMBER,"mono"); s.text(54,126,"K marks the modeled boundary.",35,TEXT,"bold"); s.text(54,160,"The payoff view separates value at and above the selected cap.",15,MUTED)
    s.rect(54,216,1092,386,PANEL,LINE,1,6); s.line([(128,520),(1074,520)],LINE,1); s.line([(128,278),(128,520)],LINE,1)
    for y,label in [(300,"$220"),(380,"$200"),(460,"$180")]:
        s.line([(128,y),(1074,y)],LINE,1); s.text(108,y+5,label,11,MUTED,"mono","right")
    s.line([(760,267),(760,521)],AMBER,2); s.text(778,300,"K / $191.10",13,AMBER,"mono"); s.line([(180,478),(340,442),(495,451),(660,374),(760,354),(910,320),(1040,286)],MINT,4); s.poly([(1040,286),(1028,284),(1034,297)],MINT)
    s.text(180,557,"START / $182",11,MUTED,"mono"); s.text(950,557,"SETTLEMENT S",11,MUTED,"mono")
    return s
def concept_settlement():
    s=Scene(1200,675,"Illustrative settlement split","Example settlement value splits into Income and Upside at a defined cap."); s.text(54,62,"MODEL / SETTLEMENT",13,AMBER,"mono"); s.text(54,126,"One example settlement.",35,TEXT,"bold"); s.text(54,160,"S = $200.00 / cap K = $190.00 / per unit",15,MUTED)
    for x,label,value,color,foot in [(54,"INCOME / UP TO K","$190.00",MINT,"min(S, K)"),(438,"UPSIDE / ABOVE K","$10.00",PINK,"max(S - K, 0)")]:
        s.rect(x,238,330,250,PANEL,LINE,1,6); s.text(x+24,278,label,12,color,"mono"); s.text(x+24,375,value,45,TEXT,"bold"); s.text(x+24,421,foot,14,MUTED,"mono")
    s.text(822,383,"+",35,MUTED,"bold","center"); s.rect(878,238,268,250,PANEL_2,LINE,1,6); s.text(902,278,"TOTAL UNIT VALUE",12,MUTED,"mono"); s.text(902,375,"$200.00",32,AMBER,"bold"); s.text(902,421,"Illustrative",14,MUTED)
    s.text(54,555,"NO LIVE ORACLE / AUCTION / TRANSACTION",12,MUTED,"mono")
    return s
def og_image():
    s=Scene(1200,630,"Tikriva Solana market terminal","Tikriva market terminal preview for Solana."); header(s,"MARKETS / OG CARD","SOLANA / TKVA"); s.text(64,210,"READ THE",56,TEXT,"bold"); s.text(64,276,"MOVE.",74,AMBER,"bold"); s.text(64,335,"BUILD WITH INTENT.",42,MINT,"bold"); s.text(66,388,"Signals / payoff map / local journal",20,MUTED); s.rect(64,435,700,92,PANEL,LINE,1,8); s.text(90,473,"TKVA",17,AMBER,"bold"); s.text(90,505,"USER-PRICED / NO LIVE QUOTE",13,MUTED,"mono"); s.mark(1000,322,240,PANEL_2); s.text(66,590,"TIKRIVA / SOLANA MARKET APP PREVIEW",13,MUTED,"mono"); return s
def identity_assets(public):
    i=Scene(64,64,"Tikriva icon","Angular faceted T/K mark."); i.mark(32,32,48,PANEL_2); i.save(public/"icon.svg",True); a=Scene(180,180,"Tikriva app icon","Angular faceted T/K mark."); a.mark(90,90,136,PANEL_2); a.save(public/"apple-icon.png")
def generate():
    script=Path(__file__).resolve(); website=script.parents[1]; public=website/"public"; public.mkdir(exist_ok=True); identity_assets(public)
    for name,scene in [("hero",hero()),("token",token()),("stack",stack()),("network",network()),("concept-backing",concept_backing()),("concept-cap",concept_cap()),("concept-settlement",concept_settlement()),("og-image",og_image())]: scene.save(public/(f"{name}.webp" if name!="og-image" else "og-image.jpg"),True)
    mirror=website/"a705"
    if mirror.is_dir():
        for name in ["icon.svg","apple-icon.png","hero.webp","hero.svg","token.webp","token.svg","stack.webp","stack.svg","network.webp","network.svg","concept-backing.webp","concept-backing.svg","concept-cap.webp","concept-cap.svg","concept-settlement.webp","concept-settlement.svg","og-image.jpg","og-image.svg"]: shutil.copy2(public/name,mirror/"public"/name)
        shutil.copy2(script,mirror/"scripts"/script.name)
    print("Tikriva angular product assets regenerated.")
    if mirror.is_dir():
        for name in ["icon.svg","apple-icon.png","hero.webp","hero.svg","token.webp","token.svg","stack.webp","stack.svg","network.webp","network.svg","concept-backing.webp","concept-backing.svg","concept-cap.webp","concept-cap.svg","concept-settlement.webp","concept-settlement.svg","og-image.jpg","og-image.svg"]: assert hashlib.sha256((public/name).read_bytes()).digest()==hashlib.sha256((mirror/"public"/name).read_bytes()).digest(),name
        print("Mirror verification: public assets are byte-identical.")
if __name__=="__main__": generate()
