import os, sys, re, argparse
from xml.etree import ElementTree as ET

# Class for storing instructions and their arguments
class Token:
    def __init__(self, order, opcode, arg_num=0,
                arg1=None, arg2=None, arg3=None):
        self.ord = order
        self.opcode = opcode
        self.arg_num = arg_num
        self.arg = {1: arg1, 2: arg2, 3: arg3} # type: Dict[Dict['type': x, 'val': y], ...]

    def semantics(self, type):
        self.semantic_type = type

    def order(self):
        if self.ord < 1:
            sys.exit(32)
        return self.ord

    def __str__(self):
        str = '%d\t%s\t' % (self.ord, self.opcode)
        for x in range(self.arg_num):
            str += self.arg[x+1]['val'] + '\t'
        return str

    def __repr__(self):
        if self.opcode == 'LABEL':
            return '%s %s' % (self.opcode, self.arg[1]['val'])
        else:
            return '%s' % (self.opcode)

# Initialization of required data structures
class Initialize:
     def __init__(self,  xml_root, cmd_input=[], lang=''):
        self.xml_root = xml_root
        self.cmd_input = cmd_input.reverse()

        if lang != '':
            if self.xml_root.attrib['language'] != lang:
                print('Chyba, zly jazyk.')
                sys.exit(32)
        
        self.frames = {'GF': dict(), 'LF': [], 'TF': None}
        self.stack = []

        self.tokens = [] # type: List[Token]
        self.position = 0
        self.labels = dict()

# Implementation of semantic analyze and helper functions
class Semantics_Tools(Initialize):
    class Uninitialized:
        pass
    class NonExistent:
        pass
    # SEMANTICS
    def _noparam(self, token):
        if token.arg[1] or token.arg[2] or token.arg[3]:
            sys.exit(32) 
    
    def _1param(self, token):
        if token.arg[1] is None or token.arg[2] or token.arg[3]:
            sys.exit(32) 

    def _2param(self, token):
        if token.arg[1] is None or token.arg[2] is None or token.arg[3]:
            sys.exit(32)

    def _3param(self, token):
        if token.arg[1] is None or token.arg[2] is None or token.arg[3] is None:
            sys.exit(32)

    def _label(self, token, existence=False):
        try:
            type = token.arg[1]['type']
        except TypeError:
            sys.exit(32) 
        
        if type != 'label':
            sys.exit(53)
        
        if existence == True:
            if token.arg[1]['val'] not in self.labels:
                sys.exit(52) 

        return token.arg[1]['val']

    def _var(self, token, pos=1, existence=False, crash=True):
        try:
            type = token.arg[pos]['type']
        except TypeError:
            sys.exit(32)

        if type != 'var':
            sys.exit(53) 

        try:
            frame, val = token.arg[pos]['val'].split('@')
        except ValueError:
            sys.exit(32) 

        regex = r"^[a-zA-Z_\-$&%*!?][a-zA-Z0-9_\-$&%*!?]*$"
        matches = re.search(regex, val)
        if matches is None:
            sys.exit(32)
        
        if frame == 'GF':
            if existence:
                if val not in self.frames['GF']:
                    if crash is True:
                        sys.exit(54) 
                    else:
                        return None

        elif frame == 'LF':
            if existence:
                if val not in self.frames['LF'][-1]:
                    if crash is True:
                        sys.exit(54)
                    else:
                        return None

        elif frame == 'TF':
            if self.frames['TF'] is not None:
                if existence:
                    if val not in self.frames['TF']:
                        if crash is True:
                            sys.exit(54) 
                        else:
                            return None
            else:
                sys.exit(55) 
    
        else:
            sys.exit(55) 
        
        return frame, val
    
    def _symb(self, token, pos=1, existence=True, crash=True):
        try:
            type = token.arg[pos]['type']
        except TypeError:
            sys.exit(32)

        if type == 'var':
            return self._var(token, pos, existence, crash)
        elif type == 'int' or type == 'bool' or type == 'string' or type == 'nil': # !!!
            try:
                if type == 'int':
                    value = int(token.arg[pos]['val'])
                
                elif type == 'bool':
                    x = (token.arg[pos]['val'])
                    if x == 'true':
                        value = True
                    elif x == 'false':
                        value = False
                    else:
                        sys.exit(57) 
                
                elif type == 'string':
                    value = str(token.arg[pos]['val'])
                
                elif type == 'nil':
                    val = str(token.arg[pos]['val'])
                    if type == 'nil' and val != 'nil':
                        sys.exit(57) 
                    value = None

            except Exception:
                sys.exit(32) 
            return type, value
        else:
            sys.exit(32) 

    def _type(self, token, pos=2):
        if token.arg[pos]['type'] == 'type':
            val = token.arg[pos]['val']
            if val == 'int' or val == 'string' or val == 'bool':
                return val
            else:
                sys.exit(53) 
        else:
            sys.exit(32) 
    
    def _comparisons(self, token, type='all'):
        frame_or_type1, val1 = self._symb(token, pos=2, existence=True)
        frame_or_type2, val2 = self._symb(token, pos=3, existence=True)
        value1 = self.get_val(frame_or_type1, val1)
        value2 = self.get_val(frame_or_type2, val2)
        if type == 'int':
            if not isinstance(value1, int) or not isinstance(value2, int):
                sys.exit(53) 
        if type == 'string':
            if not isinstance(value1, str) or not isinstance(value2, str):
                sys.exit(53) 
        elif type == 'bool':
            if not isinstance(value1, bool) or not isinstance(value2, bool):
                sys.exit(53)
        elif type == 'all':
            if not ((isinstance(value1, int) is isinstance(value2, int))
                or (isinstance(value1, str) is isinstance(value2, str))
                or (isinstance(value1, bool) is isinstance(value2, bool))
                or (value1 is None and value2 is None)
            ):
                sys.exit(53) 
        return value1, value2

    # TOOLS
    def code_to_ascii(self, string):
        def int_replace(match):
            return str(chr(int(match.group(1))))
        return re.sub(r"\\([0-9]{3})", int_replace, string)

    def insert_to(self, frame, key, source=None, val=Uninitialized):
        if source == 'GF' or source == 'LF' or source == 'TF':
            if frame == 'GF' or frame == 'TF':
                if source == 'GF' or source == 'TF':
                    self.frames[frame][key] = self.frames[source][val]
                else:
                    self.frames[frame][key] = self.frames['LF'][-1][val]
            else:
                if source == 'GF' or source == 'TF':
                    self.frames['LF'][-1][key] = self.frames[source][val]
                else:
                    self.frames['LF'][-1][key] = self.frames['LF'][-1][val]
        else:
            if frame == 'GF' or frame == 'TF':
                self.frames[frame][key] = val
            else:
                self.frames['LF'][-1][key] = val

    def get_val(self, frame, key_or_val, exists=True):
        try:
            if frame == 'GF' or frame == 'TF':
                return self.frames[frame][key_or_val]
            elif frame == 'LF':
                return self.frames[frame][-1][key_or_val]
            else:
                return key_or_val
        except KeyError:
            if exists is True:
                sys.exit(54)
            else:
                return self.NonExistent()

# Implementation of instructions
class Instructions(Semantics_Tools):
    def __init__(self, xml_root, cmd_input=[], lang=''):
        super().__init__(xml_root, cmd_input, lang)
        self.instructions = [
            'MOVE', 'CREATEFRAME', 'PUSHFRAME', 'POPFRAME', 'DEFVAR', 'CALL', 'RETURN', 'POPS', 'PUSHS', 
            'ADD', 'SUB', 'MUL', 'IDIV', 'LT', 'GT', 'EQ', 'AND', 'OR', 'NOT', 'INT2CHAR', 'STRI2INT',
            'READ', 'WRITE', 'CONCAT', 'STRLEN', 'GETCHAR', 'SETCHAR', 'TYPE',
            'LABEL', 'JUMP', 'JUMPIFEQ', 'JUMPIFNEQ', 'EXIT', 'DPRINT', 'BREAK'
        ]

    def DEFVAR(self, token):
        self._1param(token)
        frame, key = self._var(token)
        val = self.get_val(frame, key, exists=False)
        if isinstance(val, self.NonExistent):
            self.insert_to(frame, key)
        else:
            sys.exit(52) 

    def CREATEFRAME(self, token):
        self._noparam(token)
        self.frames['TF'] = dict()
    
    def PUSHFRAME(self, token):
        self._noparam(token)
        if self.frames['TF']:
            self.frames['LF'].append(self.frames['TF'])
            self.frames['TF'] = None
        else:
            sys.exit(55)
    
    def POPFRAME(self, token):
        self._noparam(token)
        if self.frames['LF']:
            self.frames['TF'] = self.frames['LF'].pop()
        else:
            sys.exit(55)

    def MOVE(self, token):
        self._2param(token)
        frame, key = self._var(token)
        frame_or_type, val = self._symb(token, pos=2)
        self.insert_to(frame, key, frame_or_type, val)

    def PUSHS(self, token):
        self._1param(token)
        frame_or_type, val = self._symb(token)
        self.stack.append(self.get_val(frame_or_type, val))
    
    def POPS(self, token):
        self._1param(token)
        if not self.stack:
            sys.exit(56) # prazdny stack
        frame, key = self._var(token, existence=True)
        self.insert_to(frame, key, val=self.stack.pop())

    def WRITE(self, token):
        self._1param(token)
        frame_or_type, val = self._symb(token)
        value = self.get_val(frame_or_type, val)
        if value is self.Uninitialized:
            sys.exit(56)
        if value is None:
            return
        if value is True:
            value = 'true'
        elif value is False:
            value = 'false'
        print(self.code_to_ascii(str(value)), end='')

    def READ(self, token):
        self._2param(token)
        frame, key = self._var(token)
        type = self._type(token)
        if self.cmd_input:
            x = self.cmd_input.pop()
        else:
            x = input()

        if x == '':
            value = None
        else:
            try:
                if type == 'int':
                    value = int(x)
                elif type == 'string':
                    value = str(x)
                elif type == 'bool':
                    if x == 'true':
                        value = True
                    else:
                        value = False
                else:
                    sys.exit(32) 
            except Exception:
                sys.exit(53)
        
        self.insert_to(frame, key, val=value)

    def CALL(self, token):
        self._1param(token)
        label = self._label(token, existence=True)
        self.stack.append(self.position)
        self.position = self.labels[label]

    def RETURN(self, token):
        self._noparam(token)
        if not self.stack:
            sys.exit(56)

        pos = self.stack.pop()
        if isinstance(pos, int):
            self.position = pos
        else:
            sys.exit(57)

    def ADD(self, token):
        self._3param(token)
        frame, key = self._var(token)
        value1, value2 = self._comparisons(token, type='int')
        self.insert_to(frame, key, val=(value1 + value2))

    def SUB(self, token):
        self._3param(token)
        frame, key = self._var(token)
        value1, value2 = self._comparisons(token, type='int')
        self.insert_to(frame, key, val=(value1 - value2))

    def MUL(self, token):
        self._3param(token)
        frame, key = self._var(token)
        value1, value2 = self._comparisons(token, type='int')
        self.insert_to(frame, key, val=(value1 * value2))

    def IDIV(self, token):
        self._3param(token)
        frame, key = self._var(token)
        value1, value2 = self._comparisons(token, type='int')
        if value2 == 0:
            sys.exit(57) # delenie nulou
        self.insert_to(frame, key, val=(value1 // value2))
    
    def LT(self, token):
        self._3param(token)
        frame, key = self._var(token)
        value1, value2 = self._comparisons(token)
        if value1 is None or value2 is None:
            sys.exit(53)
        self.insert_to(frame, key, val=(value1 < value2))

    def GT(self, token):
        self._3param(token)
        frame, key = self._var(token)
        value1, value2 = self._comparisons(token)
        if value1 is None or value2 is None:
            sys.exit(53)
        self.insert_to(frame, key, val=(value1 < value2))
    
    def EQ(self, token):
        self._3param(token)
        frame, key = self._var(token)
        value1, value2 = self._comparisons(token)
        self.insert_to(frame, key, val=(value1 == value2))

    def AND(self, token):
        self._3param(token)
        frame, key = self._var(token)
        value1, value2 = self._comparisons(token, type='bool')
        self.insert_to(frame, key, val=(value1 and value2))

    def OR(self, token):
        self._3param(token)
        frame, key = self._var(token)
        value1, value2 = self._comparisons(token, type='bool')
        self.insert_to(frame, key, val=(value1 or value2))

    def NOT(self, token):
        self._2param(token)
        frame, key = self._var(token)
        frame_or_type, val = self._symb(token, pos=2, existence=True)
        value = self.get_val(frame_or_type, val)
        if not isinstance(value, bool):
            sys.exit(53) # zly typ operandu
        self.insert_to(frame, key, val=(not value))
    
    def INT2CHAR(self, token):
        self._2param(token)
        frame, key = self._var(token)
        frame_or_type, val = self._symb(token, pos=2, existence=True)
        value = self.get_val(frame_or_type, val)
        if not isinstance(value, int):
            sys.exit(53) # zly typ operandu
        try:
            result = chr(value)
        except ValueError:
            sys.exit(58) # nespravna hodnota
        self.insert_to(frame, key, val=result)

    def STRI2INT(self, token):
        self._3param(token)
        frame, key = self._var(token)
        frame_or_type1, val1 = self._symb(token, pos=2, existence=True)
        frame_or_type2, val2 = self._symb(token, pos=3, existence=True)
        string = self.get_val(frame_or_type1, val1)
        position = self.get_val(frame_or_type2, val2)
        if not isinstance(string, str) or not isinstance(position, int):
            sys.exit(53) 
        try:
            value = ord(string[position])
        except ValueError:
            sys.exit(58) 
        self.insert_to(frame, key, val=value)

    def CONCAT(self, token):
        self._3param(token)
        frame, key = self._var(token)
        value1, value2 = self._comparisons(token, type='string')
        self.insert_to(frame, key, val=(value1 + value2))

    def STRLEN(self, token):
        self._2param(token)
        frame, key = self._var(token)
        frame_or_type, val = self._symb(token, pos=2, existence=True)
        string = self.get_val(frame_or_type, val)
        if not isinstance(string, str):
            sys.exit(53) 
        value = len(self.code_to_ascii(string))
        self.insert_to(frame, key, val=value)

    def GETCHAR(self, token):
        self._3param(token)
        frame, key = self._var(token)
        frame_or_type1, val1 = self._symb(token, pos=2, existence=True)
        frame_or_type2, val2 = self._symb(token, pos=3, existence=True)
        string = self.get_val(frame_or_type1, val1)
        position = self.get_val(frame_or_type2, val2)
        if not isinstance(string, str) or not isinstance(position, int):
            sys.exit(53) 
        try:
            value = string[position]
        except ValueError:
            sys.exit(58) 
        self.insert_to(frame, key, val=value)

    def SETCHAR(self, token):
        self._3param(token)
        frame, key = self._var(token)
        frame_or_type1, val1 = self._symb(token, pos=2, existence=True)
        frame_or_type2, val2 = self._symb(token, pos=3, existence=True)
        string = self.get_val(frame, key)
        position = self.get_val(frame_or_type1, val1)
        char = self.get_val(frame_or_type2, val2)

        if not isinstance(string, str) or not isinstance(position, int) or not isinstance(char, str):
            sys.exit(53) 
        try:
            string[position] = char[0]
        except ValueError:
            sys.exit(58) 
        self.insert_to(frame, key, val=string)

    def TYPE(self, token):
        self._2param(token)
        frame, key = self._var(token)
        frame_or_type, val = self._symb(token, pos=2, existence=True)
        value = self.get_val(frame_or_type, val)
        if isinstance(value, int):
            result = 'int'
        elif isinstance(value, str):
            result = 'string'
        elif isinstance(value, bool):
            result = 'bool'
        elif value is None:
            result = 'nil'
        elif value is self.Uninitialized:
            result = ''
        else:
            sys.exit(53)
        self.insert_to(frame, key, val=result)

    def LABEL(self, token):
        self._1param(token)
        label = self._label(token) #
        if label in self.labels:
            sys.exit(52) # redefinicia labelu
        self.labels[label] = self.position - 1
  
    def JUMP(self, token):
        self._1param(token)
        label = self._label(token, existence=True)
        self.position = self.labels[label]

    def JUMPIFEQ(self, token):
        self._3param(token)
        label = self._label(token, existence=True)
        value1, value2 = self._comparisons(token, type='all')
        if value1 == value2:
            self.position = self.labels[label]
    
    def JUMPIFNEQ(self, token):
        self._3param(token)
        label = self._label(token, existence=True)
        value1, value2 = self._comparisons(token, type='all')
        if value1 != value2:
            self.position = self.labels[label]

    def EXIT(self, token):
        self._1param(token)
        frame_or_type, val = self._symb(token)
        value = self.get_val(frame_or_type, val)
        if isinstance(value, int) and value >= 0 and value <= 49:
            sys.exit(val)
        else:
            sys.exit(57)

    def DPRINT(self, token):
        pass

    def BREAK(self, token):
        pass

class Interpreter(Instructions):
    def __init__(self, xml_root, cmd_input=[], lang=''):
        super().__init__(xml_root, cmd_input, lang)
        self.parse()

    def parse(self):
        for i in self.xml_root:
            if i.tag != 'instruction':
                sys.exit(32)
            self.tokens.append(self.tokenize(i))
        if self.tokens:
            self.tokens.sort(key=lambda token: token.order())
            no_duplicates = [tok.ord for tok in self.tokens]
            if len(no_duplicates) != len(set(no_duplicates)):
                sys.exit(32) # duplikaty v poradi
            self.labelize()
        
    def labelize(self, op_label='LABEL'):
        result = []
        for token in self.tokens:
            if token.opcode == op_label:
                label = getattr(self, token.opcode)
                label(token)
            else:
                result.append(token)
                self.position += 1
        self.position = 0
        self.tokens = result

    def tokenize(self, xml_instruction):
        arg1, arg2, arg3, arg_num = None, None, None, 0
        for i, arg in enumerate(xml_instruction, start=1):
            if arg.tag == 'arg1':
                arg1 = {'type': arg.attrib['type'], 'val': arg.text}
            elif arg.tag == 'arg2':
                arg2 = {'type': arg.attrib['type'], 'val': arg.text}
            elif arg.tag == 'arg3':
                arg3 = {'type': arg.attrib['type'], 'val': arg.text}
            else:
                sys.exit(32) 
            arg_num = i

        try:
            _ = int(xml_instruction.attrib['order'])
            _ = xml_instruction.attrib['opcode']
        except Exception:
            sys.exit(32)
        
        return Token(int(xml_instruction.attrib['order']), xml_instruction.attrib['opcode'].upper(),
                    arg_num, arg1, arg2, arg3
                )

    def interpret(self):
        if self.tokens:
            while self.position < len(self.tokens):
                token = self.tokens[self.position]
                self.instruction_check(token)
                if not hasattr(self, token.opcode):
                    print('Neimplementovana instrukcia %s' % (token.opcode))
                    continue
                method = getattr(self, token.opcode)
                method(token)
                self.position += 1 
        else:
            print('Ziadne instrukcie.')

    def instruction_check(self, token):
        if token.opcode not in self.instructions:
            sys.exit(32)

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(11, 'Zo suboru nejde citat / subor neexistuje.')

# Argument parsing
def arg_parse(args='help source= input='):
    parser = ArgumentParser(allow_abbrev=False)
    parser.add_argument('--source', type=argparse.FileType('r'))
    parser.add_argument('--input', type=argparse.FileType('r'))
    args = parser.parse_args()

    if args.source and args.input:
        xml_source = args.source.read()
        cmd_input_raw = args.input.read()
    elif args.source:
        xml_source = args.source.read()
        cmd_input_raw = ''
    elif args.input:
        cmd_input_raw = args.input.read()
        xml_source = sys.stdin.read()
    else:
        print('Chybajuci argument.')
        sys.exit(10)

    return xml_source, cmd_input_raw.splitlines()

# Debug info
def debug():
    print('\n--- Debug ---\nGF:\t', interpreter.frames['GF'])
    print('LF:\t', interpreter.frames['LF'])
    print('TF:\t', interpreter.frames['TF'])
    print('stack:\t', interpreter.stack)
    print('\ntokens:\t', interpreter.tokens[:interpreter.position+1])
    print('pos:\t', interpreter.position)
    print('labels:\t', interpreter.labels)
    print('\nexit code: ' , end='')

if __name__ == "__main__":
    # Debug switch
    DEBUG = False
    # Loads XML source and input
    xml_source, cmd_input = arg_parse()
    # Loads XML
    try: 
        xml = ET.fromstring(xml_source)
    except Exception:
        sys.exit(31)
    # Initializes interpreter
    interpreter = Interpreter(xml, cmd_input, 'IPPcode20')
    # Runs interpreter
    try:
        interpreter.interpret()
    finally:
        if DEBUG == True:
            debug()
    sys.exit(0)