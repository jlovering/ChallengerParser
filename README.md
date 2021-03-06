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
    }}
    [[
        [str None]
    ]]
```

## Parser language
The parser treats input as two groups: things that are multiple lines, and things that are single lines. Therefore the parser has 'builders' which operate over multiple lines, and 'blocks' which operate on single lines.

There can be multiple top level builders, builder output will be returned in a list.

### Builders
There are 3 types of builder: ListBuilder, DictBuilder (called 'hash' in the code because Perl), and MultiBuilder (a special builder that can group multiple builders). The code has a forth builder, the SingleLineBuilder which is used to operate on single lines.

By default builders parse until they hit a blank line

Notation notes:
    * Optional parameters are denoted by '<>' as this is not part of the language notation.
    * The '/' for callback functions is required
    * '|' is used to indicate 'or'

#### ListBuilder
Notation:
```
    [[
        ...
    ]] <optional end of section indicator> </ optional callback function>
```

ListBuilder can contain exactly 1 block.

ListBuilder will consume lines and parse according to its contained block.

List builder returns a list of what its blocks returned.

#### DictBuilder
Notation:
```
    {{
        ...
    }} <optional end of section indicator> </ optional callback function>
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
    )) <optional end of section indicator> </ optional callback function>
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
    [ parsingFunction seperator|None </ optional callback function> ]
```

The ListBlock will parse the line into a list according to the seperator provided (must be in quotes). If a 'None' is provided, then the list will be spilt per character. As with LiteralBlock, the provided parsing function will be called and value returned placed in the list.

#### SetBlock
Notation:
```
    [< parsingFunction seperator|None </ optional callback function> ]
```

(note that `[<` is the marker for the SetBlock)

SetBlock is identical to ListBlock but returns a set rather than list (helpful
for set operations)

#### GreedyListBlock
Notation:
```
    [* parsingFunction elementAcceptor seperator|None </ optional callback function> ]
```

The GreedListBlock will take items seperated using the sperator and call the 'elementAcceptor' function (which must be added with 'addFunction' (see below). The 'elementAcceptor' must return as follows:
`GACCEPT` Accept the current value.
`GREJECT` Reject the current value, this will throw away the first character and start again. It signals the parser that no acceptable value is possible (i.e. if values must start with a certain value).
`GCONTINUE` Add another value and test again.
Canidate values will have the parsing function applied before being passed to the elementAcceptor, and as with others, the parsing function will be applied to the value before placing in the returned list.

#### DictPairBlock
Notation:
```
    { [rev] keyParsingFunction|block valueParsingFunction|block seperator </ optional callback function> }
```

The DictPairBlock will first seperate the line according to the seperator. It will then parse the first value as the key and the second value as the value for the key/value pair (if the optional 'rev' flag is provided, the key and value parsers will be flipped and assumed flipped in the input). If a block notation is provided (rather than a parsing function) that key/value will be provide as input to that block and parsed according to that blocks rules, the resulting structure will be used as the key/value.

#### DictLineBlock
Notation:
```
    {* [rev] keyParsingFunction|block valueParsingFunction|block kvSeperator itemSeperator </ optional callback function> }
```

The DictLineBlock will first seperate the line according to the item seperator, it will then apply the same rules as DictPairBlock using the remaining arguments.

#### DistributingDictBlock
Notation:
```
    {< [rev] keyParsingFunction|block valueParsingFunction|block seperator </ optional callback function> }
```

(note that `{<` is the marker for the DistributingDictBlock)

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
    ( block block block... seperator </ optional callback function> )
```

The Multiblock will seperate the line according to seperator, and then apply each block in turn.

### Custom Functions
Because the functions are resolved inside the parsing library, any function desired needs to be provided using the addFunction call to the InputDefinition class (see below).

Custom functions are used for parsers, and massaging of values. The return of the custom function is added directly into the data structure.

Additionally, custom functions can be passed as special 'callback' functions. These are called once the block completes with the block's complete data structure. The return from this function will be treated as the blocks output. This is intended to perform secondary indexing on the structure (i.e. if you need the reverse of the dictionary, or some iterative composition).

The expected function prototype is therefore:
```python
def function(value):
    ...
    return valueTransformed
```

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
        # endTrim #
    ]]
))''')

thisParser = parser.Input(infile, definition)
data = thisParser.parse()
```

This creates a multibuilder (a builder that can containe multiple sub-builders) which are called in turn. The multibuilder contains 2 elements, a literal that is not parsed (is thrown away), and a list builder. The sub-list builder parses a literal calling the `endTrim` function for the value parsed off each line.

Since the internal list builder is the only element, by convention the one element list is exploded. So an example of the resulting data structure is: `[567, 119, 820]`

### More Complicated Example
```python
import ChallengerParser as parser

composedSetMap = {}
composedKeysCount = {}

def composeSetMap(h):
    for k in h:
        if k in composedSetMap:
            composedSetMap[k] = composedSetMap[k].intersection(h[k])
        else:
            composedSetMap[k] = h[k]
    return h

def composeKeyCount(l):
    for v in l:
        if v in composedKeysCount:
            composedKeysCount[v] += 1
        else:
            composedKeysCount[v] = 1
    return l

definition = parser.InputDefinition()
definition.addFunction('endTrim', lambda s: s[:-1])
definition.addFunction('composeSetMap', composeSetMap)
definition.addFunction('composeKeyCount', composeKeyCount)
definition.buildersFromStr('''[[
        {< rev [<str ' '] >[str ', ' / composeKeyCount] endTrim< ' (contains ' / composeSetMap }
    ]]''')

infile = open("file", "r")
thisParser = parser.Input(infile, definition)
data = thisParser.parse()
```

In this example the primary builder is a list builder. For each line it calles a distributed dict. This element parses key/value pairs which are seperated by ' (contains '. The distributed dict requires the key to be a list, and the values are duplicated onto every key. This distributed dict is given the 'rev' flag, indicating that the values occur first, then the keys. The keys are processed by calling the `endTrim` function on the list before it is seperated.
Two callback functions are given. The first "composeKeyCount" is called on the parsed keys list. In this case it counts the occurances of different keys over all dicts. A second callback "composeSetMap" is called on each completed dictionary. It applies a set intersection of the key value pairs for every key (essentially the intersection over all keys).

An example of the resulting data structure is:
`[{'dairy': {'mxmxvkd', 'kfcds', 'nhms', 'sqjhc'}, 'fish': {'mxmxvkd', 'kfcds', 'nhms', 'sqjhc'}}, {'dairy': {'trh', 'fvjkl', 'sbzzf', 'mxmxvkd'}}, {'soy': {'fvjkl', 'sqjhc'}}, {'fish': {'sbzzf', 'mxmxvkd', 'sqjhc'}}]`

And the secondary structures "composedSetMap" and "composedKeysCount" are:
`{'dairy': {'mxmxvkd'}, 'fish': {'sqjhc', 'mxmxvkd'}, 'soy': {'fvjkl', 'sqjhc'}}`
and:
`{'dairy': 2, 'fish': 2, 'soy': 1}`

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