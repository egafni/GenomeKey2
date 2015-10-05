"""
Provides a way to run and time multiple bash commands.  Raises an exception on any non 0 return codes.
"""
from concurrent import futures
import time
import subprocess as sp
import sys
from functools import partial
from recordtype import recordtype


def format_time(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%d:%02d:%02d" % (h, m, s)

Result = recordtype('Record', 'time attempt cmd out successful')

def run_cmd(cmd, retry, retry_wait):
    start = time.time()
    results = []
    for attempt in range(1, retry+3):
        p = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)
        successful = p.wait() == 0
        s = p.stdout.read().strip()
        s = ("\n" + s) if s else ''
        results.append(Result(time=format_time(time.time() - start), attempt=attempt, cmd=cmd, out=s, successful=successful))
        if successful:
            break
        else:
            time.sleep(retry_wait)
            
    return results

class Parallel():
    def __init__(self, retry=1, retry_wait=60):
        self.cmds = []
        self.retry = retry
        self.retry_wait = 60

    def __enter__(self):
        return self

    def run(self, cmd):
        self.cmds.append(cmd)

    def __exit__(self, exc_type, exc_val, exc_tb):
        with futures.ThreadPoolExecutor(len(self.cmds)) as ex:
            futes = [ ex.submit(partial(run_cmd, retry=self.retry, retry_wait=self.retry_wait), cmd) for cmd in self.cmds ]
            for fr in futures.as_completed(futes):
                results = fr.result()
                for r in results:
                    print '[attempt_{r.attempt} {s}, after {r.time})] {r.cmd}{r.out}'.format(r=r, s = 'successful' if r.successful else 'failed')
                if not results[-1].successful:
                    sys.exit(127)

"""
python - << EOF
from genomekey.api import Parallel
with Parallel() as p:
    p.run('''mkdir -p SM_UOC013232_222_A1/work/LB_1 && /genomekey/share/opt/samtools/1.2_libcurl/samtools view -hb s3://ngx-genomekey-out/Pilot_1genome_v2/SM_UOC013232_222_A1/work/LB_1/deduped.bam 2:1-10000 > SM_UOC013232_222_A1/work/LB_1/deduped.bam && /genomekey/share/opt/samtools/1.2_libcurl/samtools index SM_UOC013232_222_A1/work/LB_1/deduped.bam''')
    p.run('''aws s3 cp --only-show-errors s3://ngx-genomekey-out/Pilot_1genome_v2/tmp/contigs/2/target.bed tmp/contigs/2/target.bed''')
EOF
"""