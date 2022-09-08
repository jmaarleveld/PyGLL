# PyGLL - A GLL Parser Generator for Modern Python

---

## Content 

- [Project Introduction](#project-introduction)
- [TODOs](#todos)

---

## Project Introduction

This project aims to implement the object-oriented GLL (OOGLL)
algorithm for generating GLL parsers.

The main goal is to have an understandable implementation, which is 
close to the (pseudo-)code encountered in scientific paper. 
The aim of this project is to provide a clear example of how 
to implement the algorithm. The following two sources were used
as a basis for the implementation:

- _B.C.M. Cappers - Exploring and visualizing GLL parsing. https://pure.tue.nl/ws/files/46987757/782897-1.pdf_ 
- _Elizabeth Scott, Adrian Johnstone - Structuring the GLL parsing algorithm for performance. https://www.sciencedirect.com/science/article/pii/S016764231630003X_

The second goal of this project is to implement an
easy-to-use parser generator which allows the use 
of modern Python features, in particular the new `match` statement.

The syntax for declaring grammars is borrowed from the `Rascal`
metaprogramming language.

---

## TODOS

- Implement conversion of rascal-style grammar definitions to context free grammars 
  - Disambiguation, kleene star, named nodes etc. are additional abstractions which 
    are not part of normal context free grammars. They have to be somehow implemented.
    Some will be implemented when generating the context free grammar (e.g. kleene star),
    while others will be implemented by running after parsing (e.g. disambiguation)
- Implement automatic CST node generation
  - With support for pattern matching
- Implement conversion of parse trees to CST nodes defined in the rascal-style grammar 
  - The parser uses generic `{Packed,Terminal,Intermediate}Node`s. 
    These have to be converted to the generated CST nodes to enable pattern matching.
- Implement concrete syntax matching 
- Rework code generator to be more language agnostic. 
  - Idea: rework `AbstractCodeGenerator` to have specific functions for generating
            parsers, parsing methods, and GOTOs, all based on some "schema" which
            can be passed to the methods. 
            The goal is to move away from code/line level code generation, and move
            to a move abstract implementation -- this should make generating 
            C or Cython code easier.
- Implement C and Cython accelerator modules
- Think about automatic AST node generation
  - We can generate default nodes by only storing named symbols in rules, 
    and dropping all other information.
- Improve documentation
- Write tests

---

## Rascal Syntax and Constructs

1) Rascal - SyntaxDefinition
https://tutor.rascal-mpl.org/Rascal/Declarations/SyntaxDefinition/SyntaxDefinition.html
2) Rascal - Symbol
https://tutor.rascal-mpl.org/Rascal/Declarations/SyntaxDefinition/Symbol/Symbol.html
3) Rascal - Prefer/Avoid
https://github.com/usethesource/rascal/blob/main/src/org/rascalmpl/library/lang/sdf2/filters/PreferAvoid.rsc
4) Rascal - Follow
https://tutor.rascal-mpl.org/Rascal/Declarations/SyntaxDefinition/Disambiguation/Follow/Follow.html
5) Rascal - Precede
https://tutor.rascal-mpl.org/Rascal/Declarations/SyntaxDefinition/Disambiguation/Precede/Precede.html
6) Rascal - Reserve
https://tutor.rascal-mpl.org/Rascal/Declarations/SyntaxDefinition/Disambiguation/Disambiguation.html#/Rascal/Declarations/SyntaxDefinition/Disambiguation/Reserve/Reserve.html
7) Rascal - Priority
https://tutor.rascal-mpl.org/Rascal/Declarations/SyntaxDefinition/Disambiguation/Priority/Priority.html
8) Rascal - Associativity
https://tutor.rascal-mpl.org/Rascal/Declarations/SyntaxDefinition/Disambiguation/Disambiguation.html#/Rascal/Declarations/SyntaxDefinition/Disambiguation/Associativity/Associativity.html