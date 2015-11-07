import sys
import struct
import dis
import inspect
import re
from collections import OrderedDict

__all__ = [
    "orderedkwargs"
]


#
# Ensure we're running Python 2.7.
#

assert sys.version_info[:2] == (2, 7), "Python 2.7 required."


#
# VMOp, StackOp, CallOp, SpecialOp
#

class VMOp(object) :
    pass

class StackOp(VMOp) :
    def __init__(self, pop=0, pop_n=False, push=0, push_n=False) :
        self.pop = pop
        self.pop_n = pop_n
        self.push = push
        self.push_n = push_n

    def __repr__(self) :
        args = []
        if self.pop != 0 :
            args.append("pop=%s" % (self.pop,))
        if self.pop_n :
            args.append("pop_n=%s" % (self.pop_n,))
        if self.push != 0 :
            args.append("push=%s" % (self.push,))
        if self.push_n :
            args.append("push_n=%s" % (self.push_n,))
        return "StackOp(%s)" % (", ".join(args),)

class CallOp(VMOp) :
    def __init__(self, has_var=False, has_kw=False) :
        self.has_var = has_var
        self.has_kw = has_kw

    def __repr__(self) :
        args = []
        if self.has_var :
            args.append("has_var=%s" % (self.has_var,))
        if self.has_kw :
            args.append("has_kw=%s" % (self.has_kw,))
        return "CallOp(%s)" % (", ".join(args),)

class SpecialOp(VMOp) :
    pass


#
# Shortcuts for common ops.
#

nop = StackOp()

unary_op = StackOp(pop=1, push=1)
binary_op = StackOp(pop=2, push=1)
ternary_op = StackOp(pop=3, push=1)
nary_op = StackOp(pop_n=True, push=1)

pop1 = StackOp(pop=1)
pop2 = StackOp(pop=2)
pop3 = StackOp(pop=3)
pop4 = StackOp(pop=4)

push1 = StackOp(push=1)

special = SpecialOp()


#
# Opcode info
#

opcode_info = dict([
    ("BINARY_ADD", binary_op),
    ("BINARY_AND", binary_op),
    ("BINARY_DIVIDE", binary_op),
    ("BINARY_FLOOR_DIVIDE", binary_op),
    ("BINARY_LSHIFT", binary_op),
    ("BINARY_MODULO", binary_op),
    ("BINARY_MULTIPLY", binary_op),
    ("BINARY_OR", binary_op),
    ("BINARY_POWER", binary_op),
    ("BINARY_RSHIFT", binary_op),
    ("BINARY_SUBSCR", binary_op),
    ("BINARY_SUBTRACT", binary_op),
    ("BINARY_TRUE_DIVIDE", binary_op),
    ("BINARY_XOR", binary_op),
    ("BREAK_LOOP", special),
    ("BUILD_CLASS", ternary_op),
    ("BUILD_LIST", nary_op),
    ("BUILD_MAP", push1),
    ("BUILD_SET", nary_op),
    ("BUILD_SLICE", nary_op),
    ("BUILD_TUPLE", nary_op),
    ("CALL_FUNCTION", CallOp()),
    ("CALL_FUNCTION_KW", CallOp(has_kw=True)),
    ("CALL_FUNCTION_VAR", CallOp(has_var=True)),
    ("CALL_FUNCTION_VAR_KW", CallOp(has_var=True, has_kw=True)),
    ("COMPARE_OP", binary_op),
    ("CONTINUE_LOOP", special),
    ("DELETE_ATTR", pop1),
    ("DELETE_FAST", nop),
    ("DELETE_GLOBAL", nop),
    ("DELETE_NAME", nop),
    ("DELETE_SLICE+0", pop1),
    ("DELETE_SLICE+1", pop2),
    ("DELETE_SLICE+2", pop2),
    ("DELETE_SLICE+3", pop3),
    ("DELETE_SUBSCR", pop2),
    ("DUP_TOP", push1),
    ("DUP_TOPX", StackOp(push_n=True)),
    ("END_FINALLY", special),
    ("EXEC_STMT", pop3),
    ("EXTENDED_ARG", special),
    ("FOR_ITER", special),
    ("GET_ITER", unary_op),
    ("IMPORT_FROM", push1),
    ("IMPORT_NAME", binary_op),
    ("IMPORT_STAR", pop1),
    ("INPLACE_ADD", binary_op),
    ("INPLACE_AND", binary_op),
    ("INPLACE_DIVIDE", binary_op),
    ("INPLACE_FLOOR_DIVIDE", binary_op),
    ("INPLACE_LSHIFT", binary_op),
    ("INPLACE_MODULO", binary_op),
    ("INPLACE_MULTIPLY", binary_op),
    ("INPLACE_OR", binary_op),
    ("INPLACE_POWER", binary_op),
    ("INPLACE_RSHIFT", binary_op),
    ("INPLACE_SUBTRACT", binary_op),
    ("INPLACE_TRUE_DIVIDE", binary_op),
    ("INPLACE_XOR", binary_op),
    ("JUMP_ABSOLUTE", special),
    ("JUMP_FORWARD", special),
    ("JUMP_IF_FALSE_OR_POP", special),
    ("JUMP_IF_TRUE_OR_POP", special),
    ("LIST_APPEND", pop1),
    ("LOAD_ATTR", unary_op),
    ("LOAD_CLOSURE", push1),
    ("LOAD_CONST", push1),
    ("LOAD_DEREF", push1),
    ("LOAD_FAST", push1),
    ("LOAD_GLOBAL", push1),
    ("LOAD_LOCALS", push1),
    ("LOAD_NAME", push1),
    ("MAKE_CLOSURE", StackOp(pop=2, pop_n=True, push=1)),
    ("MAKE_FUNCTION", StackOp(pop=1, pop_n=True, push=1)),
    ("MAP_ADD", pop2),
    ("NOP", nop),
    ("POP_BLOCK", pop1),
    ("POP_JUMP_IF_FALSE", special),
    ("POP_JUMP_IF_TRUE", special),
    ("POP_TOP", pop1),
    ("PRINT_EXPR", pop1),
    ("PRINT_ITEM", pop1),
    ("PRINT_ITEM_TO", pop2),
    ("PRINT_NEWLINE", nop),
    ("PRINT_NEWLINE_TO", pop1),
    ("RAISE_VARARGS", special),
    ("RETURN_VALUE", special),
    ("ROT_FOUR", StackOp(pop=4, push=4)),
    ("ROT_THREE", StackOp(pop=3, push=3)),
    ("ROT_TWO", StackOp(pop=2, push=2)),
    ("SETUP_EXCEPT", special),
    ("SETUP_FINALLY", special),
    ("SETUP_LOOP", special),
    ("SETUP_WITH", special),
    ("SET_ADD", pop1),
    ("SLICE+0", unary_op),
    ("SLICE+1", binary_op),
    ("SLICE+2", binary_op),
    ("SLICE+3", ternary_op),
    ("STOP_CODE", special),
    ("STORE_ATTR", pop2),
    ("STORE_DEREF", pop1),
    ("STORE_FAST", pop1),
    ("STORE_GLOBAL", pop1),
    ("STORE_MAP", pop2),
    ("STORE_NAME", pop1),
    ("STORE_SLICE+0", pop2),
    ("STORE_SLICE+1", pop3),
    ("STORE_SLICE+2", pop3),
    ("STORE_SLICE+3", pop4),
    ("STORE_SUBSCR", pop3),
    ("UNARY_CONVERT", unary_op),
    ("UNARY_INVERT", unary_op),
    ("UNARY_NEGATIVE", unary_op),
    ("UNARY_NOT", unary_op),
    ("UNARY_POSITIVE", unary_op),
    ("UNPACK_SEQUENCE", StackOp(pop=1, push_n=True)),
    ("WITH_CLEANUP", special),
    ("YIELD_VALUE", special)
])


#
# opcode_names
#

def init_opcode_names() :
    return dict([(code, name) for name, code in dis.opmap.items()])

opcode_names = init_opcode_names()


#
# Special instructions
#

LOAD_CONST = dis.opmap["LOAD_CONST"]

EXTENDED_ARG = dis.opmap["EXTENDED_ARG"]

# has absolute jump
JUMP_IF_FALSE_OR_POP = dis.opmap["JUMP_IF_FALSE_OR_POP"]
JUMP_IF_TRUE_OR_POP = dis.opmap["JUMP_IF_TRUE_OR_POP"]
JUMP_ABSOLUTE = dis.opmap["JUMP_ABSOLUTE"]
POP_JUMP_IF_FALSE = dis.opmap["POP_JUMP_IF_FALSE"]
POP_JUMP_IF_TRUE = dis.opmap["POP_JUMP_IF_TRUE"]
CONTINUE_LOOP = dis.opmap["CONTINUE_LOOP"]

# has relative jump
FOR_ITER = dis.opmap["FOR_ITER"]
JUMP_FORWARD = dis.opmap["JUMP_FORWARD"]
SETUP_LOOP = dis.opmap["SETUP_LOOP"]
SETUP_EXCEPT = dis.opmap["SETUP_EXCEPT"]
SETUP_FINALLY = dis.opmap["SETUP_FINALLY"]
SETUP_WITH = dis.opmap["SETUP_WITH"]

# other specials
END_FINALLY = dis.opmap["END_FINALLY"]
RETURN_VALUE = dis.opmap["RETURN_VALUE"]
BREAK_LOOP = dis.opmap["BREAK_LOOP"]
WITH_CLEANUP = dis.opmap["WITH_CLEANUP"]
RAISE_VARARGS = dis.opmap["RAISE_VARARGS"]
STOP_CODE = dis.opmap["STOP_CODE"]


jabs_opcodes = set([
    JUMP_IF_FALSE_OR_POP,
    JUMP_IF_TRUE_OR_POP,
    JUMP_ABSOLUTE,
    POP_JUMP_IF_FALSE,
    POP_JUMP_IF_TRUE,
    CONTINUE_LOOP
])

jabs_conditional_opcodes = set([
    JUMP_IF_FALSE_OR_POP,
    JUMP_IF_TRUE_OR_POP,
    POP_JUMP_IF_FALSE,
    POP_JUMP_IF_TRUE,
])

jrel_opcodes = set([
    FOR_ITER,
    JUMP_FORWARD,
    SETUP_LOOP,
    SETUP_EXCEPT,
    SETUP_FINALLY,
    SETUP_WITH
])

special_opcodes = set([
    EXTENDED_ARG,

    SETUP_EXCEPT,
    SETUP_FINALLY,
    END_FINALLY,

    SETUP_LOOP,
    FOR_ITER,
    CONTINUE_LOOP,
    BREAK_LOOP,

    SETUP_WITH,
    WITH_CLEANUP,

    RETURN_VALUE,
    RAISE_VARARGS,
    STOP_CODE,

    POP_JUMP_IF_FALSE,
    POP_JUMP_IF_TRUE,
    JUMP_IF_FALSE_OR_POP,
    JUMP_IF_TRUE_OR_POP,
    JUMP_ABSOLUTE,
    JUMP_FORWARD
])


#
# Instruction
#

class Instruction(object) :
    def __init__(self, offset, opcode, argument) :
        self.offset = offset
        self.opcode = opcode
        self.argument = argument
        self.name = opcode_names[self.opcode]
        self.length = 1
        if self.argument is None :
            self.length += 2
            if self.argument >= 65536 :
                self.length += 3

    def __repr__(self) :
        values = [self.offset, self.name]
        if self.argument is not None :
            values.append(self.argument)
        return repr(values)


#
# parse_bytecode
#

def parse_bytecode(bytes) :
    instructions = []
    offset = 0
    extended_arg = None
    while offset < len(bytes) :
        opcode = ord(bytes[offset])
        argument = None
        next_offset = None
        if opcode >= dis.HAVE_ARGUMENT :
            assert offset + 3 <= len(bytes)
            argument_bytes = bytes[offset+1:offset+3]
            argument = struct.unpack("<H", argument_bytes)[0]
            next_offset = offset + 3
            if extended_arg is not None :
                argument += (extended_arg * 65536)
                extended_arg = None
                offset = offset - 3
        else :
            assert extended_arg is None
            next_offset = offset + 1
        if opcode == EXTENDED_ARG :
            assert extended_arg is None
            extended_arg = argument
            offset = next_offset
            continue
        instruction = Instruction(offset, opcode, argument)
        instructions.append(instruction)
        offset = next_offset
    assert extended_arg is None
    return instructions


#
# StackInspector
#

def stack_pop(stack) :
    #
    # Allow stack underflow
    # as the code block being processed
    # might begin with an assumption of a non-empty stack
    #
    if len(stack) > 0 :
        stack.pop()

class StackInspector(object) :
    def __init__(self, code, target_offset) :
        self.code = code
        self.target_offset = target_offset
        self.instructions = parse_bytecode(code.co_code)
        self.offset_map = {}
        for i, inst in enumerate(self.instructions) :
            self.offset_map[inst.offset] = i
        self.target_index = self.offset_map[self.target_offset]

    def find_block_begin(self, index) :
        while index > 0 :
            prev = self.instructions[index - 1]
            if isinstance(opcode_info[prev.name], SpecialOp) :
                break
            index -= 1
        return index

    def apply_pop_push(self, stack, pop, push) :
        for _ in range(pop) :
            stack_pop(stack)
        for _ in range(push) :
            stack.append(None)

    def apply_stack_op(self, op, inst, stack) :
        pop = op.pop
        if op.pop_n :
            pop += inst.argument
        push = op.push
        if op.push_n :
            push += inst.argument
        self.apply_pop_push(stack, pop, push)

    def apply_call_op(self, op, inst, stack) :
        positional_args = inst.argument % 256
        keyword_args = inst.argument / 256
        pop = 1 + positional_args + 2 * keyword_args
        if op.has_var :
            pop += 1
        if op.has_kw :
            pop += 1
        push = 1
        self.apply_pop_push(stack, pop, push)

    def apply_effect(self, inst, stack) :
        if inst.opcode == LOAD_CONST :
            stack.append(self.code.co_consts[inst.argument])
            return
        op = opcode_info[inst.name]
        if isinstance(op, StackOp) :
            self.apply_stack_op(op, inst, stack)
        elif isinstance(op, CallOp) :
            self.apply_call_op(op, inst, stack)
        else :
            assert False

    def build_stack(self) :
        end = self.target_index
        begin = self.find_block_begin(end)
        stack = []
        for inst in self.instructions[begin:end] :
            self.apply_effect(inst, stack)
        return stack

    def find_keyword_names(self) :
        stack = self.build_stack()
        inst = self.instructions[self.target_index]
        op = opcode_info[inst.name]
        assert isinstance(op, CallOp)
        positional_args = inst.argument % 256
        keyword_args = inst.argument / 256
        required = positional_args + 2 * keyword_args
        if op.has_var :
            required += 1
        if op.has_kw :
            required += 1
        assert len(stack) >= required
        if op.has_var :
            stack_pop(stack)
        if op.has_kw :
            stack_pop(stack)
        keyword_names = []
        for i in range(keyword_args) :
            j = keyword_args - i - 1
            k = len(stack) - 2*(j + 1)
            keyword_names.append(stack[k])
        return keyword_names


#
# orderedkwargs
#

def orderedkwargs(f) :
    def inner(*args, **kwargs) :
        caller = inspect.stack()[1]
        frame = caller[0]
        inspector = StackInspector(frame.f_code, frame.f_lasti)
        keywords = inspector.find_keyword_names()
        all_args = inspect.getargspec(f)
        default_names = all_args.args[-len(all_args.defaults):]
        defaults = {}
        ordered_kwargs = OrderedDict()
        for key in keywords :
            value = kwargs.pop(key)
            if key in default_names:
                defaults[key] = value
            else:
                ordered_kwargs[key] = value
        return f(*args, kwargs=ordered_kwargs, **defaults)
    return inner
