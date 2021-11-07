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

