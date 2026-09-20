# From Source Text to Tokens

A compiler usually begins by grouping characters into tokens. A token has a category, such as `NUMBER`, `IDENTIFIER`, or `PLUS`, and may preserve the original spelling as its lexeme.

For the input `total + 42`, a lexer might emit `IDENTIFIER("total")`, `PLUS("+")`, and `NUMBER("42")`.

The lexer should prefer the longest valid match when token rules overlap. Whitespace is commonly discarded, but its source position can still be recorded for diagnostics.

