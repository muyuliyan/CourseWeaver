# Parsing Expressions

A parser turns a token sequence into structure. Precedence determines which operator binds more tightly, while associativity resolves repeated operators at the same precedence level.

For `1 + 2 * 3`, multiplication binds more tightly than addition, so the tree represents `1 + (2 * 3)`. A recursive-descent parser can encode this by giving each precedence level its own function.

Useful parser errors report the unexpected token, its source location, and a small set of expected token categories.

