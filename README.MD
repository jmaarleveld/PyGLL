# PyGLL - A GLL Parser Generator for Modern Python

---

## Content 

- [Project Introduction](#project-introduction)

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
metaprogramming language:

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