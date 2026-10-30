import json, os, pathlib, subprocess, time, signal, hashlib
root=pathlib.Path(__file__).resolve().parents[2]; e=pathlib.Path(__file__).resolve().parent
cg=pathlib.Path('/sys/fs/cgroup') / pathlib.Path(open('/proc/self/cgroup').read().strip().split('::')[1].lstrip('/'))
files=['memory.max','memory.swap.max','pids.max','cpu.max','memory.current','memory.peak','memory.events','memory.swap.current','pids.current']
def snap():
 d={k:(cg/k).read_text().strip() for k in files}; m={}
 for line in pathlib.Path('/proc/meminfo').read_text().splitlines():
  k,_,v=line.partition(':'); m[k]=int(v.split()[0])
 d['host_memavailable_kib']=m['MemAvailable']; d['host_swap_used_kib']=m['SwapTotal']-m['SwapFree']; return d
cmd=['numactl','--interleave=all','python3','scripts/run_epyc_cut_campaign.py','--workers','4','--depths','6','--instances-dir',str(e/'input'),'--evidence-dir',str(e/'campaign'),'--seconds-per-cube','36','--max-nodes-per-cube','3000000']
initial=snap(); assert initial['memory.max']=='6442450944' and initial['memory.swap.max']=='0' and initial['pids.max']=='32' and initial['cpu.max']=='300000 100000', initial
(e/'command.json').write_text(json.dumps({'command':cmd,'outer_timeout_seconds':900,'host_memavailable_min_kib':16777216,'host_swap_increase_limit_kib':2097152,'initial_guard':initial,'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'input_sha256':hashlib.sha256((e/'input/grid_3x11.cnf').read_bytes()).hexdigest()},indent=2)+'\n')
start=time.monotonic(); reason=None
with (e/'campaign.log').open('w') as out, (e/'resources.jsonl').open('w') as res:
 p=subprocess.Popen(cmd,cwd=root,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
 while p.poll() is None:
  now=time.monotonic()-start; state=snap(); res.write(json.dumps({'elapsed':now,**state})+'\n'); res.flush()
  if now>900: reason='outer_timeout'
  elif state['host_memavailable_kib']<16777216: reason='host_memory_guard'
  elif state['host_swap_used_kib']-initial['host_swap_used_kib']>2097152: reason='host_swap_guard'
  if reason:
   os.killpg(p.pid,signal.SIGTERM)
   try: p.wait(timeout=5)
   except subprocess.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL)
   break
  time.sleep(3)
 p.wait(); final=snap(); res.write(json.dumps({'elapsed':time.monotonic()-start,**final})+'\n')
(e/'outcome.json').write_text(json.dumps({'returncode':p.returncode,'stop_reason':reason,'elapsed_seconds':time.monotonic()-start,'final_guard':final},indent=2)+'\n')
