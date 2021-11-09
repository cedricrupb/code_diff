import re


# Diff parsing -----------------------------------------------------------------

class Hunk:
    
    def __init__(self, lines, added_lines, rm_lines):
        self.lines       = lines
        self.added_lines = set(added_lines)
        self.rm_lines    = set(rm_lines)
        
        
    @property
    def after(self):
        
        alines = []
        
        for i, line in enumerate(self.lines):
            if i in self.rm_lines: continue
            if i in self.added_lines:
                alines.append(" " + line[1:])
            else:
                alines.append(line)
                
        return "".join(alines)
        
        
    @property
    def before(self):
        
        alines = []
        
        for i, line in enumerate(self.lines):
            if i in self.added_lines: continue
            if i in self.rm_lines:
                alines.append(" " + line[1:])
            else:
                alines.append(line)
                
        return "".join(alines)
        
    def __repr__(self):
        return "".join(self.lines)

    
def _parse_hunk(lines, start, end):
    
    hunk_lines = lines[start + 1:end]
     
    added_lines = []
    rm_lines    = []
    
    for i, hline in enumerate(hunk_lines):
        if hline.startswith("+"): added_lines.append(i)
        if hline.startswith("-"): rm_lines.append(i)
    
    return Hunk(hunk_lines, added_lines, rm_lines)
    

hunk_pat = re.compile("@@ -(\d+)(,\d+)? \+(\d+)(,\d+)? @@.*")
        
def parse_hunks(diff):
    lines = diff.splitlines(True)
    
    hunks = []
    
    start_ix = -1
    end_ix   = -1
    
    for line_ix, line in enumerate(lines):
        
        if hunk_pat.match(line):
            
            end_ix = line_ix - 1
            
            if start_ix >= 0 and start_ix < end_ix: 
                hunks.append(_parse_hunk(lines, start_ix, end_ix))
            
            start_ix = line_ix
    
    end_ix = len(lines)
    
    if start_ix >= 0 and start_ix < end_ix: 
        hunks.append(_parse_hunk(lines, start_ix, end_ix))
                
    return hunks


# Diff cleaning --------------------------------

def _has_incomplete_comment(lines):
    is_incomplete2 = False
    is_incomplete1 = False

    for line in lines:
        count2 = line.count("\"\"\"")
        if count2 % 2 == 1: is_incomplete2 = not is_incomplete2
        
        count1 = line.count("\'\'\'")
        if count1 % 2 == 1: is_incomplete1 = not is_incomplete1

    return is_incomplete1 or is_incomplete2


def _determine_incomplete_comment(lines):
    last_incomplete2 = -1
    last_incomplete1 = -1

    for i, line in enumerate(lines):
        count2 = line.count("\"\"\"")
        if count2 % 2 == 1:
            last_incomplete2 = i if last_incomplete2 == -1 else -1
        
        count1 = line.count("\'\'\'")
        if count1 % 2 == 1:
            last_incomplete1 = i if last_incomplete1 == -1 else -1

    assert last_incomplete1 != -1 or last_incomplete2 != -1

    last_incomplete = last_incomplete2 if last_incomplete2 != -1 else last_incomplete1

    dist_to_end = len(lines) - last_incomplete

    if last_incomplete < dist_to_end:
        return last_incomplete + 1, len(lines)
    else:
        return 0, last_incomplete


def clean_hunk(hunk):
    if not _has_incomplete_comment(hunk.lines): return hunk
    start, end = _determine_incomplete_comment(hunk.lines)

    new_lines = hunk.lines[start:end]
    added_lines = [l - start for l in hunk.added_lines if l >= start and l < end]
    rm_lines    = [l - start for l in hunk.rm_lines if l >= start and l < end]

    return Hunk(new_lines, added_lines, rm_lines)

