"""ACO route search with inspectable, once-per-round pheromone updates."""
import math
import time
import tkinter as tk
from tkinter import ttk, messagebox
from aco import Colony, Parameters, graph_from_edges, dijkstra

BG='#f1f5f9'
INK='#163047'
BLUE='#0284c7'
ORANGE='#e87924'
GREEN='#16a36b'
EDGES=[('A','D',8),('D','G',5),('G','J',8),('B','E',9),('E','H',6),('H','K',3),('C','F',8),('F','I',7),('I','L',2),('A','B',3),('B','C',3),('D','E',4),('E','F',9),('G','H',2),('H','I',8),('J','K',5),('K','L',6),('S','A',6),('S','B',7),('S','C',7),('J','T',3),('K','T',8),('L','T',9)]
LAYOUT={'S':(.05,.50),'T':(.95,.50)}
for column,nodes in enumerate(('ABC','DEF','GHI','JKL')):
    for row,node in enumerate(nodes):
        LAYOUT[node]=(.23+.18*column,.12+.38*row)


def score_breakdown(before, successful, evaporation=0.3, q=10):
    """Read-only preview of exactly the solver's evaporation and deposit rule."""
    rewards={edge:0.0 for edge in before}
    for path,cost in successful:
        for u,v in zip(path,path[1:]): rewards[tuple(sorted((u,v)))]+=q/cost
    return {edge: {'old':old,'remaining':max(1e-12,(1-evaporation)*old),
                   'reward':rewards[edge],
                   'new':max(1e-12,(1-evaporation)*old)+rewards[edge]}
            for edge,old in before.items()}



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
        root.geometry(f'1180x{min(800,root.winfo_screenheight()-85)}'); root.minsize(1050,700)
        root.configure(bg=BG)
        self.timer=None; self.running=False; self.colony=None
        self.score_popup=None; self.popup_tree=None; self.applied=False; self.score_rows={}; self.popups_enabled=True
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
        self.update_button=button('UPDATE SCORES',self.update_scores,'#087f70')
        self.next_button=button('NEXT ROUND  →',self.next_round,'#334155')
        tk.Button(buttons,text='Reset',command=self.reset,font=('Segoe UI',11),bg=BG,fg=INK,relief='flat',padx=10).pack(side='left')
        tk.Checkbutton(title,text='Auto-play rounds',variable=self.auto,command=self.auto_changed,bg=BG,fg=INK,font=('Segoe UI',10)).pack(side='right',padx=12)
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
        tk.Label(root,text='D = distance   •   P = preference / pheromone score   •   New P = old P × 0.70 + successful-ant rewards',font=('Segoe UI',10),bg=BG,fg='#52677c').pack(pady=(0,12))
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

    def auto_changed(self):
        if self.phase in ('pending','review'):
            self.cancel(); self.running=self.auto.get(); self.phase_time=0
            self.last_tick=time.perf_counter(); self.schedule(); self.refresh()

    def reset(self):
        self.cancel(); self.close_popup(); self.running=False; self.colony=None; self.final=False; self.phase='ready'
        self.applied=False; self.score_rows={}
        self.attempts=[]; self.successful=[]; self.completed_rounds=[]; self.travel=0; self.phase_time=0
        self.display_tau={tuple(sorted((u,v))):1.0 for u,v,_ in EDGES}
        self.message.set('Can the ants find the shortest way to the food?')
        self.detail.set('14 nodes, 23 roads. Default seed 42 is a reproducible teaching example; the answer is not forced.')
        self.refresh()

    def start(self):
        try:
            ants,rounds,seed=int(self.ants.get()),int(self.rounds.get()),int(self.seed.get())
            if not 1<=ants<=80 or not 1<=rounds<=100: raise ValueError('Use 1–80 ants and 1–100 rounds.')
            c=Colony(teaching_graph(),'S','T',Parameters(ants=ants,iterations=rounds,seed=seed,beta=1))
        except ValueError as error: return messagebox.showerror('Check settings',str(error))
        self.cancel(); self.close_popup(); self.colony=c; self.final=False; self.completed_rounds=[]
        self.prepare_round(); self.running=True; self.last_tick=time.perf_counter(); self.refresh(); self.schedule()

    def prepare_round(self):
        self.phase='launch'; self.phase_time=0; self.travel=0; self.applied=False
        self.before=self.colony.pheromone.copy(); self.display_tau=self.before.copy()
        self.attempts,self.successful=self.colony.construct_paths()
        self.score_rows=score_breakdown(self.before,self.successful,self.colony.p.evaporation,self.colony.p.q)
        # A short release interval prevents ants on the same path covering each other.
        self.delays=[i*0.12 for i in range(len(self.attempts))]
        self.end_distance=max((a['cost']+d for a,d in zip(self.attempts,self.delays)),default=0)
        self.message.set('1. Explore — ants leave the nest and choose different paths.')
        self.detail.set('Each edge shows its starting P score for this round. These scores stay fixed while the ants explore.')

    def schedule(self):
        if self.running: self.timer=self.root.after(30,self.tick)

    def tick(self):
        self.timer=None
        if not self.running: return
        now=time.perf_counter(); dt=min(0.15,now-self.last_tick)*float(self.speed.get()[:-1]); self.last_tick=now
        self.advance_time(dt); self.refresh(); self.schedule()

    def advance_time(self,dt):
        self.phase_time+=dt
        if self.phase=='launch' and self.phase_time>=2.5:
            self.phase='travel'; self.phase_time=0
        elif self.phase=='travel':
            self.travel=min(self.end_distance,self.travel+dt*5.0)
            arrived=self.arrived_count()
            stuck=sum(not a['success'] and self.travel>=a['cost']+d for a,d in zip(self.attempts,self.delays))
            self.message.set(f'Explore — {arrived} at food; {len(self.attempts)-arrived-stuck} travelling.'+(f' {stuck} stuck.' if stuck else ''))
            self.detail.set('Distance controls travel time. Scores do not change until this round is complete.')
            if self.travel>=self.end_distance: self.round_completed()
        elif self.phase in ('pending','review') and self.auto.get() and self.phase_time>=4:
            self.apply_scores()
            self.close_popup()
            if self.colony.iteration>=self.colony.p.iterations: self.show_final()
            else: self.prepare_round()

    def round_completed(self):
        self.phase='pending'; self.phase_time=0; self.running=self.auto.get()
        self.message.set('Round complete — update the preference scores when you are ready.')
        self.detail.set(self.round_winner_text())
        self.open_score_popup()

    def close_popup(self):
        if self.score_popup is not None:
            try: self.score_popup.destroy()
            except tk.TclError: pass
        self.score_popup=None; self.popup_tree=None

    def open_score_popup(self):
        if not self.popups_enabled: return
        self.close_popup()
        window=tk.Toplevel(self.root); self.score_popup=window
        window.title('Update preference scores'); window.geometry('730x480'); window.minsize(650,410)
        window.transient(self.root); window.protocol('WM_DELETE_WINDOW',self.close_popup)
        frame=ttk.Frame(window,padding=18); frame.pack(fill='both',expand=True)
        self.popup_title=tk.StringVar()
        ttk.Label(frame,textvariable=self.popup_title,font=('Segoe UI',16,'bold'),wraplength=680).pack(anchor='w')
        ttk.Label(frame,text='New score = old score × 0.70 + rewards. Each successful ant adds 10 / its route distance.',wraplength=680).pack(anchor='w',pady=(8,12))
        wrap=ttk.Frame(frame); wrap.pack(fill='both',expand=True)
        tree=ttk.Treeview(wrap,columns=('edge','old','fade','reward','new'),show='headings',height=10)
        self.popup_tree=tree
        for key,label,width in [('edge','Road',90),('old','Old P',100),('fade','After −30%',120),('reward','+ Reward',120),('new','New P',120)]:
            tree.heading(key,text=label);tree.column(key,width=width,anchor='center')
        scroll=ttk.Scrollbar(wrap,command=tree.yview);tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');tree.pack(side='left',fill='both',expand=True)
        controls=ttk.Frame(frame);controls.pack(fill='x',pady=(12,0))
        self.popup_update=tk.Button(controls,text='UPDATE SCORES',command=self.update_scores,bg=GREEN,fg='white',font=('Segoe UI',12,'bold'),relief='flat',padx=16,pady=12)
        self.popup_update.pack(side='left')
        self.popup_next=tk.Button(controls,text='NEXT ROUND →',command=self.next_round,bg=BLUE,fg='white',font=('Segoe UI',12,'bold'),relief='flat',padx=16,pady=12)
        self.popup_next.pack(side='right')
        ttk.Label(frame,text='You may close this window. NEXT ROUND applies any pending update exactly once.',wraplength=680).pack(anchor='w',pady=(10,0))
        self.refresh_popup()

    def refresh_popup(self):
        if self.score_popup is None or self.popup_tree is None: return
        self.popup_title.set('Scores updated — these values carry into the next round.' if self.applied else 'Round finished — score update is pending.')
        for row in self.popup_tree.get_children(): self.popup_tree.delete(row)
        for edge,values in self.score_rows.items():
            self.popup_tree.insert('', 'end',values=('-'.join(edge),*[f"{values[k]:.4f}" for k in ('old','remaining','reward','new')]))
        self.popup_update.configure(state='disabled' if self.applied else 'normal')
        is_last=self.colony.iteration>=self.colony.p.iterations if self.applied else self.colony.iteration+1>=self.colony.p.iterations
        self.popup_next.configure(text='FINISH / SHOW RESULT' if is_last else 'NEXT ROUND →')

    def apply_scores(self):
        if not self.colony or self.applied or self.phase!='pending': return False
        self.colony.finish_round(self.successful)
        self.applied=True; self.completed_rounds.append(self.colony.cost)
        self.display_tau=self.colony.pheromone.copy()
        self.phase='review';self.phase_time=0
        self.message.set('Scores updated: 30% evaporated, then earned rewards added.')
        self.detail.set('The displayed P values are the final scores. The next round starts with these same values.')
        self.refresh_popup()
        return True

    def update_scores(self):
        self.apply_scores()
        if self.colony and self.applied and self.colony.iteration>=self.colony.p.iterations: self.show_final()
        self.refresh()

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
        if self.final: self.close_popup(); return
        if not self.colony or self.phase not in ('pending','review'): return
        self.cancel(); self.apply_scores(); self.close_popup()
        if self.colony.iteration>=self.colony.p.iterations:
            self.show_final(); return
        self.prepare_round(); self.running=True; self.last_tick=time.perf_counter(); self.refresh(); self.schedule()

    def pause(self):
        if not self.colony or self.final or self.phase in ('pending','review'): return
        self.cancel(); self.running=not self.running; self.last_tick=time.perf_counter(); self.refresh(); self.schedule()

    def show_final(self):
        if not self.colony or self.phase not in ('pending','review','final'): return
        self.apply_scores()
        self.cancel(); self.running=False; self.final=True; self.phase='final'; self.display_tau=self.colony.pheromone.copy()
        path=self.colony.path;cost=self.colony.cost
        _,exact=dijkstra(self.colony.graph,'S','T')
        self.message.set('Selected — the shortest route found is green.' if cost==exact else 'Selected — the best route discovered is green.')
        self.detail.set(f'{" → ".join(path) or "No route discovered"}   |   Distance: {cost:g}   |   Exact shortest: {exact:g}   |   Completed rounds: {self.colony.iteration}')
        self.refresh_popup();self.refresh()

    def refresh(self):
        c=self.colony
        round_no=0 if not c else c.iteration+(1 if self.phase in ('launch','travel','pending') else 0)
        self.round_text.set(f'ROUND   {round_no} / {c.p.iterations if c else self.rounds.get()}')
        stopped=sum(not a['success'] for a in self.attempts) if self.phase not in ('ready','launch','travel') else 0
        self.food_text.set(f'AT FOOD   {self.arrived_count()} / {c.p.ants if c else self.ants.get()}'+(f'  ({stopped} stuck)' if stopped else ''))
        best_cost=min([c.cost]+[cost for _,cost in self.successful]) if c and self.phase=='pending' else c.cost if c else math.inf
        best=f'{best_cost:g}' if math.isfinite(best_cost) else '—'
        self.best_text.set(f'BEST DISTANCE   {best}')
        self.start_button.configure(text='RESTART' if c else 'START')
        self.pause_button.configure(text='RESUME' if c and not self.running and self.phase not in ('pending','review','final') else 'PAUSE',state='normal' if c and not self.final and self.phase not in ('pending','review') else 'disabled')
        self.update_button.configure(state='normal' if self.phase=='pending' else 'disabled')
        self.next_button.configure(text='FINISH →' if c and self.phase in ('pending','review') and c.iteration+(0 if self.applied else 1)>=c.p.iterations else 'NEXT ROUND →',state='normal' if self.phase in ('pending','review') else 'disabled')
        self.result_button.configure(state='normal' if self.phase in ('pending','review') else 'disabled')
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
        w=max(c.winfo_width(),800); h=max(c.winfo_height(),340)
        # Leave generous clear space around food and the nest.
        positions={node:(x*w,35+y*(h-70)) for node,(x,y) in LAYOUT.items()}
        selected=set()
        if self.final: selected={tuple(sorted(e)) for e in zip(self.colony.path,self.colony.path[1:])}
        elif self.phase=='pending' and self.successful:
            path,_=min(self.successful,key=lambda x:x[1]); selected={tuple(sorted(e)) for e in zip(path,path[1:])}
        for u,v,weight in EDGES:
            edge=tuple(sorted((u,v))); x,y=positions[u]; xx,yy=positions[v]
            tau=self.display_tau.get(edge,1); width=3+2.4*math.log1p(tau)
            color=GREEN if edge in selected else '#a7c9b8' if self.phase=='review' else '#bdcbd1'
            if self.final and edge not in selected: color='#e2e8ed'; width=3
            c.create_line(x,y,xx,yy,fill=color,width=width,capstyle='round')
            mx,my=(x+xx)/2,(y+yy)/2
            c.create_rectangle(mx-34,my-20,mx+34,my+20,fill='white',outline='#dce5eb')
            c.create_text(mx,my-8,text=f'D: {weight}',font=('Segoe UI',10,'bold'),fill=INK,tags=('distance_label',))
            c.create_text(mx,my+9,text=f'P: {tau:.2f}',font=('Segoe UI',9,'bold'),fill='#087f70',tags=('score_label',))
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
                color={'A':BLUE,'B':ORANGE,'C':'#8b5cf6'}.get(a['path'][1],BLUE)
                if distance<0:
                    x=sx-36+(i%8)*9; y=sy+32+(i//8)*11
                    self.draw_ant(x,y,0,'#64748b'); continue
                x,y=positions[u]; xx,yy=positions[v]; angle=math.atan2(yy-y,xx-x)
                offset=((i%5)-2)*5
                x=x+(xx-x)*f-math.sin(angle)*offset
                y=y+(yy-y)*f+math.cos(angle)*offset
                self.draw_ant(x,y,angle,color)
        c.create_text(w/2,15,text='D = distance   |   P = current preference score (pheromone)   |   Scores update once after each round',font=('Segoe UI',10),fill='#64748b')
        if self.final: c.create_text(w/2,h-14,text='GREEN = SELECTED ROUTE',font=('Segoe UI',12,'bold'),fill=GREEN)


if __name__=='__main__':
    root=tk.Tk(); App(root)
    if root.tk.call('tk','windowingsystem')=='win32': root.state('zoomed')
    root.mainloop()
