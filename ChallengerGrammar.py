GRAMMAR = '''
@@grammar::ChallengerParser

start
    =
    expression $
    ;

expression
    =
    block
    | builderstart
    | builderend
    ;

builderstart
    =
    | multibuilderstart
    | listbuilderstart
    | hashbuilderstart
    ;

builderend
    =
    | multibuilderend
    | listbuilderend
    | hashbuilderend
    ;

multibuilderstart
    =
    '(('
    ;

multibuilderend
    =
    ')' [quotedstring] ['/' functionName]
    ;

listbuilderstart
    =
    '[['
    ;

listbuilderend
    =
    ']' [quotedstring] ['/' functionName]
    ;

hashbuilderstart
    =
    '{{'
    ;

hashbuilderend
    =
    '}' [quotedstring] ['/' functionName]
    ;

quotedstring
    =
    |/\".*?\"/
    |/\'.*?\'/
    ;

none
    =
    'None'
    ;

block
    =
    | orblock
    | encapblock
    | literalblock
    | listblock
    | greedylistblock
    | setblock
    | hashpairblock
    | hashpairdistribute
    | hashlineblock
    | multiblock
    ;

orblock
    =
    'or'>{block}+
    ;

encapblock
    =
    '>' block functionName '<'
    ;

hashableencapblock
    =
    '>' hashableblock functionName '<'
    ;

literalblock
    =
    | '#' functionName ['/' functionName] '#'
    | '#' quotedstring ['/' functionName] '#'
    | '#' '#'
    ;

listblock
    =
    '[' functionName (quotedstring|none) ['/' functionName] ']'
    ;

greedylistblock
    =
    '[*' functionName listinput (quotedstring|none) ['/' functionName] ']'
    ;

setblock
    =
    '[<' functionName (quotedstring|none) ['/' functionName] ']'
    ;

hashableblock
    =
    | literalblock
    | listblock
    | greedylistblock
    | setblock
    | hashableencapblock
    ;

hashpairblock
    =
    '{' ['rev'] (functionName|hashableblock) (functionName|block) quotedstring ['/' functionName] '}'
    ;

hashpairdistribute
    =
    '{<' ['rev'] (functionName|hashableblock) (functionName|block) quotedstring ['/' functionName] '}'
    ;

hashlineblock
    =
    '{*' ['rev'] (functionName|hashableblock) (functionName|block) quotedstring quotedstring ['/' functionName] '}'
    ;

multiblock
    =
    '(' {block}+ quotedstring ['/' functionName] ')'
    ;

functionName
    =
    /[a-zA-Z]+[a-zA-Z0-9_.]+/
    ;

listinput
    =
    |'[' ', '.{/[^\]^,]+/}+ ']'
    |'[' ','.{/[^\]^,]+/}+ ']'
    ;
'''