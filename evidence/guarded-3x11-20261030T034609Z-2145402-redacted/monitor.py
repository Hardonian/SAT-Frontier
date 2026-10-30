import json, os, pathlib, subprocess, time, signal
root=pathlib.Path('<HOME>/SAT-Frontier-publish')
e=root/'evidence/guarded-3x11-20261030T034609Z-2145402'
cg=pathlib.Path('/sys/fs/cgroup') / pathlib.Path(open('/proc/self/cgroup').read().strip().split('::')[1].lstrip('/'))
def snap():
    files=['memory.max','memory.swap.max','pids.max','cpu.max','memory.current','memory.peak','memory.events','memory.swap.current','pids.current']
    return {k:(cg/k).read_text().strip() for k in files}
cmd=['numactl','--interleave=all','python3','scripts/run_epyc_cut_campaign.py','--workers','4','--depths','6','--instances-dir',str(e/'input'),'--evidence-dir',str(e/'campaign'),'--seconds-per-cube','12','--max-nodes-per-cube','1000000']
(e/'command.json').write_text(json.dumps({'command':cmd,'timeout_seconds':270,'initial_guard':snap(),'git_head':'4cda234278815873048b41de211c79c00e0e452c'},indent=2)+'\n')
start=time.monotonic(); timed_out=False
with (e/'campaign.log').open('w') as out, (e/'resources.jsonl').open('w') as res:
    p=subprocess.Popen(cmd,cwd=root,stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
    while p.poll() is None:
        res.write(json.dumps({'elapsed':time.monotonic()-start,**snap()})+'\n'); res.flush()
        if time.monotonic()-start>270:
            timed_out=True; os.killpg(p.pid,signal.SIGTERM)
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL)
            break
        time.sleep(3)
    p.wait(); final=snap(); res.write(json.dumps({'elapsed':time.monotonic()-start,**final})+'\n')
(e/'outcome.json').write_text(json.dumps({'returncode':p.returncode,'outer_timeout':timed_out,'elapsed_seconds':time.monotonic()-start,'final_guard':final,'interpretation':'timeout: incomplete, no result implied' if timed_out else 'inspect campaign raw result and returncode'},indent=2)+'\n')
