import os

from cosmos import abstract_input_taskfile as aif, abstract_output_taskfile as aof
from ... import settings as s
from ... import GK_Tool
from genomekey.aws import s3



# stream a normal s3 stream/pull and stream auto s3/stream pull
class FastQC(GK_Tool):
    cpu_req = 2
    skip_s3_pull = True
    # s3_streamable = ['reads']

    def cmd(self, reads=aif(format='fastq', n='>=2'),
            out_dir=aof(name='fastqc', format='dir')):
        fastqc_tmp_dir = os.path.join(self.output_dir, 'tmp')
        r1s = filter(lambda tf: tf.task_output_for.tags['read_pair'] in [1, '1'], reads)
        r2s = filter(lambda tf: tf.task_output_for.tags['read_pair'] in [2, '2'], reads)
        assert len(r1s) == len(r2s)


        # if fastq files are in s3, download them
        r1s, s3_pulls_1 = s3.pull_if_s3(r1s, fastqc_tmp_dir)
        r2s, s3_pulls_2 = s3.pull_if_s3(r2s, fastqc_tmp_dir)

        if len(r1s) > 1:
            # If there are more than 1 fastqs per read_pair, merge them into one file per read_pair
            # Note, catting compressed files together seems fine
            r1, r2 = os.path.join(fastqc_tmp_dir, 'r1.fastq.gz'), os.path.join(fastqc_tmp_dir, 'r2.fastq.gz')
            cat = r"""
            cat {r1s_join} > {r1}
            cat {r2s_join} > {r2}
            """.format(s=s,
                       r1s_join=' '.join(map(str, r1s)),
                       r2s_join=' '.join(map(str, r2s)),
                       **locals())
        else:
            r1, r2 = r1s[0], r2s[0]
            cat = ""

        return r"""
            mkdir -p {fastqc_tmp_dir}
            {s3_pulls_1}
            {s3_pulls_2}

            {cat}

            mkdir -p {out_dir}
            {s[opt][fastqc]} \
            --threads {self.cpu_req} \
            --dir {s[gk][tmp_dir]} \
            -o {out_dir} \
            {r1} {r2}

            rm -rf {fastqc_tmp_dir}
            """.format(s=s, **locals())