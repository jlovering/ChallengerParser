import sys
import re
import logging
import tatsu
import ChallengerGrammar

EMPTYLINE = ""
NODELIM = None
SPACE = ' '
NEWLINE = '\n'

logger = logging.getLogger('root')
FORMAT = "%(filename)s:%(lineno)d:%(funcName)20s() : %(message)s"
logging.basicConfig(stream=sys.stderr, format=FORMAT, level=logging.INFO)

def tr(inS, i, s):
    return inS.translate(str.maketrans(i,s))

def CharIgnore(inp):
    return ""

class SingleBlock:
    def __init__(self):
        return

    def parse(self, inp):
        return inp

class OrBlock(SingleBlock):
    def __init__(self, parsers):
        self.parsers = parsers

        for p in self.parsers:
            if not issubclass(type(p), SingleBlock):
                raise TypeError("OrBlock all parsers must be SingleBlock")

    def parse(self, inp):
        logging.debug("inp: \"%s\"" % inp)

        self.value = None
        for p in self.parsers:
            try:
                self.value = p.parse(inp)
                break
            except:
                continue

        if self.value is None:
            raise Exception("No parsers for \"%s\"" % inp)

        return self.value

class LiteralBlock(SingleBlock):
    def __init__(self, parser, callback=None):
        self.parser = parser
        self.callback = callback

        if not callable(parser):
            raise TypeError("Literal parser must be callable")

        if callback is not None and not callable(callback):
            raise TypeError("Callback must be callable")

    def parse(self, inp):
        logging.debug("inp: \"%s\"" % inp)

        if self.callback is not None:
            return self.callback(self.parser(inp))

        return self.parser(inp)

class LiteralNoParse(SingleBlock):
    def __init__(self, absolute=None):
        self.absolute = absolute
        return

    def parse(self, inp):
        logging.debug("inp: \"%s\"" % inp)
        if self.absolute is not None:
            if inp != self.absolute:
                raise ValueError("LiteralNoParse exact value expected not received")
        return None

class EncapsulatedLine(SingleBlock):
    def __init__(self, trimmer, block):
        self.trimmer = trimmer
        self.block = block

        if not callable(self.trimmer):
            raise TypeError("EncapsulatedLine requires callable trimmer")

    def parse(self, inp):
        logging.debug("inp: \"%s\"" % inp)
        inp = self.trimmer(inp)
        return self.block.parse(inp)

class MultiBlockLine(SingleBlock):
    def __init__(self, blocks, delimiter, callback=None):
        self.blocks = blocks
        self.delimiter = delimiter
        self.callback = callback

        if callback is not None and not callable(callback):
            raise TypeError("Callback must be callable")

        for b in self.blocks:
            if not issubclass(type(b), SingleBlock):
                raise TypeError("MultiBlockLine must parse blocks")

    def parse(self, inp):
        logging.debug("inp: \"%s\"" % inp)
        self.items = []
        for (line, b) in zip(inp.split(self.delimiter), self.blocks):
            logging.debug("inp: \"%s\"" % inp)
            bout = b.parse(line)
            if bout is not None:
                self.items.append(bout)

        if len(self.items) == 1:
            self.items = self.items[0]

        if self.callback is not None:
                return self.callback(self.items)
        return self.items

class ListBlock(SingleBlock):
    def __init__(self, elementParser, delimiter, callback=None):
        self.elementParser = elementParser
        self.delimiter = delimiter
        self.callback = callback

        if not callable(elementParser):
            raise TypeError("List elementParser must be callable", elementParser)

        if callback is not None and not callable(callback):
            raise TypeError("Callback must be callable")

    def parse(self, inp):
        self.list = []
        logging.debug("inp: \"%s\"" % inp)
        if self.delimiter is None:
            for i in inp:
                eparse = self.elementParser(i)
                if eparse is not None:
                    self.list.append(eparse)
        else:
            for i in inp.split(self.delimiter):
                eparse = self.elementParser(i)
                if eparse is not None:
                    self.list.append(eparse)

        if self.callback is not None:
            return self.callback(self.list)

        return self.list

class ListElementMunch(SingleBlock):
    def __init__(self, elements, elementParser, delimiter, callback=None):
        self.elements = elements
        self.elementParser = elementParser
        self.delimiter = delimiter
        self.callback = callback

        if callback is not None and not callable(callback):
            raise TypeError("Callback must be callable")

        if not callable(elementParser):
            raise TypeError("List elementParser must be callable", elementParser)

    def parse(self, inp):
        self.list = []
        logging.debug("inp: \"%s\"" % inp)
        if self.delimiter is None:
            cand = []
            remaining = inp
            while remaining != "":
                cand.append(self.elementParser(remaining[0]))
                remaining = remaining[1:]
                if self.elementParser(''.join(cand)) in self.elements:
                    self.list.append(self.elementParser(''.join(cand)))
                    cand = []
        else:
            inpA = inp.split(self.delimiter)
            cand = []
            remaining = inpA
            while len(remaining) > 0:
                cand.append(self.elementParser(remaining[0]))
                remaining = remaining[1:]
                if self.delimiter.join(cand) in self.elements:
                    self.list.append(self.delimiter.join(cand))
                    cand = []

        if self.callback is not None:
            return self.callback(self.list)

        return self.list

class SetBlock(ListBlock):
    def __init__(self, elementParser, delimiter, callback=None):
        super().__init__(elementParser, delimiter, callback)

    def parse(self, inp):
        tlist = super().parse(inp)
        return set(tlist)


class HashPairBlock(SingleBlock):
    def __init__(self, keyblock, valueblock, seperator, distribute=False, reverse=False, callback=None):
        self.keyblock = keyblock
        self.valueblock = valueblock
        self.seperator = seperator
        self.distribute = distribute
        self.reverse = reverse
        self.callback = callback

        if callback is not None and not callable(callback):
            raise TypeError("Callback must be callable")

        if not callable(self.keyblock) and \
            not isinstance(self.valueblock, SingleBlock):
            raise TypeError("Keyblock must be callable or SinglBlock")

        if not callable(self.valueblock) and \
            not isinstance(self.valueblock, SingleBlock):
            raise TypeError("Valueblock must be callable or SinglBlock")

    def parse(self, inp):
        logging.debug("inp: \"%s\"" % inp)
        if not self.reverse:
            key, value = inp.split(self.seperator)
        else:
            value, key = inp.split(self.seperator)

        if isinstance(self.keyblock, SingleBlock):
            self.key = self.keyblock.parse(key)
        else:
            self.key = self.keyblock(key)

        if isinstance(self.valueblock, SingleBlock):
            self.value = self.valueblock.parse(value)
        else:
            self.value = self.valueblock(value)

        self.hash = {}
        if self.distribute:
            for k in self.key:
                self.hash[k] = self.value
        else:
            self.hash[key] = self.value

        if self.callback is not None:
            return self.callback(self.hash)

        return self.hash

class HashLineBlock(SingleBlock):
    def __init__(self, hashparser, delimiter, callback=None):
        self.hashparser = hashparser
        self.delimiter = delimiter
        self.callback = callback

        if callback is not None and not callable(callback):
            raise TypeError("Callback must be callable")

        if not isinstance(self.hashparser, HashPairBlock):
            raise TypeError("HashLineBuilder needs HashPairBlock")

    def parse(self, inp):
        logging.debug("inp: \"%s\"" % inp)
        self.hash = {}
        if self.delimiter is not None:
            for l in inp.split(self.delimiter):
                lh = self.hashparser.parse(l)
                if lh is not None:
                    self.hash.update(lh)
        else:
            lh = self.hashparser.parse(inp)
            if lh is not None:
                self.hash.update(lh)

        if self.callback is not None:
            return self.callback(self.hash)

        return self.hash

class MuiltiLineBlock:
    def __init__(self):
        return

    def parse(self, inp):
        return inp

class MultiLineSpanBuilder(MuiltiLineBlock):
    def __init__(self, lineblock, seperator, endvalue, callback=None):
        self.lineblock = lineblock
        self.seperator = seperator
        self.endvalue = endvalue
        self.callback = callback

        if callback is not None and not callable(callback):
            raise TypeError("Callback must be callable")

        if not issubclass(type(self.lineblock), SingleBlock):
            raise TypeError("SingleLineBuilder needs SingleBlock to build")

    def parse(self, infile, incLine=""):
        logging.debug("inp: \"%s\"" % incLine)
        compositeline = incLine

        line = infile.readline().rstrip()
        while line != self.endvalue:
            compositeline += self.seperator + line
            logging.debug("inp: \"%s\"" % line)
            line = infile.readline().rstrip()

        logging.debug("inp: \"%s\"" % line)

        if self.callback is not None:
            return self.callback(self.lineblock.parse(compositeline))
        return self.lineblock.parse(compositeline)

class SingleLineBuilder(MuiltiLineBlock):
    def __init__(self, lineblock, callback=None):
        self.lineblock = lineblock
        self.callback = callback

        if callback is not None and not callable(callback):
            raise TypeError("Callback must be callable")

        if not issubclass(type(self.lineblock), SingleBlock):
            raise TypeError("SingleLineBuilder needs SingleBlock to build")

    def parse(self, infile, intLine=None):
        if intLine == None:
            line = infile.readline().rstrip()
        else:
            line = intLine
        logging.debug("inp: \"%s\"" % line)

        if self.callback is not None:
            return self.callback(self.lineblock.parse(compositeline))
        return self.lineblock.parse(line)

class SingleLineBuilderThrowToEnd(SingleLineBuilder):
    def __init__(self, lineblock, endvalue, callback=None):
        super().__init__(lineblock, callback=callback)
        self.endvalue = endvalue
        self.callback = callback

        if callback is not None and not callable(callback):
            raise TypeError("Callback must be callable")

    def parse(self, infile, intLine=None):
        if intLine == None:
            line = infile.readline().rstrip()
        else:
            line = intLine
        logging.debug("inp: \"%s\"" % line)

        l = super().parse(infile)
        while infile.readline().rstrip() != self.endvalue:
            continue
        return l

class MultiBuilderBuilder(MuiltiLineBlock):
    def __init__(self, blocks, endvalue, callback=None):
        self.blocks = blocks
        self.endvalue = endvalue
        self.callback = callback

        if callback is not None and not callable(callback):
            raise TypeError("Callback must be callable")

        for b in self.blocks:
            if not isinstance(b, MuiltiLineBlock) and \
                not isinstance(b, MultiLineSpanBuilder):
                raise TypeError("MultiBuilderBuilder combines several multiline blocks")

    def parse(self, infile, intLine=None):
        if intLine == None:
            line = infile.readline().rstrip()
        else:
            line = intLine
        logging.debug("inp: \"%s\"" % line)
        self.list = []
        while line != self.endvalue:
            blockOut = []
            for b in self.blocks:
                if isinstance(b, MultiLineSpanBuilder):
                    l = b.parse(infile, line)
                elif isinstance(b, MuiltiLineBlock):
                    l = b.parse(infile, line)
                else:
                    raise Exception("oops")

                if l is not None:
                    blockOut.append(l)

                line = infile.readline().rstrip()
                logging.debug("inp: \"%s\"" % line)
            self.list += blockOut

        if len(self.list) == 1:
            self.list = self.list[0]

        if self.callback is not None:
            return self.callback(self.list)
        return self.list

class ListBuilder(MuiltiLineBlock):
    def __init__(self, lineblock, endvalue, callback=None):
        self.lineblock = lineblock
        self.endvalue = endvalue
        self.callback = callback

        if callback is not None and not callable(callback):
            raise TypeError("Callback must be callable")

        if not isinstance(self.lineblock, SingleBlock) and \
            not isinstance(self.lineblock, MuiltiLineBlock) and \
            not isinstance(self.lineblock, MultiLineSpanBuilder):
            raise TypeError("Listbuilder needs SingleBlock or MultiLineSpanBuilder got \"%s\"" % type(self.lineblock))

    def parse(self, infile, intLine=None):
        if intLine == None:
            line = infile.readline().rstrip()
        else:
            line = intLine
        logging.debug("inp: \"%s\"" % line)
        self.list = []
        while line != self.endvalue:
            if isinstance(self.lineblock, SingleBlock):
                l = self.lineblock.parse(line)
            elif isinstance(self.lineblock, MultiLineSpanBuilder):
                l = self.lineblock.parse(infile, line)
            elif isinstance(self.lineblock, MuiltiLineBlock):
                l = self.lineblock.parse(infile, line)
            else:
                raise Exception("oops")

            if l is not None:
                self.list.append(l)

            line = infile.readline().rstrip()
            logging.debug("inp: \"%s\"" % line)

        if len(self.list) == 1:
            self.list = self.list[0]

        if self.callback is not None:
            return self.callback(self.list)
        return self.list

class HashBuilder(MuiltiLineBlock):
    def __init__(self, hashblock, endvalue, callback=None):
        self.hashblock = hashblock
        self.endvalue = endvalue
        self.callback = callback

        if callback is not None and not callable(callback):
            raise TypeError("Callback must be callable")

        if not isinstance(self.hashblock, HashPairBlock) and \
            not isinstance(self.hashblock, HashLineBlock):
            raise TypeError("Hashbuilder needs HashPairBlock to build")

    def parse(self, infile, intLine=None):
        if intLine == None:
            line = infile.readline().rstrip()
        else:
            line = intLine

        logging.debug("inp: \"%s\"" % line)

        self.hash = {}
        while line != self.endvalue:
            lineH = self.hashblock.parse(line)

            self.hash.update(lineH)

            line = infile.readline().rstrip()

        if self.callback is not None:
            return self.callback(self.hash)
        return self.hash

class InputDefinition:
    def __init__(self):
        self.builders = []
        self.functions = {
            'int' : int,
            'str' : str }

    def buildersFromStr(self, stringDef):
        if stringDef is not None:
            self.stringDef = stringDef.split('\n')
            self.stridx = 0
            self.strParseRootBuilders()

    def strParseUnQuote(self, str):
        return str[1:-1]

    def strParseRootBuilders(self):
        while self.stridx < len(self.stringDef):
            self.addBuilder(self.strParseBuilder())

    def strParseBuilder_helper(self, ast):
        # At this point the AST is either a builder symbol, which can only be one item
        # For reasons I don't understand tatsu will return this as a none tuple
        # Any tuple is by definition not the start of a builder block, and those must be
        # of a length greater than 1
        if isinstance(ast, tuple) and len(ast) > 1:
            return SingleLineBuilder(self.strParseBlock(ast))
        elif ast == '((':
            return self.strParseMultiBuilderBuilder()
        elif ast == '[[':
            return self.strParseListBuilder()
        elif ast == '{{':
            return self.strParseHashBuilder()
        else:
            raise ValueError("Not a valid builder")

    def strParseBuilder(self):
        while self.stridx < len(self.stringDef):
            ast = tatsu.parse(ChallengerGrammar.GRAMMAR, self.stringDef[self.stridx])
            self.stridx += 1
            logging.debug("ast: \"%s\"" % str(ast))
            return self.strParseBuilder_helper(ast)

    def strParseBuilder_closehelper(self, ast):
        # There are 4 valid close forms for any builder:
        #   ')',
        #   (')', "delimiter")
        #   (')', '/',          callback)
        #   (')', "delimiter",  '/',        callback)
        # The first is handled directly, the ast passed here is only after the initial
        # close symbol, and assumes that is stripped

        if len(ast) == 1:
            # Can only have a delimiter:
            return self.strParseUnQuote(ast[0]), None
        elif len(ast) == 2:
            # Can only be a callback
            return None, self.functions[ast[1]]
        elif len(ast) == 3:
            # Both!
            return self.strParseUnQuote(ast[0]), self.functions[ast[2]]
        else:
            raise ValueError("Malformed builder close: \"%s\"" % (ast))

    def strParseMultiBuilderBuilder(self):
        builders = []
        while self.stridx < len(self.stringDef):
            ast = tatsu.parse(ChallengerGrammar.GRAMMAR, self.stringDef[self.stridx])
            self.stridx += 1
            logging.debug("ast: \"%s\"" % str(ast))
            # As above, the close is a str if it's a single close
            if isinstance(ast, str) and ast == '))':
                #Close this Multibuilder
                return MultiBuilderBuilder(builders, EMPTYLINE)
            elif isinstance(ast, tuple) and ast[0] == '))':
                delimiter, callback = self.strParseBuilder_closehelper(ast[1:])
                return MultiBuilderBuilder(builders, delimiter, callback)
            else:
                builders.append(self.strParseBuilder_helper(ast))

    def strParseListBuilder(self):
        builder = None
        while self.stridx < len(self.stringDef):
            ast = tatsu.parse(ChallengerGrammar.GRAMMAR, self.stringDef[self.stridx])
            self.stridx += 1
            logging.debug("ast: \"%s\"" % str(ast))
            # Same close forms as above, but with ']'
            if isinstance(ast, str) and ast == ']]':
                return ListBuilder(builder, EMPTYLINE)
            elif isinstance(ast, tuple) and ast[0] == ']]':
                delimiter, callback = self.strParseBuilder_closehelper(ast[1:])
                return ListBuilder(builder, delimiter, callback)
            else:
                if builder is not None:
                    raise ValueError("List Builder can only contain one element")
                builder = self.strParseBuilder_helper(ast)

    def strParseHashBuilder(self):
        builder = None
        while self.stridx < len(self.stringDef):
            ast = tatsu.parse(ChallengerGrammar.GRAMMAR, self.stringDef[self.stridx])
            self.stridx += 1
            logging.debug("ast: \"%s\"" % str(ast))
            # Same close forms as above
            if isinstance(ast, str) and ast == '}}':
                return HashBuilder(builder, EMPTYLINE)
            elif isinstance(ast, tuple) and ast[0] == '}}':
                delimiter, callback = self.strParseBuilder_closehelper(ast[1:])
                return HashBuilder(builder, delimiter, callback)
            else:
                # Hash builders can only contain hash builder type elements
                # This means that the blocks encountered must be either '{', '{*', or '{d'
                # All of these are multipls so will be a tuple
                if isinstance(ast, tuple) and len(ast) > 1 and \
                    (ast[0] == '{' or ast[0] == '{*' or ast[0] == '{d'):
                    if builder is not None:
                        raise ValueError("Hash Builder can only contain one element")
                    builder = self.strParseBlock(ast)
                else:
                    raise ValueError("Not a valid builder")

    def strParseBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))
        if ast[0] == '#':
            return self.strParseLiteralBlock(ast)
        elif ast[0] == '(':
            return self.strParseMultiBlockLine(ast)
        elif ast[0] == '[':
            return self.strParseListBlock(ast)
        elif ast[0] == '[*':
            return self.strParseListMunchBlock(ast)
        elif ast[0] == '[<':
            return self.strParseSetBlock(ast)
        elif ast[0] == '{':
            return self.strParseHashPairBlock(ast)
        elif ast[0] == '{*':
            return self.strParseHashLineBlock(ast)
        elif ast[0] == '{<':
            return self.strParseHashPairBlock(ast, True)
        elif ast[0] == 'or':
            return self.strParseOrBlock(ast)
        elif ast[0] == '>':
            return self.strParseEncapBlock(ast)
        else:
            raise ValueError("Not a valid block")

    def strParseLiteralBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))
        # Literals have 3 forms:
        # ('#', parserFunction, #')
        # ('#', "ExactMatch", '#')
        # ('#', '#')
        if len(ast) == 2:
            return LiteralNoParse()
        m = re.match(r"\"(.+)\"", ast[1])
        if m is not None:
            return LiteralNoParse(self.strParseUnQuote(ast[1]))
        else:
            return LiteralBlock(self.functions[ast[1]])

    def strParseTrailingArgs_helper(self, ast):
        # All List/Multi blocks varients have the form:
        #  ... "delimiter", ']')
        #  ... "delimiter", '/', callback ']')
        # To make this reusable, only the deliminator onwards is passed
        logging.debug("ast: \"%s\"" % str(ast))

        if len(ast) == 2:
            delimiter = ast[0]
            callback = None
        elif len(ast) == 4:
            delimiter = ast[0]
            callback = self.functions[ast[2]]

        if delimiter == "None":
            delimiter = None
        else:
            delimiter = self.strParseUnQuote(delimiter)

        return delimiter, callback

    def strParseMultiBlockLine(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))
        blocks = []
        # Multi blocks have the forms:
        #  ('(', [ (any block) ...], "delimiter", ')')
        #  ('(', [ (any block) ...], "delimiter", '/', callback ')')

        for b in ast[1]:
            blocks.append(self.strParseBlock(b))

        delimiter, callback = self.strParseTrailingArgs_helper(ast[2:])

        return MultiBlockLine(blocks, delimiter, callback)

    def strParseListBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))
        # List blocks have the forms:
        #  ('[', elementParser, "delimiter", ']')
        #  ('[', elementParser, "delimiter", '/', callback ']')

        elP = self.functions[ast[1]]

        delimiter, callback = self.strParseTrailingArgs_helper(ast[2:])

        return ListBlock(elP, delimiter, callback)

    def strParseSetBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))

        elP = self.functions[ast[1]]

        delimiter, callback = self.strParseTrailingArgs_helper(ast[2:])

        return SetBlock(elP, delimiter, callback)

    def strParseListMunchBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))

        # This block is special, the elements is a list, which parses into it's own tuple
        # Due to a nueance of how the parser grabs the list, the '[' and ']' bookend the list itself
        # inside the tuple. We therefore tunnel directly to the list
        # i.e.:
        # [* elementParser ('[', [...] ,']') "delimiter"...

        elP = self.functions[ast[1]]

        elements = []
        for e in ast[2][1]:
            elements.append(self.strParseUnQuote(e))

        delimiter, callback = self.strParseTrailingArgs_helper(ast[3:])

        return ListElementMunch(elements, elP, delimiter, callback)


    def strParseHashTypeKV_helper(self, ast):
        # Hash types allow the key and value to also be blocks
        # So we pull those out of the ast and recursively parse them
        logging.debug("ast: \"%s\"" % str(ast))

        # Hash pair blocks take the form:
        #  ('{', [rev], keyparser|block, valueparser|block, "seperator", '}')
        #  ('{', [rev], keyparser|block, valueparser|block, "seperator", '\', callback, '}')
        # If key or value are blocks, then they will be nested tuples

        # Support the reversed type by detecting revesed, caller will pass enough
        # AST to not have to worry, this function slices the AST to after the KV objects

        if type(ast[0]) == str and ast[0] == "rev":
            astKey = ast[2]
            astValue = ast[1]
            astRemaining = ast[3:]
            reverse = True
        else:
            astKey = ast[0]
            astValue = ast[1]
            astRemaining = ast[2:]
            reverse = False

        if type(astKey) == tuple:
            key = self.strParseBlock(astKey)
        else:
            key = self.functions[astKey]

        if type(astValue) == tuple:
            value = self.strParseBlock(astValue)
        else:
            value = self.functions[astValue]

        return key, value, reverse, astRemaining

    def strParseHashPairBlock(self, ast, distribute=False):
        logging.debug("ast: \"%s\"" % str(ast))

        key, value, reverse, ast = self.strParseHashTypeKV_helper(ast[1:])
        # ast is replaces and is now align to after the kv pair

        # Incidentally the seperator and optional callback take the same form here
        # As in listblocks, so reuse to make life easier
        seperator, callback = self.strParseTrailingArgs_helper(ast)

        return HashPairBlock(key, value, seperator, distribute, reverse, callback)

    def strParseHashLineBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))

        # A HashLineBlock is almost identical to the HashPair, except that an additional
        # Seperator is added. The first is always the key/value seperator and the second
        # is always the item seperator. We reuse the trailing arg function as it will work

        key, value, reverse, ast = self.strParseHashTypeKV_helper(ast[1:])
        # ast is replaces and is now align to after the kv pair

        seperator = self.strParseUnQuote(ast[0])

        itemSeperator, callback = self.strParseTrailingArgs_helper(ast[1:])

        return HashLineBlock(HashPairBlock(key, value, seperator, reverse=reverse), itemSeperator, callback)


    def strParseOrBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))

        # OrBlocks are 'special', they are parsed to be left noted
        # i.e "block1 or block2" becomes ('or', block1, block2)
        # When ors nest, this pattern repeats, so "bl1 or bl2 or bl3"
        # becomes ('or', bl1, ('or', bl2, 'bl3'))
        # Though untested, this should automatically build recursive or's
        # Which is sub-optimal as it increases recursion depth (where the orblock
        # can hypothetically work on n blocks)

        blocks = []
        for b in ast[1:]:
            blocks.append(self.strParseBlock(b))

        return OrBlock(blocks)

    def strParseEncapBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))

        return EncapsulatedLine(self.functions[ast[2]], self.strParseBlock(ast[1]))

    def addBuilder(self, builder):
        if not issubclass(type(builder), MuiltiLineBlock):
            raise TypeError("Builders must be MuiltiLineBlocks, use SingleLineBuilder for 1 line")
        self.builders.append(builder)

    def addFunction(self, name, func):
        if not callable(func):
            raise TypeError("Parser functions must be callable")

        self.functions[name] = func

class Input:
    def __init__(self, infile, definition):
        self.infile = infile
        self.definition = definition

        if not isinstance(self.definition, InputDefinition):
            raise TypeError("InputDefinition required")

    def parse(self):
        if len(self.definition.builders) == 1:
            self.blockOut = self.definition.builders[0].parse(self.infile)
        else:
            self.blockOut = []
            for b in self.definition.builders:
                bout = b.parse(self.infile)
                if bout is not None:
                    self.blockOut.append(bout)

        return self.blockOut

    def retrieve(self):
        return self.blockOut