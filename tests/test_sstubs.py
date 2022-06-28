import code_diff as cd

from code_diff.diff_utils import parse_hunks
from code_diff import SStubPattern

# Util --------------------------------------------------------------

def compute_diff_sstub(diff):
    hunks = parse_hunks(diff)
    hunk  = hunks[0]
    diff  = cd.difference(hunk.before, hunk.after, lang = "python")
    return diff.sstub_pattern()



# Wrong Function name ----------------------------------------------

def test_wrong_function_name_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- test()
+ test2()
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.WRONG_FUNCTION_NAME


def test_wrong_function_name_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- test.call()
+ test.call_async()
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.WRONG_FUNCTION_NAME


def test_wrong_function_name_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- test.call_async('Hello World', x, x / 2)
+ test.call('Hello World', x, x / 2)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.WRONG_FUNCTION_NAME


def test_wrong_function_name_4():

    test = """
@@ -0,0 +0,0 @@ test
    
- test_call.call('Hello World', x, x / 2)
+ test.call('Hello World', x, x / 2)
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.WRONG_FUNCTION_NAME


def test_wrong_function_name_5():

    test = """
@@ -0,0 +0,0 @@ test
    
- test.x.call('Hello World', x, x / 2)
+ test.y.call('Hello World', x, x / 2)
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.WRONG_FUNCTION_NAME



# Same Function more args -------------------------------------------

def test_same_function_more_args_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- test()
+ test(x)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_MORE_ARGS


def test_same_function_more_args_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- test(x)
+ test(x, y)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_MORE_ARGS


def test_same_function_more_args_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- test(x, y)
+ test(x, y + 1)
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.SAME_FUNCTION_MORE_ARGS


def test_same_function_more_args_4():

    test = """
@@ -0,0 +0,0 @@ test
    
- test(x)
+ test(x, y + 1)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_MORE_ARGS


def test_same_function_more_args_5():

    test = """
@@ -0,0 +0,0 @@ test
    
- test(x + 1)
+ test(x, y + 1)
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.SAME_FUNCTION_MORE_ARGS


def test_same_function_more_args_6():

    test = """
@@ -0,0 +0,0 @@ test
    
- test.call(x)
+ test.call(x, y)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_MORE_ARGS


def test_same_function_more_args_7():

    test = """
@@ -0,0 +0,0 @@ test
    
- test.call(x)
+ test.call(x, y, z, d, a, call())
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_MORE_ARGS


def test_same_function_more_args_8():

    test = """
@@ -0,0 +0,0 @@ test
    
- test.call1(x)
+ test.call(x, y, z, d, a, call())
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.SAME_FUNCTION_MORE_ARGS

# Same Function less args -------------------------------------------

def test_same_function_less_args_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- test(x)
+ test()
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_LESS_ARGS


def test_same_function_less_args_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- test(x, y)
+ test(x)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_LESS_ARGS



def test_same_function_less_args_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- test(x, y + 1)
+ test(x, y)
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.SAME_FUNCTION_LESS_ARGS


def test_same_function_less_args_4():

    test = """
@@ -0,0 +0,0 @@ test
    
- test(x, y + 1)
+ test(x)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_LESS_ARGS


def test_same_function_less_args_5():

    test = """
@@ -0,0 +0,0 @@ test
    
- test(x, y + 1)
+ test(x + 1)
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.SAME_FUNCTION_LESS_ARGS


def test_same_function_less_args_6():

    test = """
@@ -0,0 +0,0 @@ test
    
- test.call(x, y)
+ test.call(x)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_LESS_ARGS


def test_same_function_less_args_7():

    test = """
@@ -0,0 +0,0 @@ test
    
- test.call(x, y, z, d, a, call())
+ test.call(x)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_LESS_ARGS

# Same Function wrong caller -------------------------------------------

def test_same_function_wrong_caller_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- test.call()
+ test1.call()
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_WRONG_CALLER


def test_same_function_wrong_caller_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- test.x.call()
+ test.y.call()
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.SAME_FUNCTION_WRONG_CALLER


def test_same_function_wrong_caller_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- call()
+ test.call()
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.SAME_FUNCTION_WRONG_CALLER


# Same Function swap args -------------------------------------------

def test_same_function_swap_args_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- test.call(x, y)
+ test.call(y, x)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_SWAP_ARGS


def test_same_function_swap_args_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- test.call1(x, y)
+ test.call(y, x)
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.SAME_FUNCTION_SWAP_ARGS


def test_same_function_swap_args_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- test.call(x, y, z)
+ test.call(y, x, z)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_SWAP_ARGS


def bin_swaps(x):
    for i in range(len(x) - 1):
        for j in range(i + 1, len(x)):
            result = list(x)
            result[i], result[j] = result[j], result[i]
            yield result


def test_same_function_swap_args_auto():

    args = ["a", "b", "c", "d + 1", "0 if a != 0 else 1"]

    for l in range(2, len(args)):
        perm = tuple(args[:l])

        for p in bin_swaps(perm):

            test = """
@@ -0,0 +0,0 @@ test
            
- test.call(%s)
+ test.call(%s)
            
            """ % (", ".join(perm), ", ".join(p))
            
            assert compute_diff_sstub(test) == SStubPattern.SAME_FUNCTION_SWAP_ARGS


# Add function around expression -------------------------------------------

def test_add_function_around_expression_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x
+ result = int(x)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_FUNCTION_AROUND_EXPRESSION


def test_add_function_around_expression_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x + 1
+ result = int(x) + 1
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_FUNCTION_AROUND_EXPRESSION


def test_add_function_around_expression_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x + 1
+ result = int(x + 1)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_FUNCTION_AROUND_EXPRESSION

# Add method call --------------------------------------------------------


def test_add_method_call_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x
+ result = x.get()
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_METHOD_CALL


def test_add_method_call_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x.get()
+ result = x.get().return()
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_METHOD_CALL


def test_add_method_call_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x.y
+ result = x.y.get()
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_METHOD_CALL


def test_add_method_call_4():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x.get()
+ result = x.return().get()
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_METHOD_CALL


def test_add_method_call_5():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x.get()
+ result = x.return.get()
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.ADD_METHOD_CALL



def test_add_method_call_6():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x.return().get()
+ result = x.get()
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.ADD_METHOD_CALL

# Change identifier --------------------------------------------------------

def test_change_identifier_used_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x
+ result = y
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_IDENTIFIER_USED


def test_change_identifier_used_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = test(path = path)
+ result = test(path = path2)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_IDENTIFIER_USED


def test_change_identifier_used_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = test(path = path)
+ result = test(path2 = path)
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.CHANGE_IDENTIFIER_USED


def test_change_identifier_used_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = test(path = path)
+ result = test2(path = path)
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.CHANGE_IDENTIFIER_USED


def test_change_identifier_used_4():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = test.x(a, b, c)
+ result = test1.x(a, b, c)
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.CHANGE_IDENTIFIER_USED


def test_change_identifier_used_5():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = test.x(a, b, c)
+ result1 = test.x(a, b, c)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_IDENTIFIER_USED


# Change numeric literal ----------------------------------------------------

def test_change_numeric_literal_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = 0
+ result = 1
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_NUMERIC_LITERAL


def test_change_numeric_literal_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x + 1
+ result = x + 5
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_NUMERIC_LITERAL


def test_change_numeric_literal_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x + 1
+ result = x + 5.0
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_NUMERIC_LITERAL


def test_change_numeric_literal_4():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x + 1
+ result = x + 1.0
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.CHANGE_NUMERIC_LITERAL


def test_change_numeric_literal_5():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x + 1
+ result = x + a
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.CHANGE_NUMERIC_LITERAL


# Change boolean literal ----------------------------------------------------

def test_change_boolean_literal_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- if True:
+ if False:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BOOLEAN_LITERAL


def test_change_boolean_literal_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- if True and x < 0:
+ if False and x < 0:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BOOLEAN_LITERAL


def test_change_boolean_literal_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- if False and x < 0:
+ if True and x < 0:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BOOLEAN_LITERAL


def test_change_boolean_literal_4():

    test = """
@@ -0,0 +0,0 @@ test
    
- if False and x < 0:
+ if x / 2 == 0 and x < 0:
    pass
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.CHANGE_BOOLEAN_LITERAL

# Change unary operator ----------------------------------------------------

def test_change_unary_operator_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x:
+ if not x:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_UNARY_OPERATOR


def test_change_unary_operator_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x
+ result = -x
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_UNARY_OPERATOR


def test_change_unary_operator_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = x
+ result = +x
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_UNARY_OPERATOR


def test_change_unary_operator_4():

    test = """
@@ -0,0 +0,0 @@ test
    
- if not x:
+ if x:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_UNARY_OPERATOR


def test_change_unary_operator_5():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = -x
+ result = x
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_UNARY_OPERATOR


def test_change_unary_operator_6():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = +x
+ result = x
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_UNARY_OPERATOR


def test_change_unary_operator_7():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x and y:
+ if not x and y:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_UNARY_OPERATOR


def test_change_unary_operator_8():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x and y:
+ if not (x and y):
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_UNARY_OPERATOR



# Change binary operator ----------------------------------------------------

def test_change_binary_operator_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x and y:
+ if x or y:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BINARY_OPERATOR


def test_change_binary_operator_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x or y:
+ if x and y:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BINARY_OPERATOR


def test_change_binary_operator_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x + y:
+ if x or y:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BINARY_OPERATOR


def test_change_binary_operator_4():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x and y:
+ if x - y:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BINARY_OPERATOR


def test_change_binary_operator_5():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x + y:
+ if x - y:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BINARY_OPERATOR


def test_change_binary_operator_6():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x + y:
+ if x % y:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BINARY_OPERATOR


def test_change_binary_operator_7():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x + y:
+ if x / y:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BINARY_OPERATOR


def test_change_binary_operator_8():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x + y < 5:
+ if x + y <= 5:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BINARY_OPERATOR


def test_change_binary_operator_9():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x + y < 5 and is_t:
+ if x + y <= 5 and is_t:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BINARY_OPERATOR


# Change binary operand -----------------------------------------------------


def test_change_binary_operand_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x and y:
+ if x and z:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BINARY_OPERAND


def test_change_binary_operand_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x and y:
+ if x and z <= 1:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BINARY_OPERAND


def test_change_binary_operand_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- if x and y:
+ if x > 8 and z <= 1:
    pass
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.CHANGE_BINARY_OPERAND


def test_change_binary_operand_4():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = result + graphA / 2
+ result = result + graphB / 2
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_BINARY_OPERAND



# Change attribute used ----------------------------------------------------------------


def test_change_attribute_used_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = person.name
+ result = person.age
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_ATTRIBUTE_USED


def test_change_attribute_used_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = (x + y).name
+ result = (x + y).age
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_ATTRIBUTE_USED


def test_change_attribute_used_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = person.name.name
+ result = person.age.age
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.CHANGE_ATTRIBUTE_USED


def test_change_attribute_used_4():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = person.name.name
+ result = person.age.name
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_ATTRIBUTE_USED



# Change keyword argument used ----------------------------------------------------------

def test_change_keyword_argument_used_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = Person(name = 5)
+ result = Person(age  = 5)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_KEYWORD_ARGUMENT_USED


def test_change_keyword_argument_used_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = Person(path = path)
+ result = Person(paths = path)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_KEYWORD_ARGUMENT_USED


def test_change_keyword_argument_used_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = Person(path = path)
+ result = Person(path = paths)
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.CHANGE_KEYWORD_ARGUMENT_USED


def test_change_keyword_argument_used_4():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = Person(path = path)
+ result = Person(path = path, path2 = path)
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.CHANGE_KEYWORD_ARGUMENT_USED


def test_change_keyword_argument_used_5():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = Person(path = path, path = path)
+ result = Person(path = path, path2 = path)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_KEYWORD_ARGUMENT_USED


def test_change_keyword_argument_used_6():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = Person(path2 = path, path = path)
+ result = Person(path = path, path2 = path)
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.CHANGE_KEYWORD_ARGUMENT_USED

# Change constant type used --------------------------------------------------------------

def test_change_constant_type_used_1():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = 3
+ result = 3.0
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_CONSTANT_TYPE


def test_change_constant_type_used_2():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = 3
+ result = 3.1
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.CHANGE_CONSTANT_TYPE


def test_change_constant_type_used_3():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = 3
+ result = '3'
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_CONSTANT_TYPE


def test_change_constant_type_used_4():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = "3"
+ result = '3'
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.CHANGE_CONSTANT_TYPE


def test_change_constant_type_used_5():

    test = """
@@ -0,0 +0,0 @@ test
    
- result = 3.0
+ result = '3'
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.CHANGE_CONSTANT_TYPE

# Add elements to iterable ----------------------------------------------------------------

def test_add_elements_to_iterable_1():
    test = """
@@ -0,0 +0,0 @@ test
    
- result = ()
+ result = (1,)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_ELEMENTS_TO_ITERABLE


def test_add_elements_to_iterable_2():
    test = """
@@ -0,0 +0,0 @@ test
    
- result = (1,)
+ result = (1,2,)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_ELEMENTS_TO_ITERABLE


def test_add_elements_to_iterable_3():
    test = """
@@ -0,0 +0,0 @@ test
    
- result = (1,)
+ result = (1,2, x + 1)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_ELEMENTS_TO_ITERABLE

def test_add_elements_to_iterable_4():
    test = """
@@ -0,0 +0,0 @@ test
    
- result = (1,)
+ result = (1,2, x + 1, fn())
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_ELEMENTS_TO_ITERABLE


def test_add_elements_to_iterable_5():
    test = """
@@ -0,0 +0,0 @@ test
    
- result = (1,)
+ result = [1,2, x + 1, fn()]
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.ADD_ELEMENTS_TO_ITERABLE


def test_add_elements_to_iterable_6():
    test = """
@@ -0,0 +0,0 @@ test
    
- result = [1,2,]
+ result = [1,2, x + 1, fn()]
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_ELEMENTS_TO_ITERABLE


def test_add_elements_to_iterable_7():
    test = """
@@ -0,0 +0,0 @@ test
    
- result = [1,2,]
+ result = [1, x + 1, fn(), 2]
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_ELEMENTS_TO_ITERABLE


def test_add_elements_to_iterable_8():
    test = """
@@ -0,0 +0,0 @@ test
    
- result = [1,2,]
+ result = [1, x + 1, fn()]
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.ADD_ELEMENTS_TO_ITERABLE


def test_add_elements_to_iterable_9():
    test = """
@@ -0,0 +0,0 @@ test
    
- result = {1,2,}
+ result = {1,2, x + 1, fn()}
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_ELEMENTS_TO_ITERABLE

# Add attribute access ---------------------------------------------------------------------

def test_add_attribute_access_1():
    test = """
@@ -0,0 +0,0 @@ test
    
- result = say_hello_to(person)
+ result = say_hello_to(person.name)
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_ATTRIBUTE_ACCESS


def test_add_attribute_access_2():
    test = """
@@ -0,0 +0,0 @@ test
    
- result = person.age
+ result = person.parent.age
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.ADD_ATTRIBUTE_ACCESS


# More specific if ------------------------------------------------------------------------

def test_more_specific_if_1():
    test = """
@@ -0,0 +0,0 @@ test
    
- if x:
+ if x and y:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.MORE_SPECIFIC_IF


def test_more_specific_if_2():
    test = """
@@ -0,0 +0,0 @@ test
    
- if isinstance(x):
+ if isinstance(x, y):
    pass
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.MORE_SPECIFIC_IF


def test_more_specific_if_3():
    test = """
@@ -0,0 +0,0 @@ test
    
- if x:
+ if not x:
    pass
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.MORE_SPECIFIC_IF


def test_more_specific_if_4():
    test = """
@@ -0,0 +0,0 @@ test
    
- if x and test():
+ if x and test() or test2():
    pass
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.MORE_SPECIFIC_IF

# Less specific if ------------------------------------------------------------------------

def test_less_specific_if_1():
    test = """
@@ -0,0 +0,0 @@ test
    
- if x:
+ if x or y:
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.LESS_SPECIFIC_IF


def test_less_specific_if_2():
    test = """
@@ -0,0 +0,0 @@ test
    
- if isinstance(x, y):
+ if isinstance(x):
    pass
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.LESS_SPECIFIC_IF


def test_less_specific_if_3():
    test = """
@@ -0,0 +0,0 @@ test
    
- if not x:
+ if x:
    pass
    
    """
    
    assert compute_diff_sstub(test) != SStubPattern.LESS_SPECIFIC_IF


def test_less_specific_if_4():
    test = """
@@ -0,0 +0,0 @@ test
    
- if x and test():
+ if x and test() or test2():
    pass
    
    """
    
    assert compute_diff_sstub(test) == SStubPattern.LESS_SPECIFIC_IF


# Real world tests ----------------------------------------------------------------

def test_real_world_1():

    test = """
@@ -16,7 +16,7 @@ def test_databases():
     bench2 = Benchmark(statement, setup, name='list with xrange',
         description='Xrange', start_date=datetime(2013, 3, 9))
 
-    dbHandler = BenchmarkDb.get_instance('bench.db')
+    dbHandler = BenchmarkDb('bench.db')
    """

    assert compute_diff_sstub(test) == SStubPattern.SINGLE_STMT



def test_real_world_2():

    test = """
@@ -146,7 +146,7 @@ class DatetimeWidget(DateWidget):
         if default in (year, month, day, hour, minute):
             return default

-        if self.ampm is True and hour != 12:
+        if self.ampm is True and int(hour)!=12:
             ampm = self.request.get(self.name + '-ampm', default)
             if ampm == 'PM':
                 hour = str(12+int(hour))
    """

    assert compute_diff_sstub(test) == SStubPattern.ADD_FUNCTION_AROUND_EXPRESSION


def test_real_world_3():

    test = """
@@ -59,7 +59,8 @@ class UrlRewriteFilter(object):
         if ext in CONTENT_TYPES:
             # Use the content type specified by the extension
             return (path, CONTENT_TYPES[ext])
-        elif http_accept is None:
+        elif http_accept is None or http_accept == '*/*':
+            # TODO: This probably isn't the best place to handle "Accept: */*"
             # No extension or Accept header specified, use default
             return (path_info, DEFAULT_CONTENT_TYPE)
         else:
    
    """

    assert compute_diff_sstub(test) == SStubPattern.LESS_SPECIFIC_IF