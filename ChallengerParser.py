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
    def __init__(self, elementParser, delimiter):
        super().__init__(elementParser, delimiter)

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

    def strParseBuilder(self):
        while self.stridx < len(self.stringDef):
            ast = tatsu.parse(ChallengerGrammar.GRAMMAR, self.stringDef[self.stridx])
            self.stridx += 1
            logging.debug("ast: \"%s\"" % str(ast))
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

    def strParseMultiBuilderBuilder(self):
        builders = []
        while self.stridx < len(self.stringDef):
            ast = tatsu.parse(ChallengerGrammar.GRAMMAR, self.stringDef[self.stridx])
            self.stridx += 1
            logging.debug("ast: \"%s\"" % str(ast))
            if isinstance(ast, tuple) and len(ast) > 1:
                builders.append(SingleLineBuilder(self.strParseBlock(ast)))
            elif ast == '((':
                builders.append(self.strParseMultiBuilderBuilder())
            elif ast == '[[':
                builders.append(self.strParseListBuilder())
            elif ast == '{{':
                builders.append(self.strParseHashBuilder())
            elif ast == ')':
                #Close this Multibuilder
                if len(ast) == 2:
                    return MultiBuilderBuilder(builders, self.strParseUnQuote(ast[0]))
                else:
                    return MultiBuilderBuilder(builders, EMPTYLINE)
            else:
                raise ValueError("Not a valid builder")

    def strParseListBuilder(self):
        builder = None
        while self.stridx < len(self.stringDef):
            ast = tatsu.parse(ChallengerGrammar.GRAMMAR, self.stringDef[self.stridx])
            self.stridx += 1
            logging.debug("ast: \"%s\"" % str(ast))
            if isinstance(ast, tuple) and len(ast) > 1:
                if builder is not None:
                    raise ValueError("List Builder can only contain one element")
                builder = self.strParseBlock(ast)
            elif ast == '((':
                if builder is not None:
                    raise ValueError("List Builder can only contain one element")
                builder = self.strParseMultiBuilderBuilder()
            elif ast == '[[':
                if builder is not None:
                    raise ValueError("List Builder can only contain one element")
                builder = self.strParseListBuilder()
            elif ast == '{{':
                if builder is not None:
                    raise ValueError("List Builder can only contain one element")
                builder = self.strParseHashBuilder()
            elif ast == ']':
                #Close this ListBuilder
                if len(ast) == 2:
                    return ListBuilder(builder, self.strParseUnQuote(ast[1]))
                else:
                    return ListBuilder(builder, EMPTYLINE)
            else:
                raise ValueError("Not a valid builder")

    def strParseHashBuilder(self):
        builder = None
        while self.stridx < len(self.stringDef):
            ast = tatsu.parse(ChallengerGrammar.GRAMMAR, self.stringDef[self.stridx])
            self.stridx += 1
            logging.debug("ast: \"%s\"" % str(ast))
            if isinstance(ast, tuple) and len(ast) > 1 and ast[0][0] == '{':
                if builder is not None:
                    raise ValueError("Hash Builder can only contain one element")
                builder = self.strParseBlock(ast)
            elif ast == '}':
                #Close this ListBuilder
                if len(ast) == 2:
                    return HashBuilder(builder, self.strParseUnQuote(ast[1]))
                else:
                    return HashBuilder(builder, EMPTYLINE)
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
            return self.strParseHashDistributeBlock(ast)
        elif ast[0] == 'or':
            return self.strParseOrBlock(ast)
        elif ast[0] == '>':
            return self.strParseEncapBlock(ast)
        else:
            raise ValueError("Not a valid block")

    def strParseLiteralBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))
        if len(ast) == 2:
            return LiteralNoParse()
        m = re.match(r"\"(.+)\"", ast[1])
        if m is not None:
            return LiteralNoParse(self.strParseUnQuote(ast[1]))
        else:
            return LiteralBlock(self.functions[ast[1]])

    def strParseMultiBlockLine(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))
        blocks = []
        for b in ast[1]:
            blocks.append(self.strParseBlock(b))
        return MultiBlockLine(blocks, self.strParseUnQuote(ast[2]))

    def strParseListBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))
        seperator = ast[2]
        if seperator == 'None':
            return ListBlock(self.functions[ast[1]], None)
        else:
            return ListBlock(self.functions[ast[1]], self.strParseUnQuote(seperator))

    def strParseSetBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))
        seperator = ast[2]
        if seperator == 'None':
            return SetBlock(self.functions[ast[1]], None)
        else:
            return SetBlock(self.functions[ast[1]], self.strParseUnQuote(seperator))

    def strParseListMunchBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))
        elements = []
        for e in ast[2][1]:
            elements.append(self.strParseUnQuote(e))

        seperator = ast[3]
        if seperator == 'None':
            return ListElementMunch(elements, self.functions[ast[1]], None)
        else:
            return ListElementMunch(elements, self.functions[ast[1]], self.strParseUnQuote(seperator))

    def strParseHashPairBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))

        if type(ast[1]) == tuple:
            key = self.strParseBlock(ast[2])
        else:
            key = self.functions[ast[1]]

        if type(ast[2]) == tuple:
            value = self.strParseBlock(ast[2])
        else:
            value = self.functions[ast[2]]

        return HashPairBlock(key, value, self.strParseUnQuote(ast[3]))

    def strParseHashLineBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))

        if type(ast[1]) == tuple:
            key = self.strParseBlock(ast[2])
        else:
            key = self.functions[ast[1]]

        if type(ast[2]) == tuple:
            value = self.strParseBlock(ast[2])
        else:
            value = self.functions[ast[2]]

        return HashLineBlock(HashPairBlock(key, value, self.strParseUnQuote(ast[3])), self.strParseUnQuote(ast[4]))

    def strParseHashDistributeBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))

        if type(ast[1]) == tuple:
            key = self.strParseBlock(ast[2])
        else:
            key = self.functions[ast[1]]

        if type(ast[2]) == tuple:
            value = self.strParseBlock(ast[2])
        else:
            value = self.functions[ast[2]]

        return HashPairBlock(key, value, self.strParseUnQuote(ast[3]), distribute=True)

    def strParseOrBlock(self, ast):
        logging.debug("ast: \"%s\"" % str(ast))

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