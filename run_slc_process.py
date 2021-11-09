import os
import argparse
import tarfile
import json
import gzip

from glob import glob
from tqdm import tqdm

import multiprocessing as mp

import code_diff as cd
from code_diff.diff_utils import parse_hunks, clean_hunk

def load_slcs_from_tar(tar_files):

    for tar_file in tar_files:
        tar = tarfile.open(tar_file, "r:gz")

        for tarinfo in tar:
            if not tarinfo.isfile(): continue
            with tar.extractfile(tarinfo) as lines:
                for line in lines:
                    yield json.loads(line.decode("utf-8"))   


def create_output(slc, **kwargs):  

    output = {
        "project": slc["project"],
        "commit_sha": slc["commit_sha"],
        "parent_sha": slc["parent_sha"],
        "file_path": slc["file_path"],
        "project_url": slc["project_url"],

        "likely_bug": slc["likely_bug"],
        "comodified": slc["comodified"],
        "in_function": slc["in_function"],
        
        "diff": slc["diff"],
    }

    output.update(kwargs)
    return output


def process_slc(slc):
    
    diff_message = slc["diff"]
    diff_hunks   = parse_hunks(diff_message)

    diff_candidates = []
    for hunk in diff_hunks:
        hunk = clean_hunk(hunk)

        try:
            diff = cd.difference(hunk.before, hunk.after, lang = "python")
            diff_candidates.append(diff)
        except ValueError:
            continue
    
    if len(diff_candidates) != 1: return None

    source_diff = diff_candidates[0]

    sstub_pattern = source_diff.sstub_pattern().name
    edit_script   = str(source_diff.edit_script())

    try:
        statement_diff = source_diff.statement_diff()
        before = statement_diff.source_text
        after  = statement_diff.target_text
    except ValueError:
        before = source_diff.source_text
        after  = source_diff.target_text

    return create_output(slc,
                            before = before,
                            after  = after, 
                            sstub_pattern = sstub_pattern, 
                            edit_script = edit_script)


# Save to jsonl.gz

class JsonlGzSaver:

    def __init__(self, save_dir, num_objects = 1e5):
        self.save_dir = save_dir
        self.num_objects = num_objects
        
        self.object_count = 0
        self.file_count   = 0

        self.file_handler = None
        self._update_handler()

    def _update_handler(self):
        
        need_update = self.file_handler is None or self.object_count >= self.num_objects
        if not need_update: return

        file_path = os.path.join(self.save_dir, "file-%d.jsonl" % self.file_count)

        if self.file_handler is not None: self.file_handler.close()

        self.file_handler = open(file_path, "wb")
        self.file_count += 1
        self.object_count = 0

    def save(self, obj):
        json_obj = json.dumps(obj) + "\n"
        self.file_handler.write(json_obj.encode("utf-8"))
        self.object_count += 1
        self._update_handler()

    def close(self):
        if self.file_handler is not None:
            self.file_handler.close()
        self.file_handler = None

# Multiprocessing --------------------------------

def pmap(map_fn, data):

    cpu_count = mp.cpu_count()

    if cpu_count <= 4: # To few CPUs for multiprocessing
        for output in map(map_fn, data):
            yield output

    with mp.Pool(processes = cpu_count) as pool:
        for output in pool.imap_unordered(map_fn, data):
            yield output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")

    args = parser.parse_args()

    tar_files = glob(os.path.join(args.input_dir, "*.tar.gz"))

    slc_saver = JsonlGzSaver(args.output_dir)

    try:
        process_map = pmap(process_slc, load_slcs_from_tar(tar_files))
        for output in tqdm(process_map, total = 66e6):
            if output is None: continue
            slc_saver.save(output)
    finally:
        slc_saver.close()


if __name__ == '__main__':
    main()