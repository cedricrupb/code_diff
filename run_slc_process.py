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
from code_diff.gumtree    import json_serialize, json_deserialize

def load_slcs_from_tar(tar_files):

    for tar_file in tar_files:
        tar = tarfile.open(tar_file, "r:gz")

        try:
            for tarinfo in tar:
                if not tarinfo.isfile(): continue
                with tar.extractfile(tarinfo) as lines:
                    for line in lines:
                        yield json.loads(line.decode("utf-8"))  
        finally:
            tar.close()

         


def create_output(slc, hunk, **kwargs):  

    diff_message = str(hunk)

    assert len(diff_message) > 0 and len(diff_message.splitlines()) > 0

    output = {
        "project": slc["project"],
        "commit_sha": slc["commit_sha"],
        "parent_sha": slc["parent_sha"],
        "file_path": slc["file_path"],
        "project_url": slc["project_url"],

        "likely_bug": slc["likely_bug"],
        "comodified": slc["comodified"],
        "in_function": slc["in_function"],
        
        "diff": diff_message,
    }

    output.update(kwargs)
    return output


def _increase_ast_size(diff, current_level):

    if current_level == 0:
        try:
            return diff.statement_diff()
        except Exception:
            return diff
        
    if current_level == 1:
        return diff.root_diff()

    if current_level > 1: return diff


def _is_ghost_script(script):
    if script is None: return True
    if len(script) == 0: return False

    return hasattr(script[0].target_node, "node_id")


def compute_edit_script_it(diff):
    # For efficiency, we donnot compute the edit script for the full AST
    # This works in most cases. However this sometimes fails
    # We can detect that it fails, when ghost nodes appear in the edit script
    # In this case, we increase the AST size and recompute the edit script

    edit_script = None
    diff_level  = 0

    while diff_level < 3:
        edit_script = diff.edit_script()

        if not _is_ghost_script(edit_script): return edit_script
        
        diff = _increase_ast_size(diff, diff_level)
        diff_level += 1

    return edit_script # Return most precise edit script (even if it has ghost nodes)



def process_hunk(slc, hunk):
    
    # Generate diff
    try:
        diff = cd.difference(hunk.before, hunk.after, lang = "python")
    except Exception:
        return None
    
    # Process diff

    sstub_pattern = diff.sstub_pattern()
    edit_script = compute_edit_script_it(diff)

    try:
        stmt_diff = diff.statement_diff()
        before_diff = stmt_diff.source_text
        after_diff  = stmt_diff.target_text
    except ValueError:
        before_diff = diff.source_text
        after_diff  = diff.target_text

    edit_script_json = json_serialize(edit_script)

    return create_output(slc, hunk,
                            before = before_diff,
                            after  = after_diff,
                            sstub_pattern = sstub_pattern.name,
                            edit_script   = edit_script_json)


def process_slc(slc):
    
    diff_message = slc["diff"]
    diff_hunks   = parse_hunks(diff_message)

    outputs = []
    for hunk in diff_hunks:
        hunk = clean_hunk(hunk)
        output = process_hunk(slc, hunk)
        if output is not None: outputs.append(output)
        
    return outputs
    

def try_process_slc(slc):
    try:
        return process_slc(slc)
    except Exception as e:
        print(e)
        print(slc["diff"])
        raise
        return []

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

        file_path = os.path.join(self.save_dir, "file-%d.jsonl.gz" % self.file_count)

        if self.file_handler is not None: self.file_handler.close()

        self.file_handler = gzip.open(file_path, "wb")
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

    if cpu_count <= 4: # Too few CPUs for multiprocessing
        for output in map(map_fn, data):
            yield output

    with mp.Pool(processes = cpu_count) as pool:
        for output in pool.imap_unordered(map_fn, data, chunksize = 4 * cpu_count):
            yield output


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")

    args = parser.parse_args()

    tar_files = glob(os.path.join(args.input_dir, "*.tar.gz"))

    slc_saver = JsonlGzSaver(args.output_dir)

    try:

        process_map = pmap(try_process_slc, load_slcs_from_tar(tar_files))
    
        for output_hunks in tqdm(process_map, total = 66e6):
            for output in output_hunks:
                if output is None: continue
                slc_saver.save(output)
        
    finally:
        slc_saver.close()



if __name__ == '__main__':
    main()