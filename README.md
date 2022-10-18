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
close to the (pseudo-)code encountered in scientific papers. 
The aim of this project is to provide a clear example of how 
to implement the algorithm. The following sources were used
as a basis for the implementation:

- _B.C.M. Cappers - Exploring and visualizing GLL parsing. https://pure.tue.nl/ws/files/46987757/782897-1.pdf_ 
- _Elizabeth Scott, Adrian Johnstone - Structuring the GLL parsing algorithm for performance. https://www.sciencedirect.com/science/article/pii/S016764231630003X_
- _Afroozeh, A., Izmaylova, A. (2015). Faster, Practical GLL Parsing. https://link.springer.com/chapter/10.1007/978-3-662-46663-6_5_ 

The second goal of this project is to implement an
easy-to-use parser generator which allows the use 
of modern Python features, in particular the new `match` statement.

Additionally, the purpose of this project is to be educational.
The aim is to show how to implement a basic version of the GLL parsing 
algorithm, while also building basis disambiguation features on top 
of it. 

The syntax for declaring grammars is borrowed from the `Rascal`
metaprogramming language.

---

## TODOS

- [ ] Implement conversion of rascal-style grammar definitions to context free grammars
  - [x] Implement precede/not precede checks 
  - [x] Implement follow/not follow checks 
    - [x] Implement follow/not follow for terminals 
    - [x] Implement follow/not follow for nonterminals
  - [ ] Implement restriction checks
  - [ ] Implement "inline choice"
  - [ ] Implement kleene star and related constructs
  - [ ] Implement parametrized nonterminals 
  - [ ] Complete this list
- [ ] Refactor `IntermediateNode` and `IntermediateNodeKey` to no longer have the `is_nonterminal` field.
  This field should be moved to the `GrammarSlot` class.
- [x] Clean up debugging code 
- [ ] Implement automatic CST node generation with support for pattern matching
- [ ] Implement conversion of parse trees to CST nodes defined in the rascal-style grammar 
  - The parser uses generic `{Packed,Terminal,Intermediate}Node`s. 
    These have to be converted to the generated CST nodes to enable pattern matching.
- [ ] Implement concrete syntax matching 
- [x] Rework code generator to be more language agnostic.
- [ ] Implement C and Cython accelerator modules
- [ ] Think about automatic AST node generation
  - We can generate default nodes by only storing named symbols in rules, 
    and dropping all other information.
- [ ] Improve documentation
- [ ] Write tests
