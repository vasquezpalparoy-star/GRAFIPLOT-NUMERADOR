import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk
import fitz, io, os

MM=72/25.4
class App:
 def __init__(self,r):
  self.r=r;r.title("GRAFIPLOT NUMERADOR A4");r.geometry("1140x790")
  self.src=None;self.kind=None;self.pg=0;self.im=None;self.doc=None;self.preview=None;self.drag=False
  self.val={k:tk.StringVar(value=v) for k,v in dict(orient="Vertical",start="1",count="10",zeros="2",prefix="N° ",size="20",color="#d00000",x="120",y="35",zoom="100").items()}
  side=tk.Frame(r,width=270,padx=12,pady=12);side.pack(side="left",fill="y")
  tk.Label(side,text="GRAFIPLOT NUMERADOR",font=("Arial",15,"bold")).pack(pady=10)
  tk.Button(side,text="CARGAR PDF O IMAGEN",command=self.load).pack(fill="x",pady=8)
  self.chooser=ttk.Combobox(side,values=["Vertical","Horizontal"],state="readonly",textvariable=self.val["orient"]);self.field(side,"A4 orientación",self.chooser)
  for lbl,key in [("Número inicial","start"),("Cantidad de hojas","count"),("Ceros antes del número","zeros"),("Prefijo","prefix"),("Tamaño (puntos)","size"),("Color hexadecimal","color"),("Posición horizontal (mm)","x"),("Posición vertical (mm)","y")]:
   self.field(side,lbl,tk.Entry(side,textvariable=self.val[key]))
  tk.Button(side,text="ELEGIR COLOR",command=self.color).pack(fill="x",pady=3)
  tk.Button(side,text="EXPORTAR PDF NUMERADO",command=self.export,bg="#036eab",fg="white").pack(fill="x",pady=16)
  tk.Label(side,text="Arrastra el número sobre la hoja.\nCtrl + rueda: zoom",justify="left").pack(anchor="w")
  right=tk.Frame(r,bg="#253448");right.pack(side="right",fill="both",expand=True)
  bar=tk.Frame(right);bar.pack(fill="x")
  tk.Button(bar,text="−",command=lambda:self.zoom(-20)).pack(side="left")
  self.zoomlabel=tk.Label(bar,text="100%");self.zoomlabel.pack(side="left",padx=8)
  tk.Button(bar,text="+",command=lambda:self.zoom(20)).pack(side="left")
  tk.Button(bar,text="Ajustar",command=self.fit).pack(side="left",padx=12)
  tk.Button(bar,text="◀",command=lambda:self.change(-1)).pack(side="left")
  self.pagetext=tk.Label(bar,text="1 / 10");self.pagetext.pack(side="left",padx=5)
  tk.Button(bar,text="▶",command=lambda:self.change(1)).pack(side="left")
  canvaswrap=tk.Frame(right);canvaswrap.pack(fill="both",expand=True)
  self.c=tk.Canvas(canvaswrap,bg="#34465c",highlightthickness=0)
  sx=tk.Scrollbar(canvaswrap,orient="horizontal",command=self.c.xview);sy=tk.Scrollbar(canvaswrap,command=self.c.yview)
  self.c.configure(xscrollcommand=sx.set,yscrollcommand=sy.set)
  self.c.grid(row=0,column=0,sticky="nsew");sy.grid(row=0,column=1,sticky="ns");sx.grid(row=1,column=0,sticky="ew")
  canvaswrap.rowconfigure(0,weight=1);canvaswrap.columnconfigure(0,weight=1)
  self.c.bind("<Button-1>",self.click);self.c.bind("<B1-Motion>",self.move);self.c.bind("<ButtonRelease-1>",lambda e:setattr(self,"drag",False))
  self.c.bind("<Control-MouseWheel>",lambda e:self.zoom(20 if e.delta>0 else -20))
  self.c.bind("<Configure>",lambda e:self.draw())
  for v in self.val.values():v.trace_add("write",lambda *_:self.draw())
  r.after(300,self.fit)
 def field(self,parent,label,widget):
  tk.Label(parent,text=label,anchor="w").pack(fill="x",pady=(7,0));widget.pack(fill="x")
 def color(self):
  c=colorchooser.askcolor(color=self.val["color"].get())[1]
  if c:self.val["color"].set(c)
 def dims(self):return (210,297) if self.val["orient"].get()=="Vertical" else (297,210)
 def number(self,i):
  start=int(self.val["start"].get());z=max(0,int(self.val["zeros"].get()))
  return self.val["prefix"].get()+str(start+i).zfill(z+1)
 def load(self):
  path=filedialog.askopenfilename(filetypes=[("PDF e imágenes","*.pdf *.png *.jpg *.jpeg *.webp *.bmp"),("Todos","*.*")])
  if not path:return
  try:
   if self.doc:self.doc.close()
   self.doc=None;self.im=None
   if path.lower().endswith(".pdf"):self.doc=fitz.open(path);self.kind="pdf"
   else:self.im=Image.open(path).convert("RGB");self.kind="image"
   self.src=path;self.pg=0;self.draw()
  except Exception as e:messagebox.showerror("Archivo",str(e))
 def change(self,step):
  count=max(1,int(self.val["count"].get()));self.pg=max(0,min(count-1,self.pg+step));self.draw()
 def zoom(self,d):
  try:v=int(self.val["zoom"].get())
  except:v=100
  self.val["zoom"].set(str(max(25,min(400,v+d))))
 def fit(self):
  w,h=self.dims();a=max(200,self.c.winfo_width()-60);b=max(200,self.c.winfo_height()-60)
  self.val["zoom"].set(str(max(25,min(350,int(min(a/w,b/h)*100/3.0)))))
 def frame_data(self):
  w,h=self.dims();zoom=int(self.val["zoom"].get())/100;scale=3*zoom
  return w,h,scale,int(w*scale),int(h*scale)
 def base(self,w,h,pw,ph):
  image=Image.new("RGB",(pw,ph),"white")
  if self.kind=="pdf" and self.doc:
   p=self.doc[self.pg%len(self.doc)];rect=p.rect
   factor=min(pw/rect.width,ph/rect.height)
   pix=p.get_pixmap(matrix=fitz.Matrix(factor,factor),alpha=False)
   inp=Image.frombytes("RGB",(pix.width,pix.height),pix.samples)
   image.paste(inp,((pw-inp.width)//2,(ph-inp.height)//2))
  elif self.kind=="image" and self.im:
   src=self.im;factor=min(pw/src.width,ph/src.height)
   tw=max(1,int(src.width*factor));th=max(1,int(src.height*factor))
   inp=src.resize((tw,th),Image.Resampling.LANCZOS)
   image.paste(inp,((pw-tw)//2,(ph-th)//2))
  return image
 def draw(self):
  try:
   w,h,s,pw,ph=self.frame_data()
   if pw>4500 or ph>4500:return
   bg=self.base(w,h,pw,ph)
   self.preview=ImageTk.PhotoImage(bg);self.c.delete("all")
   self.c.create_image(25,25,image=self.preview,anchor="nw")
   self.c.create_rectangle(25,25,25+pw,25+ph,outline="#c9d4e0")
   x=float(self.val["x"].get())*s;y=float(self.val["y"].get())*s
   size=max(7,int(float(self.val["size"].get())*s/MM))
   self.c.create_text(25+x,25+y,anchor="nw",text=self.number(self.pg),font=("Arial",size,"bold"),fill=self.val["color"].get(),tags="number")
   self.c.configure(scrollregion=(0,0,pw+60,ph+60));self.zoomlabel.config(text=self.val["zoom"].get()+"%")
   self.pagetext.config(text=f'{self.pg+1} / {self.val["count"].get()}')
  except (ValueError,tk.TclError,ZeroDivisionError):pass
 def click(self,e):
  x=self.c.canvasx(e.x);y=self.c.canvasy(e.y)
  self.drag="number" in self.c.gettags("current")
 def move(self,e):
  if not self.drag:return
  w,h,s,_,_=self.frame_data()
  x=max(0,min(w,(self.c.canvasx(e.x)-25)/s));y=max(0,min(h,(self.c.canvasy(e.y)-25)/s))
  self.val["x"].set(f"{x:.1f}");self.val["y"].set(f"{y:.1f}")
 def export(self):
  try:
   count=int(self.val["count"].get())
   if count<1 or count>10000:raise ValueError("Cantidad debe ser entre 1 y 10000")
   w,h=self.dims();out=fitz.open()
   x=float(self.val["x"].get())*MM;y=float(self.val["y"].get())*MM
   size=float(self.val["size"].get())
   rgb=tuple(int(self.val["color"].get()[i:i+2],16)/255 for i in (1,3,5))
   for i in range(count):
    page=out.new_page(width=w*MM,height=h*MM)
    if self.kind=="pdf" and self.doc:
     p=self.doc[i%len(self.doc)];r=p.rect;factor=min(page.rect.width/r.width,page.rect.height/r.height)
     aw=r.width*factor;ah=r.height*factor
     rect=fitz.Rect((page.rect.width-aw)/2,(page.rect.height-ah)/2,(page.rect.width+aw)/2,(page.rect.height+ah)/2)
     page.show_pdf_page(rect,self.doc,i%len(self.doc),keep_proportion=True)
    elif self.kind=="image" and self.im:
     b=io.BytesIO();self.im.save(b,format="PNG")
     page.insert_image(page.rect,stream=b.getvalue(),keep_proportion=True)
    page.insert_text((x,y+size),self.number(i),fontsize=size,fontname="hebo",color=rgb,overlay=True)
   path=filedialog.asksaveasfilename(defaultextension=".pdf",initialfile="GRAFIPLOT_NUMERADO.pdf",filetypes=[("PDF","*.pdf")])
   if path:out.save(path,garbage=4,deflate=True);messagebox.showinfo("Correcto",f"PDF creado: {path}")
   out.close()
  except Exception as e:messagebox.showerror("Error de exportación",str(e))
if __name__=="__main__":
 root=tk.Tk();App(root);root.mainloop()
