import sys
import re
import logging

EMPTYLINE = ""
NODELIM = None
SPACE = ' '
NEWLINE = '\n'

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

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
        logging.debug("%s, \"%s\"" % (type(self), inp))

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
    def __init__(self, parser):
        self.parser = parser

        if not callable(parser):
            raise TypeError("Literal parser must be callable")

    def parse(self, inp):
        logging.debug("%s, \"%s\"" % (type(self), inp))
        return self.parser(inp)

class LiteralNoParse(SingleBlock):
    def __init__(self, absolute=None):
        self.absolute = absolute
        return

    def parse(self, inp):
        logging.debug("%s, \"%s\" <nop>" % (type(self), inp))
        if self.absolute is not None:
            if inp != self.absolute:
                raise ValueError("LiteralNoParse exact value expected not received")
        return None

class EncapsulatedLine(SingleBlock):
    def __init__(self, leadtrim, tailtrim, block):
        self.leadtrim = leadtrim
        self.tailtrim = tailtrim
        self.block = block

        if not callable(self.leadtrim) or \
            not callable(self.tailtrim):
            raise TypeError("EncapsulatedLine requires callable trimmers")

    def parse(self, inp):
        logging.debug("%s, \"%s\" <nop>" % (type(self), inp))
        inp = self.leadtrim(self.tailtrim(inp))
        return self.block.parse(inp)

class MultiBlockLine(SingleBlock):
    def __init__(self, blocks, delimiter):
        self.blocks = blocks
        self.delimiter = delimiter

        for b in self.blocks:
            if not issubclass(type(b), SingleBlock):
                raise TypeError("MultiBlockLine must parse blocks")

    def parse(self, inp):
        logging.debug("%s, \"%s\"" % (type(self), inp))
        self.items = []
        for (line, b) in zip(inp.split(self.delimiter), self.blocks):
            logging.debug("\t%s" % line)
            bout = b.parse(line)
            if bout is not None:
                self.items.append(bout)

        if len(self.items) == 1:
            return self.items[0]

        return self.items

class ListBlock(SingleBlock):
    def __init__(self, elementParser, delimiter):
        self.elementParser = elementParser
        if not callable(elementParser):
            raise TypeError("List elementParser must be callable", elementParser)
        self.delimiter = delimiter

    def parse(self, inp):
        self.list = []
        logging.debug("%s, \"%s\"" % (type(self), inp))
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
        return self.list

class ListElementMunch(SingleBlock):
    def __init__(self, elements, elementParser, delimiter):
        self.elements = elements
        self.elementParser = elementParser
        self.delimiter = delimiter

        if not callable(elementParser):
            raise TypeError("List elementParser must be callable", elementParser)

    def parse(self, inp):
        self.list = []
        logging.debug("%s, \"%s\"" % (type(self), inp))
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
        return self.list

class SetBlock(ListBlock):
    def __init__(self, elementParser, delimiter):
        super().__init__(elementParser, delimiter)

    def parse(self, inp):
        tlist = super().parse(inp)
        return set(tlist)


class HashPairBlock(SingleBlock):
    def __init__(self, keyblock, valueblock, seperator, distribute=False, reverse=False):
        self.keyblock = keyblock
        self.valueblock = valueblock
        self.seperator = seperator
        self.distribute = distribute
        self.reverse = reverse

        if not callable(self.keyblock) and \
            not isinstance(self.valueblock, SingleBlock):
            raise TypeError("Keyblock must be callable or SinglBlock")

        if not callable(self.valueblock) and \
            not isinstance(self.valueblock, SingleBlock):
            raise TypeError("Valueblock must be callable or SinglBlock")

    def parse(self, inp):
        logging.debug("%s, \"%s\"" % (type(self), inp))
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

        return self.hash

class HashLineBlock(SingleBlock):
    def __init__(self, hashparser, delimiter):
        self.hashparser = hashparser
        self.delimiter = delimiter

        if not isinstance(self.hashparser, HashPairBlock):
            raise TypeError("HashLineBuilder needs HashPairBlock")

    def parse(self, inp):
        logging.debug("%s, \"%s\"" % (type(self), inp))
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
        return self.hash

class MuiltiLineBlock:
    def __init__(self):
        return

    def parse(self, inp):
        return inp

class MultiLineSpanBuilder(MuiltiLineBlock):
    def __init__(self, lineblock, seperator, endvalue):
        self.lineblock = lineblock
        self.seperator = seperator
        self.endvalue = endvalue

        if not issubclass(type(self.lineblock), SingleBlock):
            raise TypeError("SingleLineBuilder needs SingleBlock to build")

    def parse(self, infile, incLine=""):
        logging.debug("%s, \"%s\"" % (type(self), incLine))
        compositeline = incLine

        line = infile.readline().rstrip()
        while line != self.endvalue:
            compositeline += self.seperator + line
            logging.debug("%s, \"%s\"" % (type(self), compositeline))
            line = infile.readline().rstrip()

        logging.debug("%s, %s" % (type(self), compositeline))
        return self.lineblock.parse(compositeline)

class SingleLineBuilder(MuiltiLineBlock):
    def __init__(self, lineblock):
        self.lineblock = lineblock

        if not issubclass(type(self.lineblock), SingleBlock):
            raise TypeError("SingleLineBuilder needs SingleBlock to build")

    def parse(self, infile, intLine=None):
        if intLine == None:
            line = infile.readline().rstrip()
        else:
            line = intLine
        logging.debug("%s, \"%s\"" % (type(self), line))

        return self.lineblock.parse(line)

class SingleLineBuilderThrowToEnd(SingleLineBuilder):
    def __init__(self, lineblock, endvalue):
        super().__init__(lineblock)
        self.endvalue = endvalue

    def parse(self, infile, intLine=None):
        if intLine == None:
            line = infile.readline().rstrip()
        else:
            line = intLine
        logging.debug("%s, \"%s\"" % (type(self), line))

        l = super().parse(infile)
        while infile.readline().rstrip() != self.endvalue:
            continue
        return l

class MultiBuilderBuilder(MuiltiLineBlock):
    def __init__(self, blocks, endvalue):
        self.blocks = blocks
        self.endvalue = endvalue

        for b in self.blocks:
            if not isinstance(b, MuiltiLineBlock) and \
                not isinstance(b, MultiLineSpanBuilder):
                raise TypeError("MultiBuilderBuilder combines several multiline blocks")

    def parse(self, infile, intLine=None):
        if intLine == None:
            line = infile.readline().rstrip()
        else:
            line = intLine
        logging.debug("%s, \"%s\"" % (type(self), line))
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
                logging.debug("%s, \"%s\"" % (type(self), line))
            self.list += blockOut

        if len(self.list) == 1:
            return self.list[0]

        return self.list

class ListBuilder(MuiltiLineBlock):
    def __init__(self, lineblock, endvalue):
        self.lineblock = lineblock
        self.endvalue = endvalue

        if not isinstance(self.lineblock, SingleBlock) and \
            not isinstance(self.lineblock, MuiltiLineBlock) and \
            not isinstance(self.lineblock, MultiLineSpanBuilder):
            raise TypeError("Listbuilder needs SingleBlock or MultiLineSpanBuilder to build")

    def parse(self, infile, intLine=None):
        if intLine == None:
            line = infile.readline().rstrip()
        else:
            line = intLine
        logging.debug("%s, \"%s\"" % (type(self), line))
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
            logging.debug("%s, \"%s\"" % (type(self), line))

        if len(self.list) == 1:
            return self.list[0]

        return self.list

class HashBuilder(MuiltiLineBlock):
    def __init__(self, hashblock, endvalue):
        self.hashblock = hashblock
        self.endvalue = endvalue

        if not isinstance(self.hashblock, HashPairBlock):
            raise TypeError("Hashbuilder needs HashPairBlock to build")

    def parse(self, infile, intLine=None):
        if intLine == None:
            line = infile.readline().rstrip()
        else:
            line = intLine

        logging.debug("%s, \"%s\"" % (type(self), line))

        self.hash = {}
        while line != self.endvalue:
            lineH = self.hashblock.parse(line)

            self.hash.update(lineH)

            line = infile.readline().rstrip()

        return self.hash

class InputDefinition:
    def __init__(self):
        self.builders = []

    def addBuilder(self, builder):
        if not issubclass(type(builder), MuiltiLineBlock):
            raise TypeError("Builders must be MuiltiLineBlocks, use SingleLineBuilder for 1 line")
        self.builders.append(builder)

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