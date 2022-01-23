# Code Diff
------------------------------------------------
> Fast AST based code differencing in Python

Software projects are constantly evolving to integrate new features or improve existing implementations. To keep track of this progress, it becomes important to track individual code changes. Code differencing provides a way
to identify the smallest code change between two
implementations. 

**code.diff** provides a fast alternative to standard code differencing techniques with a focus
on AST based code differencing. As part of this library, we include a fast reimplementation of the [**GumTree**](https://github.com/GumTreeDiff/gumtree) algorithm. However, by relying on
a best-effort AST parser, we are able to generate
AST code changes for individual code snippets. Many
programming languages including Python, Java and JavaScript are supported!


## Installation
The package is tested under Python 3. It can be installed via:
```
pip install code-diff
```

## Usage
code.diff can compute a code difference for nearly any program code in a few lines of code:
```python
import code_diff as cd

# Python
output = cd.difference(
    '''
        def my_func():
            print("Hello World")
    ''',
    '''
        def say_helloworld():
            print("Hello World")
    ''',
lang = "python")

# Output: my_func -> say_helloworld

output.edit_script()

# Output: 
# [
#  Update((identifier:my_func, line 1:12 - 1:19), say_helloworld)
#]


# Java
output = cd.difference(
    '''
        int x = x + 1;
    ''',
    '''
        int x = x / 2;
    ''',
lang = "java")

# Output: x + 1 -> x / 2

output.edit_script()

# Output: [
#  Insert(/:/, (binary_operator, line 0:4 - 0:9), 1),
#  Update((integer:1, line 0:8 - 0:9), 2),
#  Delete((+:+, line 0:6 - 0:7))
#]


```
## Language support
code.diff supports most programming languages
where an AST can be computed. To parse an AST,
the underlying parser employs
* [**code.tokenize:**](https://github.com/cedricrupb/code_tokenize) A frontend for 
tree-sitter to effectively parse and tokenize 
program code in Python.

* [**tree-sitter:**](https://tree-sitter.github.io/tree-sitter/) A best-effort AST parser supporting
many programming languages including Python, Java and JavaScript.

To decide whether your code can be handled by code.diff please review the libraries above.

**GumTree:** To compute an edit script between a source and target AST, we employ a Python reimplementation of the [GumTree](https://github.com/GumTreeDiff/gumtree) algorithm. Note however that the computed script are heavily dependent on the AST representation of the given code. Therefore, AST edit script computed with code.diff might significantly differ to the one computed by GumTree.


## Release history
* 0.1.0
    * Initial functionality
    * Documentation
    * SStuB Testing

## Project Info
The goal of this project is to provide developer with easy access to AST-based code differencing. This is currently developed as a helper library for internal research projects. Therefore, it will only be updated as needed.

Feel free to open an issue if anything unexpected
happens. 

[Cedric Richter](https://uol.de/informatik/formale-methoden/team/cedric-richter) - [@cedricrupb](https://twitter.com/cedricrupb) - cedric.richter@uni-oldenburg.de

Distributed under the MIT license. See ``LICENSE`` for more information.


