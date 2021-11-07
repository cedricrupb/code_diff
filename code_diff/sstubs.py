from enum import Enum

class SStubPattern(Enum):

    MULTI_STMT      = 0
    SINGLE_STMT     = 1


# SStub classification -------------------------------

def classify_sstub(source_ast, target_ast):
    pass