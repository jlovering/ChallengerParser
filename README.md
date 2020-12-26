# Challenger Parser

    requirements: TatSu==5.5.0

Challenger parser is designed to simplify parsing programming callenge input.
This is a python version loosly based on https://github.com/furstenheim/challenger
However, this version features a PEG parser that can consume a string representation
of the required parser. This is the recommended way to use the parser.

## Rational
At their core contest questions present 3 different kinds of input:
literals,
lists,
dictionaries

For example Advent of Code 2020 featured simple formats:
```
    0,3,6
```

And more complex:
```
    0: 4 1 5
    1: 2 3 | 3 2
    2: 4 4 | 5 5
    3: 4 5 | 5 4
    4: "a"
    5: "b"

    ababbb
    bababa
    abbbab
    aaabbb
    aaaabbb
```

Though the former is easy to formulate a parser for:
```python
    return infile.readline().rstrip().split(',')
```
(given an open file infile)
Even that requires a number of key words.

The later example requires far more work.

By contrast, the two preceeding examples can be expressed to Challenger as follows:
```
    [#int#]
```

and:
```
    {{
        {int ([int ' '] or #quoteTrim#   [int ' '] ' | ') ': '}
    }
    [[
        [str None]
    ]
```

## Parser language
The parser treats input as two groups: things that are multiple lines, and things that are single lines. Therefore the parser has 'builders' which operate over multiple lines, and 'blocks' which operate on single lines.

There can be multiple top level builders, builder output will be returned in a list.

### Builders
There are 3 types of builder: ListBuilder, DictBuilder (called 'hash' in the code because Perl), and MultiBuilder (a special builder that can group multiple builders). The code has a forth builder, the SingleLineBuilder which is used to operate on single lines.

By default builders parse until they hit a blank line

#### ListBuilder
Notation:
```
    [[
        ...
    ] <optional end of section indicator>
```

ListBuilder can contain exactly 1 block.

ListBuilder will consume lines and parse according to its contained block.

List builder returns a list of what its blocks returned.

#### DictBuilder
Notation:
```
    {{
        ...
    } <optional end of section indicator>
```

DictBuilder can contain exactly 1 Dict type block:
* DictPairBlock
* DictLineBlock
* DistributingDictBlock

DictBuilder will consume lines and parse according to its contained block.

DictBuildeer returns a dictionary composed of all the dictionaries generated within (i.e. dictionaries will not be nested)

#### MultiBuilder
Notation:
```
    ((
        ...
    ) <optional end of section indicator>
```

MultiBuilder can contain multiple builders/blocks. MultiBuilder will consume lines passing them to each contained block sequentailly. If a block is a builder it will consume until termination and MultiBuilder will continue from where it stopped with the next block.

MultiBuilder returns a list of the outputs from the attached blocks

### Blocks
There are 7 types of blocks parsing block and 3 utility types. Each block consumes a single line of input and returns data to it's parent builder.

#### LiteralBlock
Notation:
```
    # <optional parsing function | quoted literal to match> #
```

The LiteralBlock parses a value. If called with no options, the literal will be discarded. If a parsing function is provided then the literal will be passed to the function and the resulting value returned. Functions beyond built in 'int' and 'str' must be provided to the parser (see below). If a quoted string is provided then an exact match must be found, if the string does not match the parser will throw an exception.

#### ListBlock
Notation:
```
    [ parsingFunction seperator|None ]
```

The ListBlock will parse the line into a list according to the seperator provided (must be in quotes). If a 'None' is provided, then the list will be spilt per character. As with LiteralBlock, the provided parsing function will be called and value returned placed in the list.

#### SetBlock
Notation:
```
    [< parsingFunction seperator|None ]
```

SetBlock is identical to ListBlock but returns a set rather than list (helpful
for set operations)

#### GreedyListBlock
Notation:
```
    [* parsingFunction [inputlist] seperator|None ]
```

The GreedListBlock will parse items in the inputlist into a list. i.e. a value must appear in the inputlist to be parsed. It will consume as many characters as needed to achieve a match. As with others, the parsing function will be applied to the value before placing in the returned list.

#### DictPairBlock
Notation:
```
    { keyParsingFunction|block valueParsingFunction|block seperator}
```

The DictPairBlock will first seperate the line according to the seperator. It will then parse the first value as the key and the second value as the value for the key/value pair. If a block notation is provided (rather than a parsing function) that key/value will be provide as input to that block and parsed according to that blocks rules, the resulting structure will be used as the key/value.

#### DictLineBlock
Notation:
```
    {* keyParsingFunction|block valueParsingFunction|block kvSeperator itemSeperator}
```

The DictLineBlock will first seperate the line according to the item seperator, it will then apply the same ruls as DictPairBlock using the remaining arguments.

#### DistributingDictBlock
Notation:
```
    {< keyParsingFunction|block valueParsingFunction|block seperator}
```

This is a special varient of the DictPairBlock. It is not well tested. This block requires that key resolves to a list, it will then iterate the key list and create entries for each key with the entire output of value.

#### OrBlock
Notation:
```
    block or block
```

If an OrBlock is provided it will attempt to call each parser returning the first value which matches. Although implemented for 'n' ors, it's not clear more than 2 will work.

#### EncapsulationBlock
Notation:
```
    > block modifyingFunction <
```

The EncapsualationBlock will apply the modifying function to the input before passing it to the underlying block

#### MultiBlock
Notation:
```
    ( block block block... seperator)
```

The Multiblock will seperate the line according to seperator, and then apply each block in turn.

## Usage
### Example
```python
import ChallengerParser as parser

infile = open("file", "r")

defintion = parser.InputDefinition()
definition.addFunction('endTrim', lambda s: s[:-1])
definition.buildersFromStr('''((
    ##
    [[
        # endTrim#
    ]
)''')

thisParser = parser.Input(infile, definition)
data = thisParser.parse()
```

### API
#### InputDefinition
Class that defined the block structure
##### __init__()
No arguments
##### addBuilder(builder)
If used manually, adds a toplevel builder to the InputDefinition (not recommended)
##### addFunction(name, function)
Adds a function that can be called within the parser. By default the parser understands 'int' and 'str'. All other functions must be added.
##### buildersFromStr(string)
Use a parser notation to construct the appropriate definition. This is the recommended useage.
#### Input
The Input class performs the input parsing
##### __init__(infile, definition)
Takes an open file handle and a constructed defintion
##### parse()
Execute the parse, returns the resulting data structure.

## Limitation:
* I don't know what I don't know. This parsers might be completely unable to handle certain types of input
* Dict pairs can't be reversed in the notation (the block itself supports a reverse flag)