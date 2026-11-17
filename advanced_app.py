"""Run: python app.py. No third-party dependencies required."""
import csv
import json
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from aco import Colony, Parameters, demo_graph, random_graph, graph_from_edges, dijkstra


class App:
    def __init__(self, root):
        self.root = root
        root.title('BIC | Ant Colony Optimization • Shortest Path Lab')
        root.geometry('1180x820')
        root.minsize(950,700)
        self.graph, self.colony, self.running = demo_graph(), None, False
        self.timer = None
        style = ttk.Style()
        style.theme_use('clam')
        header = ttk.Frame(root, padding=16)
        header.pack(fill='x')
        ttk.Label(header,text='ANT COLONY  /  SHORTEST PATH LAB',font=('Segoe UI',20,'bold')).pack(anchor='w')
        ttk.Label(header,text='Explore → reinforce → evaporate → repeat. Compare every run with an exact baseline.').pack(anchor='w')
        bar = ttk.Frame(root,padding=10); bar.pack(fill='x')
        self.fields = {}
        for i,(name,value) in enumerate([('Source','A'),('Target','H'),('Ants','40'),('Iterations','100'),('Alpha','1'),('Beta','2'),('Evaporation','0.3'),('Seed','42')]):
            cell = ttk.Frame(bar); cell.pack(side='left',padx=5)
            ttk.Label(cell,text=name).pack(anchor='w')
            var = tk.StringVar(value=value); self.fields[name]=var
            ttk.Entry(cell,textvariable=var,width=10).pack()
        actions = ttk.Frame(root,padding=10); actions.pack(fill='x')
        for label,command in [('Run / restart',self.start),('Pause / resume',self.pause),('Demo graph',self.demo),('Random graph',self.random),('Load JSON',self.load),('Save graph',self.save_graph),('Export CSV',self.export)]:
            ttk.Button(actions,text=label,command=command).pack(side='left',padx=4)
        self.status = tk.StringVar(value='Ready. Choose a graph and click Run / restart.')
        ttk.Label(root,textvariable=self.status,padding=10,font=('Segoe UI',11)).pack(fill='x')
        self.canvas=tk.Canvas(root,bg='#101c30',highlightthickness=0,height=420)
        self.canvas.pack(fill='both',expand=True,padx=16)
        self.chart=tk.Canvas(root,bg='white',height=160,highlightthickness=0)
        self.chart.pack(fill='x',padx=16,pady=8)
        ttk.Label(root,text='Green = best ACO route • Blue edge thickness = pheromone • Edge labels = cost | JSON format: {"edges": [["A", "B", 2], ...]}',padding=8).pack()
        self.canvas.bind('<Configure>',lambda e:self.draw())
        self.draw()

    def demo(self):
        self.set_graph(demo_graph(),'A','H')

    def random(self):
        self.set_graph(random_graph(16,0.14,42),'0','15')

    def set_graph(self,graph,source,target):
        self.cancel_timer()
        self.running=False; self.colony=None; self.graph=graph
        self.fields['Source'].set(source); self.fields['Target'].set(target)
        self.status.set('Graph loaded. Click Run / restart.'); self.draw()

    def load(self):
        path=filedialog.askopenfilename(filetypes=[('Graph JSON','*.json')])
        if path:
            try:
                with open(path,encoding='utf-8') as f: data=json.load(f)
                graph=graph_from_edges(data['edges'],data.get('nodes',[]))
                if not graph: raise ValueError('Graph is empty.')
                self.set_graph(graph,data.get('source',next(iter(graph))),data.get('target',list(graph)[-1]))
            except (ValueError,KeyError,TypeError,OSError) as error: messagebox.showerror('Invalid graph',str(error))

    def save_graph(self):
        path=filedialog.asksaveasfilename(defaultextension='.json')
        if path:
            with open(path,'w',encoding='utf-8') as f:
                json.dump({'nodes':list(self.graph),'edges':[(u,v,w) for u in self.graph for v,w in self.graph[u].items() if u<v], 'source':self.fields['Source'].get(),'target':self.fields['Target'].get()},f,indent=2)

    def start(self):
        try:
            f={k:v.get() for k,v in self.fields.items()}
            p=Parameters(int(f['Ants']),int(f['Iterations']),float(f['Alpha']),float(f['Beta']),float(f['Evaporation']),10,int(f['Seed']))
            if p.ants>500 or p.iterations>2000: raise ValueError('GUI limit: 500 ants, 2000 iterations.')
            colony=Colony(self.graph,f['Source'],f['Target'],p)
            self.cancel_timer()
            self.colony=colony
            self.exact=dijkstra(self.graph,f['Source'],f['Target'])
            self.running=True
            self.tick(self.colony)
        except ValueError as error: messagebox.showerror('Check inputs',str(error))

    def pause(self):
        if self.colony and self.colony.iteration<self.colony.p.iterations:
            self.cancel_timer()
            self.running=not self.running
            if self.running: self.tick(self.colony)

    def cancel_timer(self):
        if self.timer is not None:
            self.root.after_cancel(self.timer)
            self.timer=None

    def tick(self,colony):
        self.timer=None
        if not self.running or colony is not self.colony: return
        colony.step()
        cost = f'{colony.cost:g}' if colony.path else 'not found'
        exact = f'{self.exact[1]:g}' if self.exact[0] else 'unreachable'
        self.status.set(f'Iteration {colony.iteration}/{colony.p.iterations}   |   ACO: {cost}   |   Dijkstra: {exact}   |   Route: {" → ".join(colony.path) or "none"}')
        self.draw()
        if not colony.reachable:
            self.status.set('No route exists: destination is disconnected.'); self.running=False
        elif colony.iteration<colony.p.iterations: self.timer=self.root.after(30,lambda:self.tick(colony))
        else: self.running=False

    def draw(self):
        c=self.canvas; c.delete('all'); self.chart.delete('all')
        w,h=max(c.winfo_width(),850),max(c.winfo_height(),350)
        nodes=list(self.graph)
        pos={u:(w/2+0.40*w*math.cos(2*math.pi*i/len(nodes)),h/2+0.37*h*math.sin(2*math.pi*i/len(nodes))) for i,u in enumerate(nodes)}
        best=set()
        if self.colony: best={tuple(sorted(e)) for e in zip(self.colony.path,self.colony.path[1:])}
        max_tau=max(self.colony.pheromone.values(),default=1) if self.colony else 1
        for u in nodes:
            for v,weight in self.graph[u].items():
                if u>=v: continue
                edge=tuple(sorted((u,v))); x,y=pos[u]; xx,yy=pos[v]
                tau=self.colony.pheromone[edge]/max_tau if self.colony else 0.1
                c.create_line(x,y,xx,yy,fill='#52e3a0' if edge in best else '#4274a4',width=4 if edge in best else 1+4*tau)
                mx,my=(x+xx)/2,(y+yy)/2
                c.create_rectangle(mx-12,my-9,mx+12,my+9,fill='#101c30',outline='')
                c.create_text(mx,my,text=f'{weight:g}',fill='#dceafa',font=('Segoe UI',9))
        for u,(x,y) in pos.items():
            color='#52e3a0' if u==self.fields['Source'].get() else '#ffca76' if u==self.fields['Target'].get() else '#e5edf9'
            c.create_oval(x-18,y-18,x+18,y+18,fill=color,outline='')
            c.create_text(x,y,text=u,fill='#101c30',font=('Segoe UI',11,'bold'))
        chart=self.chart
        chart.create_text(15,15,anchor='w',text='BEST COST BY ITERATION  (orange dashed = exact optimum)',fill='#334155')
        if self.colony:
            data=[r for r in self.colony.history if math.isfinite(r['best_cost'])]
            if data:
                hi=max(r['best_cost'] for r in data)+1; lo=min(self.exact[1],min(r['best_cost'] for r in data))-1
                cw=max(chart.winfo_width(),850)
                xy=lambda i,v:(50+(cw-80)*i/max(1,self.colony.p.iterations),135-95*(v-lo)/(hi-lo))
                if math.isfinite(self.exact[1]):
                    y=xy(0,self.exact[1])[1]; chart.create_line(50,y,cw-20,y,fill='#d97706',dash=(5,4))
                points=[z for r in data for z in xy(r['iteration'],r['best_cost'])]
                if len(points)>2: chart.create_line(*points,fill='#059669',width=3)
                chart.create_text(25,45,text=f'{hi:g}'); chart.create_text(25,135,text=f'{lo:g}')

    def export(self):
        if not self.colony: return messagebox.showinfo('Run first','Run the algorithm before exporting.')
        path=filedialog.asksaveasfilename(defaultextension='.csv')
        if path:
            with open(path,'w',newline='',encoding='utf-8') as f:
                writer=csv.DictWriter(f,fieldnames=['iteration','best_cost','successful_ants']); writer.writeheader(); writer.writerows(self.colony.history)


if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()
