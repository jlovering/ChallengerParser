import unittest
import logging
import sys
import re

import testCaseSoT

import ChallengerParser as parser
import ChallengerGrammar
import tatsu

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

class DayTest():
    def deepCompare(self, struct1, struct2):
        truthy = []
        for (s1, s2) in zip(struct1, struct2):
            #logging.debug("%s %s" % (s1, s2))
            try:
                if len(s1) == len(s2):
                    if len(s1) == 1:
                        truthy.append(s1 == s2)
                    else:
                        truthy.append(self.deepCompare(s1, s2))
                else:
                    truthy.append(False)
            except:
                truthy.append(s1 == s2)
        #logging.debug(truthy)
        return all(truthy)

    def testParse(self):
        par = parser.Input(self.infile, self.definition)
        outData = par.parse()
        logging.debug(outData)

        SoT = eval("testCaseSoT.%s" % type(self).__name__.replace("_Strings",""))
        logging.debug(SoT)

        assert self.deepCompare(SoT, outData)

    def tearDown(self):
        self.infile.close()

class Day1Test(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addBuilder(parser.ListBuilder(parser.LiteralBlock(int), ""))

        self.infile = open("testfiles/day1-testInput", "r")

class Day1Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.buildersFromStr('''[[
#int#
]''')

        self.infile = open("testfiles/day1-testInput", "r")

class Day2Test(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.ListBuilder( \
                parser.MultiBlockLine( \
                    [ \
                    parser.ListBlock(int, '-'),
                    parser.LiteralBlock(lambda e: str(e)[:-1]),
                    parser.LiteralBlock(str)
                    ], ' '), \
                parser.EMPTYLINE) \
            )

        self.infile = open("testfiles/day2-testInput", "r")

class Day2Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addFunction('Day2Test_Strings_custom', lambda s: s[:-1])
        self.definition.buildersFromStr('''[[
([int '-'] #Day2Test_Strings_custom# #str# ' ')
]''')
        self.infile = open("testfiles/day2-testInput", "r")

class Day3Test(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.ListBuilder( \
                    parser.ListBlock(str, None), \
                parser.EMPTYLINE) \
            )

        self.infile = open("testfiles/day3-testInput", "r")

class Day3Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition = parser.InputDefinition()
        self.definition.buildersFromStr('''[[
[str None]
]''')
        self.infile = open("testfiles/day3-testInput", "r")

class Day4Test(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.ListBuilder( \
                parser.MultiLineSpanBuilder( \
                    parser.HashLineBlock( \
                        parser.HashPairBlock(str, str, ':'), \
                        ' '), \
                    #parser.LiteralBlock(str), \
                    ' ', parser.EMPTYLINE), \
                parser.EMPTYLINE) \
            )
        self.infile = open("testfiles/day4-testInput", "r")

class Day4Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.buildersFromStr('''[[
{{
{*str str ':' ' '}
}
]''')
        self.infile = open("testfiles/day4-testInput", "r")

class Day5Test(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addBuilder(parser.ListBuilder(parser.LiteralBlock(lambda v: int(parser.tr(v, 'BFRL', '1010'), 2)), ""))

        self.infile = open("testfiles/day5-testInput", "r")

class Day5Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addFunction('Day5Test_Strings_custom', lambda v: int(parser.tr(v, 'BFRL', '1010'), 2))
        self.definition.buildersFromStr('''[[
#Day5Test_Strings_custom#
]''')
        self.infile = open("testfiles/day5-testInput", "r")

class Day6Test(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.ListBuilder( \
                parser.ListBuilder( \
                    parser.SetBlock(str, parser.NODELIM), \
                parser.EMPTYLINE), \
            parser.EMPTYLINE)
            )

        self.infile = open("testfiles/day6-testInput", "r")

class Day6Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.buildersFromStr('''[[
[[
[<str None]
]
]''')

        self.infile = open("testfiles/day6-testInput", "r")

class Day7Test(DayTest, unittest.TestCase):
    def setUp(self):
        def bagParse(b):
            if b == " no other bags.":
                return None
            else:
                sR = {}
                for l in b.split(','):
                    bM = re.match(r"[\s]*(\d+) (.+) bag[s]{0,1}", l)
                    sR[bM.group(2)] = int(bM.group(1))
                return sR
        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.HashBuilder( \
                    parser.HashPairBlock(str, bagParse, "bags contain"),\
                ""), \
            )

        self.infile = open("testfiles/day7-testInput", "r")

class Day7Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        def bagParse(b):
            if b == " no other bags.":
                return None
            else:
                sR = {}
                for l in b.split(','):
                    bM = re.match(r"[\s]*(\d+) (.+) bag[s]{0,1}", l)
                    sR[bM.group(2)] = int(bM.group(1))
                return sR

        self.definition = parser.InputDefinition()
        self.definition.addFunction('Day7Test_Strings_custom', bagParse)
        self.definition.buildersFromStr('''{{
{str Day7Test_Strings_custom "bags contain"}
}''')

        self.infile = open("testfiles/day7-testInput", "r")

class Day8Test(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.ListBuilder( \
                parser.MultiBlockLine( \
                    [ \
                        parser.LiteralBlock(str), \
                        parser.LiteralBlock(int), \
                    ], parser.SPACE), \
                parser.EMPTYLINE)
            )

        self.infile = open("testfiles/day8-testInput", "r")

class Day8Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.buildersFromStr('''[[
(#str# #int# ' ')
]''')

        self.infile = open("testfiles/day8-testInput", "r")

class Day13Test(DayTest, unittest.TestCase):
    def setUp(self):
        def busParser(b):
            if b == "x":
                return None
            else:
                return int(b)
        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.SingleLineBuilder( \
                parser.LiteralBlock(int) \
                ) \
            )
        self.definition.addBuilder( \
            parser.SingleLineBuilder( \
                parser.ListBlock( \
                    busParser, \
                    ',')
                )
            )

        self.infile = open("testfiles/day13-testInput", "r")

class Day13Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        def busParser(b):
            if b == "x":
                return None
            else:
                return int(b)
        self.definition = parser.InputDefinition()
        self.definition.addFunction('Day13Test_Strings_custom', busParser)
        self.definition.buildersFromStr('''#int#
[Day13Test_Strings_custom ',']''')

        self.infile = open("testfiles/day13-testInput", "r")


class Day14Test(DayTest, unittest.TestCase):
    def setUp(self):
        def memKeyParse(b):
            mP = re.match(r"mem\[(\d)+\]", b)
            return mP.group(1)

        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.SingleLineBuilder( \
                parser.LiteralBlock(lambda d: d.split(' = ')[1]) \
                ) \
            )
        self.definition.addBuilder( \
            parser.ListBuilder( \
                parser.MultiBlockLine( [ \
                        parser.LiteralBlock(memKeyParse), \
                        parser.LiteralBlock(int), \
                        ], \
                    ' = '), \
                parser.EMPTYLINE)
            )

        self.infile = open("testfiles/day14-testInput", "r")

class Day14Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        def memKeyParse(b):
            mP = re.match(r"mem\[(\d)+\]", b)
            return mP.group(1)

        self.definition = parser.InputDefinition()
        self.definition.addFunction('Day14Test_Strings_custom', memKeyParse)
        self.definition.addFunction('Day14Test_Strings_custom1', lambda d: d.split(' = ')[1])
        self.definition.buildersFromStr('''#Day14Test_Strings_custom1#
[[
(#Day14Test_Strings_custom# #int# " = ")
]''')

        self.infile = open("testfiles/day14-testInput", "r")

class Day16Test(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.HashBuilder( \
                parser.HashPairBlock( \
                    str, \
                    parser.MultiBlockLine( \
                        [\
                            parser.MultiBlockLine( \
                                [\
                                    parser.LiteralBlock(int), \
                                    parser.LiteralBlock(int)\
                                ], "-"), \
                            parser.MultiBlockLine( \
                                [\
                                    parser.LiteralBlock(int), \
                                    parser.LiteralBlock(int)\
                                ], "-") \
                        ], " or "), \
                    ":"), \
                parser.EMPTYLINE) \
            )
        self.definition.addBuilder( \
            parser.MultiBuilderBuilder( \
                [ \
                    parser.SingleLineBuilder( \
                            parser.LiteralNoParse()
                        ), \
                    parser.SingleLineBuilder( \
                        parser.ListBlock(int, ',')
                    ) \
                ], parser.EMPTYLINE)
            )

        self.definition.addBuilder( \
            parser.MultiBuilderBuilder( \
                [ \
                    parser.SingleLineBuilder( \
                            parser.LiteralNoParse() \
                        ), \
                    parser.ListBuilder( \
                            parser.ListBlock(int, ','),
                            parser.EMPTYLINE \
                        ) \
                ], parser.EMPTYLINE)
            )

        self.infile = open("testfiles/day16-testInput", "r")

class Day16Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.buildersFromStr('''{{
{str ([int '-'] [int '-'] ' or ') ':'}
}
((
    #"your ticket:"#
    [int ',']
)
((
    #"nearby tickets:"#
    [[
        [int ',']
    ]
)''')

        self.infile = open("testfiles/day16-testInput", "r")

class Day19Test(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.HashBuilder( \
                parser.HashPairBlock( \
                    int, \
                    parser.MultiBlockLine( \
                        [\
                            parser.OrBlock(
                                [\
                                    parser.ListBlock(int, parser.SPACE), \
                                    parser.LiteralBlock(lambda s: s[1]) \
                                ] \
                            ), \
                            parser.ListBlock(int, parser.SPACE), \
                        ], ' | '), \
                    ": "), \
                parser.EMPTYLINE) \
            )

        self.definition.addBuilder( \
            parser.ListBuilder( \
                    parser.ListBlock(str, None),
                    parser.EMPTYLINE \
                ) \
            )

        self.infile = open("testfiles/day19-testInput", "r")

class Day19Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addFunction('Day19Test_Strings_custom', lambda s: s[1])
        self.definition.buildersFromStr('''{{
{int ([int ' '] or #Day19Test_Strings_custom# [int ' '] ' | ') ': '}
}
[[
[str None]
]''')

        self.infile = open("testfiles/day19-testInput", "r")

class Day20Test(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.MultiBuilderBuilder( \
                [
                    parser.SingleLineBuilder( \
                        parser.MultiBlockLine( \
                            [\
                                parser.LiteralNoParse("Tile"), \
                                parser.LiteralBlock(lambda s: int(s[:-1])) \
                            ], parser.SPACE), \
                        ), \
                    parser.ListBuilder( \
                        parser.ListBlock(str, None), \
                        parser.EMPTYLINE) \
                ], \
                parser.EMPTYLINE) \
            )

        self.infile = open("testfiles/day20-testInput", "r")

class Day20Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addFunction('Day20Test_Strings_custom', lambda s: int(s[:-1]))
        self.definition.buildersFromStr('''[[
((
    (#"Tile"# #Day20Test_Strings_custom# ' ')
    [[
        [str None]
    ]
)
]''')

        self.infile = open("testfiles/day20-testInput", "r")

class Day21Test(DayTest, unittest.TestCase):
    '''
    Unfortunately this input is too weird, so the parser would have to return a list array and further handling is needed
    '''
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.ListBuilder( \
                    parser.MultiBlockLine( [\
                            parser.ListBlock(str, ' '), \
                            parser.EncapsulatedLine( \
                                lambda s: s[:-1], \
                                parser.ListBlock(str, ', ') \
                                ), \
                            ], \
                        ' (contains '), \
                parser.EMPTYLINE) \
            )

        self.infile = open("testfiles/day21-testInput", "r")

class Day21Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addFunction('Day21Test_Strings_custom', lambda s: s[:-1])
        self.definition.buildersFromStr('''[[
([str ' '] >[str ', '] Day21Test_Strings_custom< ' (contains ')
]''')

        self.infile = open("testfiles/day21-testInput", "r")

class Day22Test(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.MultiBuilderBuilder( \
                [ \
                    parser.SingleLineBuilder( \
                        parser.LiteralNoParse(), \
                        ), \
                    parser.ListBuilder( \
                        parser.LiteralBlock(int), \
                        parser.EMPTYLINE) \
                ], \
                parser.EMPTYLINE) \
            )

        self.infile = open("testfiles/day22-testInput", "r")

class Day22Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        self.definition = parser.InputDefinition()
        self.definition.buildersFromStr('''((
    ##
    [[
        #int#
    ]
)''')

        self.infile = open("testfiles/day22-testInput", "r")

class Day24Test(DayTest, unittest.TestCase):
    def setUp(self):
        directions = ['ne','e','se','sw','w','nw']
        self.definition = parser.InputDefinition()
        self.definition.addBuilder( \
            parser.ListBuilder( \
                parser.ListElementMunch(directions, str, None), \
                parser.EMPTYLINE) \
            )

        self.infile = open("testfiles/day24-testInput", "r")

class Day24Test_Strings(DayTest, unittest.TestCase):
    def setUp(self):
        directions = ['ne','e','se','sw','w','nw']
        self.definition = parser.InputDefinition()
        self.definition.buildersFromStr('''[[
        [* str %s None]
    ]''' % (directions))

        self.infile = open("testfiles/day24-testInput", "r")

class GrammarTest():
    def testGrammar(self):
        #print(self.TESTSTR)
        for (i, s) in enumerate(self.TESTSTR.split('\n')):
            ast = tatsu.parse(ChallengerGrammar.GRAMMAR, s)
            #rint(ast)
            #rint(self.expect[i])
            assert ast == self.expect[i]

class GrammarTest_Builders(GrammarTest, unittest.TestCase):
    def setUp(self):
        self.TESTSTR = \
'''((
) " "
[[
] "."
{{
} ","'''
        self.expect = [
            ('(('),
            (')', '" "'),
            ('[['),
            (']', '"."'),
            ('{{'),
            ('}', '","'),
            ]

class GrammarTest_LiteralBlock(GrammarTest, unittest.TestCase):
    def setUp(self):
        self.TESTSTR = \
'''#int#
#foo/bar#'''
        self.expect = [
            ('#', 'int', '#'),
            ('#', 'foo', '/', 'bar', '#'),
            ]

class GrammarTest_ListBlock(GrammarTest, unittest.TestCase):
    def setUp(self):
        self.TESTSTR = \
'''[int ' ']
[int ',' /call]'''
        self.expect = [
            ('[', 'int', '\' \'', ']'),
            ('[', 'int', '\',\'', '/', 'call', ']'),
            ]

class GrammarTest_GreedListBlock(GrammarTest, unittest.TestCase):
    def setUp(self):
        self.TESTSTR = \
'''[*int [a,b,c] None]
[*int [0, 1, 2] None /call]'''
        self.expect = [
            ('[*', 'int', ('[', ['a', 'b', 'c'], ']'), 'None', ']'),
            ('[*', 'int', ('[', ['0', '1', '2'], ']'), 'None', '/', 'call', ']'),
            ]

class GrammarTest_SetBlock(GrammarTest, unittest.TestCase):
    def setUp(self):
        self.TESTSTR = \
'''[<int ' ']
[<int '.' /call]'''
        self.expect = [
            ('[<', 'int', '\' \'', ']'),
            ('[<', 'int', '\'.\'', '/', 'call', ']'),
            ]

class GrammarTest_HashPair(GrammarTest, unittest.TestCase):
    def setUp(self):
        self.TESTSTR = \
'''{int int ' '}
{int int '.' /call}
{#func# int ' '}
{#func# #func# ' '}'''
        self.expect = [
            ('{', 'int', 'int', '\' \'', '}'),
            ('{', 'int', 'int', '\'.\'', '/', 'call', '}'),
            ('{', ('#', 'func', '#'), 'int', '\' \'', '}'),
            ('{', ('#', 'func', '#'), ('#', 'func', '#'), '\' \'', '}'),
            ]

unittest.main()