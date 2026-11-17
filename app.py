"""Visual ACO teaching demo: distance-based motion and one explanation at a time."""
import math
import time
import tkinter as tk
from tkinter import ttk, messagebox
from collections import Counter
from aco import Colony, Parameters, graph_from_edges, dijkstra

BG='#f1f5f9'
INK='#163047'
BLUE='#0284c7'
ORANGE='#e87924'
GREEN='#16a36b'
EDGES=[('S','A',3),('S','B',4),('A','C',3),('B','D',5),('C','T',4),('D','T',6),('A','B',4),('C','D',4)]
LAYOUT={'S':(.10,.50),'A':(.32,.21),'B':(.32,.79),'C':(.61,.21),'D':(.61,.79),'T':(.87,.50)}


def teaching_graph():
    return graph_from_edges(EDGES)


def ant_position(graph, path, distance):
    """Return edge, fractional position, and arrival using cumulative weighted distance."""
    if distance<0: return path[0],path[0],0.0,False
    for u,v in zip(path,path[1:]):
        weight=graph[u][v]
        if distance<weight: return u,v,distance/weight,False
        distance-=weight
    return path[-1],path[-1],1.0,True


class App:
    def __init__(self,root):
        self.root=root; root.title('BIC | Follow the ants')
        root.geometry(f'1180x{min(800,root.winfo_screenheight()-85)}'); root.minsize(900,640)
        root.configure(bg=BG)
        self.timer=None; self.running=False; self.colony=None
        self.ants=tk.StringVar(value='40'); self.rounds=tk.StringVar(value='5'); self.seed=tk.StringVar(value='42')
        self.speed=tk.StringVar(value='1x'); self.auto=tk.BooleanVar(value=False)
        self.phase='ready'; self.phase_time=0; self.travel=0; self.final=False
        self.attempts=[]; self.successful=[]; self.completed_rounds=[]; self.display_tau={}
        self.message=tk.StringVar(); self.detail=tk.StringVar(); self.round_text=tk.StringVar(); self.food_text=tk.StringVar(); self.best_text=tk.StringVar()
        title=tk.Frame(root,bg=BG); title.pack(fill='x',padx=24,pady=(16,8))
        tk.Label(title,text='FOLLOW THE ANTS',font=('Segoe UI',23,'bold'),bg=BG,fg=INK).pack(side='left')
        tk.Button(title,text='Settings',command=self.settings,font=('Segoe UI',11),bg='white',fg=INK,relief='flat',padx=18,pady=8).pack(side='right')
        buttons=tk.Frame(root,bg=BG); buttons.pack(fill='x',padx=24,pady=5)
        def button(text,command,color):
            b=tk.Button(buttons,text=text,command=command,font=('Segoe UI',15,'bold'),bg=color,fg='white',activebackground=color,activeforeground='white',relief='flat',padx=24,pady=13,disabledforeground='#cbd5e1')
            b.pack(side='left',padx=(0,12)); return b
        self.start_button=button('START',self.start,GREEN)
        self.pause_button=button('PAUSE',self.pause,BLUE)
        self.next_button=button('NEXT ROUND  →',self.next_round,'#334155')
        tk.Button(buttons,text='Reset',command=self.reset,font=('Segoe UI',11),bg=BG,fg=INK,relief='flat',padx=10).pack(side='left')
        tk.Checkbutton(buttons,text='Auto-play rounds',variable=self.auto,bg=BG,fg=INK,font=('Segoe UI',10)).pack(side='right')
        metrics=tk.Frame(root,bg=BG); metrics.pack(fill='x',padx=24,pady=8)
        for var in [self.round_text,self.food_text,self.best_text]:
            tk.Label(metrics,textvariable=var,font=('Segoe UI',13,'bold'),fg=INK,bg='white',padx=18,pady=9).pack(side='left',fill='x',expand=True,padx=(0,8))
        self.banner=tk.Label(root,textvariable=self.message,font=('Segoe UI',16,'bold'),bg=BG,fg=INK,anchor='w',wraplength=1080,justify='left')
        self.banner.pack(fill='x',padx=24,pady=(8,4))
        self.canvas=tk.Canvas(root,bg='#fcfdfb',highlightthickness=1,highlightbackground='#dbe3e9',height=380)
        self.canvas.pack(fill='both',expand=True,padx=24,pady=8)
        foot=tk.Frame(root,bg=BG); foot.pack(fill='x',padx=24,pady=(0,8))
        tk.Label(foot,textvariable=self.detail,font=('Segoe UI',12),bg=BG,fg=INK,anchor='w',wraplength=900,justify='left').pack(side='left',fill='x',expand=True)
        self.result_button=tk.Button(foot,text='Show best route',command=self.show_final,font=('Segoe UI',11,'bold'),bg='white',fg=GREEN,relief='flat',padx=16,pady=9)
        self.result_button.pack(side='right',padx=(10,0))
        tk.Label(root,text='Numbers = distance (map not to scale)   •   Longer distance takes longer   •   Thicker trail = more pheromone',font=('Segoe UI',10),bg=BG,fg='#52677c').pack(pady=(0,12))
        self.canvas.bind('<Configure>',lambda e:self.draw())
        root.bind('<Configure>',lambda e:self.banner.configure(wraplength=max(800,root.winfo_width()-60)) if e.widget is root else None)
        self.reset()

    def settings(self):
        window=tk.Toplevel(self.root); window.title('Demo settings'); window.resizable(False,False)
        frame=ttk.Frame(window,padding=24); frame.pack()
        ttk.Label(frame,text='Changes to ants / rounds apply on the next Start.',wraplength=350).grid(row=0,column=0,columnspan=2,pady=(0,16))
        for i,(name,var) in enumerate([('Ants per round (1–80)',self.ants),('Rounds (1–100)',self.rounds),('Random seed',self.seed)],1):
            ttk.Label(frame,text=name).grid(row=i,column=0,sticky='w',padx=(0,20),pady=8)
            ttk.Entry(frame,textvariable=var,width=10).grid(row=i,column=1)
        ttk.Label(frame,text='Animation speed').grid(row=4,column=0,sticky='w',pady=8)
        ttk.Combobox(frame,textvariable=self.speed,values=['0.5x','1x','2x','4x'],width=8,state='readonly').grid(row=4,column=1)
        ttk.Button(frame,text='Done',command=window.destroy).grid(row=5,column=0,columnspan=2,pady=(16,0))

    def cancel(self):
        if self.timer is not None: self.root.after_cancel(self.timer); self.timer=None

    def reset(self):
        self.cancel(); self.running=False; self.colony=None; self.final=False; self.phase='ready'
        self.attempts=[]; self.successful=[]; self.completed_rounds=[]; self.travel=0; self.phase_time=0
        self.display_tau={tuple(sorted((u,v))):1.0 for u,v,_ in EDGES}
        self.message.set('Can the ants find the shortest way to the food?')
        self.detail.set('Click START. Watch the ants split at the junctions.')
        self.refresh()

    def start(self):
        try:
            ants,rounds,seed=int(self.ants.get()),int(self.rounds.get()),int(self.seed.get())
            if not 1<=ants<=80 or not 1<=rounds<=100: raise ValueError('Use 1–80 ants and 1–100 rounds.')
            c=Colony(teaching_graph(),'S','T',Parameters(ants=ants,iterations=rounds,seed=seed,beta=1))
        except ValueError as error: return messagebox.showerror('Check settings',str(error))
        self.cancel(); self.colony=c; self.final=False; self.completed_rounds=[]
        self.prepare_round(); self.running=True; self.last_tick=time.perf_counter(); self.refresh(); self.schedule()

    def prepare_round(self):
        self.phase='launch'; self.phase_time=0; self.travel=0
        self.before=self.colony.pheromone.copy(); self.display_tau=self.before.copy()
        self.attempts,self.successful=self.colony.construct_paths()
        # A short release interval prevents ants on the same path covering each other.
        self.delays=[i*0.12 for i in range(len(self.attempts))]
        self.end_distance=max((a['cost']+d for a,d in zip(self.attempts,self.delays)),default=0)
        self.message.set('1. Explore — ants leave the nest and choose different paths.')
        self.detail.set('They leave in a small stream so you can follow them.')

    def schedule(self):
        if self.running: self.timer=self.root.after(30,self.tick)

    def tick(self):
        self.timer=None
        if not self.running: return
        now=time.perf_counter(); dt=min(0.15,now-self.last_tick)*float(self.speed.get()[:-1]); self.last_tick=now
        self.advance_time(dt); self.refresh(); self.schedule()

    def advance_time(self,dt):
        self.phase_time+=dt
        if self.phase=='launch' and self.phase_time>=1.0:
            self.phase='travel'; self.phase_time=0
        elif self.phase=='travel':
            self.travel=min(self.end_distance,self.travel+dt*2.4)
            arrived=self.arrived_count()
            stuck=sum(not a['success'] and self.travel>=a['cost']+d for a,d in zip(self.attempts,self.delays))
            self.message.set(f'1. Explore — {arrived} at food; {len(self.attempts)-arrived-stuck} travelling.'+(f' {stuck} stuck.' if stuck else ''))
            self.detail.set('Every ant takes the same time per distance unit. Shorter trips finish sooner after departure.')
            if self.travel>=self.end_distance:
                self.phase='compare'; self.phase_time=0
                self.message.set('2. Compare — keep the shortest successful trip.')
                self.detail.set(self.round_winner_text())
        elif self.phase=='compare' and self.phase_time>=3:
            self.phase='evaporate'; self.phase_time=0
            self.message.set('3. Update trails — old pheromone fades by 30%.')
            self.detail.set('Watch the lines become thinner. This reduces old trail scores.')
        elif self.phase=='evaporate':
            f=min(1,self.phase_time/2)
            self.display_tau={edge:max(1e-12,tau*(1-0.3*f)) for edge,tau in self.before.items()}
            if f>=1:
                self.colony.finish_round(self.successful)
                self.completed_rounds.append(self.colony.cost)
                self.after=self.colony.pheromone.copy(); self.faded=self.display_tau.copy()
                self.phase='deposit'; self.phase_time=0
                self.message.set('3. Update trails — shorter successful trips add more pheromone per ant.')
                self.detail.set('The reinforced roads become thicker. Future ants are more likely to choose them.')
        elif self.phase=='deposit':
            f=min(1,self.phase_time/2.5)
            self.display_tau={edge:self.faded[edge]+f*(tau-self.faded[edge]) for edge,tau in self.after.items()}
            if f>=1:
                if self.colony.iteration>=self.colony.p.iterations: self.show_final()
                else:
                    self.phase='review'; self.phase_time=0
                    self.message.set('Round complete. Will more ants use the good trails next time?')
                    self.detail.set('Click NEXT ROUND to see the effect of the updated pheromone.')
                    if not self.auto.get(): self.running=False
        elif self.phase=='review' and self.auto.get() and self.phase_time>=2: self.prepare_round()

    def arrived_count(self):
        if not self.attempts: return 0
        if self.phase not in ('launch','travel'): return sum(a['success'] for a in self.attempts)
        return sum(a['success'] and self.travel>=a['cost']+d for a,d in zip(self.attempts,self.delays))

    def round_winner_text(self):
        if not self.successful: return 'No ant reached food in this round.'
        path,cost=min(self.successful,key=lambda x:x[1])
        terms=' + '.join(f'{self.colony.graph[u][v]:g}' for u,v in zip(path,path[1:]))
        return f'This round: {" → ".join(path)}     Distance: {terms} = {cost:g}'

    def next_round(self):
        if not self.colony or self.final or self.phase!='review': return
        self.cancel(); self.prepare_round(); self.running=True; self.last_tick=time.perf_counter(); self.refresh(); self.schedule()

    def pause(self):
        if not self.colony or self.final or self.phase=='review': return
        self.cancel(); self.running=not self.running; self.last_tick=time.perf_counter(); self.refresh(); self.schedule()

    def show_final(self):
        # Do not silently finish unobserved rounds. This selects from completed rounds only.
        if not self.colony or self.colony.iteration==0 or self.phase not in ('review','deposit','final'): return
        self.cancel(); self.running=False; self.final=True; self.phase='final'; self.display_tau=self.colony.pheromone.copy()
        path=self.colony.path; cost=self.colony.cost
        _,exact=dijkstra(self.colony.graph,'S','T')
        self.message.set('4. Selected — the shortest route found is highlighted in green.' if cost==exact else '4. Selected — the best route found is highlighted in green.')
        self.detail.set(f'{" → ".join(path)}     Total distance: {cost:g}     Exact shortest: {exact:g}     Completed rounds: {self.colony.iteration}')
        self.refresh()

    def refresh(self):
        c=self.colony
        round_no=0 if not c else c.iteration+(1 if self.phase in ('launch','travel','compare','evaporate') else 0)
        self.round_text.set(f'ROUND   {round_no} / {c.p.iterations if c else self.rounds.get()}')
        stopped=sum(not a['success'] for a in self.attempts) if self.phase not in ('ready','launch','travel') else 0
        self.food_text.set(f'AT FOOD   {self.arrived_count()} / {c.p.ants if c else self.ants.get()}'+(f'  ({stopped} stuck)' if stopped else ''))
        best=f'{c.cost:g}' if c and math.isfinite(c.cost) else '—'
        self.best_text.set(f'BEST DISTANCE   {best}')
        self.start_button.configure(text='RESTART' if c else 'START')
        self.pause_button.configure(text='RESUME' if c and not self.running and self.phase not in ('review','final') else 'PAUSE',state='normal' if c and not self.final and self.phase!='review' else 'disabled')
        self.next_button.configure(state='normal' if self.phase=='review' else 'disabled')
        self.result_button.configure(state='normal' if self.phase=='review' else 'disabled')
        self.draw()

    def draw_ant(self,x,y,angle,color,tag=True):
        c=self.canvas; cs,sn=math.cos(angle),math.sin(angle)
        def pt(a,b): return x+a*cs-b*sn,y+a*sn+b*cs
        for a in (-3,0,3):
            x1,y1=pt(a,-5); x2,y2=pt(a+2,5)
            c.create_line(x1,y1,x2,y2,fill=color,width=1.4,tags=('ant_detail',))
        for a,r in [(-4,3.3),(0,2.3),(4,2.7)]:
            xx,yy=pt(a,0); c.create_oval(xx-r,yy-r,xx+r,yy+r,fill=color,outline='#ffffff',width=.4,tags=('ant',) if tag and a==0 else ('ant_detail',))

    def draw(self):
        c=self.canvas; c.delete('all')
        w=max(c.winfo_width(),800); h=max(c.winfo_height(),270)
        # Leave generous clear space around food and the nest.
        positions={node:(x*w,35+y*(h-70)) for node,(x,y) in LAYOUT.items()}
        selected=set()
        if self.final: selected={tuple(sorted(e)) for e in zip(self.colony.path,self.colony.path[1:])}
        elif self.phase=='compare' and self.successful:
            path,_=min(self.successful,key=lambda x:x[1]); selected={tuple(sorted(e)) for e in zip(path,path[1:])}
        for u,v,weight in EDGES:
            edge=tuple(sorted((u,v))); x,y=positions[u]; xx,yy=positions[v]
            tau=self.display_tau.get(edge,1); width=3+2.4*math.log1p(tau)
            color=GREEN if edge in selected else '#a7c9b8' if self.phase in ('deposit','review') else '#bdcbd1'
            if self.final and edge not in selected: color='#e2e8ed'; width=3
            c.create_line(x,y,xx,yy,fill=color,width=width,capstyle='round')
            mx,my=(x+xx)/2,(y+yy)/2
            c.create_oval(mx-14,my-14,mx+14,my+14,fill='white',outline='#e2e8f0')
            c.create_text(mx,my,text=weight,font=('Segoe UI',13,'bold'),fill=INK)
        for node,(x,y) in positions.items():
            radius=23 if node in ('S','T') else 17
            fill='#fef3c7' if node=='S' else '#dcfce7' if node=='T' else 'white'
            c.create_oval(x-radius,y-radius,x+radius,y+radius,fill=fill,outline='#94a3b8',width=1.5)
            c.create_text(x,y,text=node,font=('Segoe UI',13,'bold'),fill=INK)
        sx,sy=positions['S']; tx,ty=positions['T']
        c.create_text(sx,sy-42,text='NEST',font=('Segoe UI',12,'bold'),fill=INK)
        c.create_text(tx,ty-42,text='FOOD',font=('Segoe UI',12,'bold'),fill=GREEN)
        c.create_text(tx,ty+43,text=f'{self.arrived_count()} arrived',font=('Segoe UI',12,'bold'),fill=GREEN)
        if self.colony and self.phase in ('launch','travel'):
            for i,(a,delay) in enumerate(zip(self.attempts,self.delays)):
                distance=self.travel-delay if self.phase=='travel' else -1
                u,v,f,ended=ant_position(self.colony.graph,a['path'],distance)
                if ended:
                    if not a['success']:
                        x,y=positions[a['path'][-1]]
                        c.create_text(x+25,y+10+(i%3)*8,text='×',fill='#dc2626',font=('Segoe UI',14,'bold'))
                    continue  # Food counter replaces the unreadable pile of arrived ants.
                color=BLUE if a['path'][1]=='A' else ORANGE
                if distance<0:
                    x=sx-36+(i%8)*9; y=sy+32+(i//8)*11
                    self.draw_ant(x,y,0,'#64748b'); continue
                x,y=positions[u]; xx,yy=positions[v]; angle=math.atan2(yy-y,xx-x)
                offset=((i%5)-2)*5
                x=x+(xx-x)*f-math.sin(angle)*offset
                y=y+(yy-y)*f+math.cos(angle)*offset
                self.draw_ant(x,y,angle,color)
        c.create_text(w/2,15,text='Blue ants take the upper first turn. Orange ants take the lower first turn.',font=('Segoe UI',10),fill='#64748b')
        if self.final: c.create_text(w/2,h-14,text='GREEN = SELECTED ROUTE',font=('Segoe UI',12,'bold'),fill=GREEN)


if __name__=='__main__':
    root=tk.Tk(); App(root)
    if root.tk.call('tk','windowingsystem')=='win32': root.state('zoomed')
    root.mainloop()
