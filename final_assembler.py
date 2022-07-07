from typing import Optional


class Instruction:
    def __init__(self, _type: str, opcode: str, secondary_opcode: Optional[str]=None):
        self._type = _type
        self.opcode = opcode
        self.secondary_opcode = secondary_opcode

    def final_assemble(self, line: str):
        try:
            match self._type:
                case "A":
                    # add r1 r2 r5
                    _, r0, r1, r2 = line.split()
                    return f"{self.opcode}00{handle_register(r0)}{handle_register(r1)}{handle_register(r2)}"
                case "B":
                    # mov r0 $3
                    _, r0, imm = line.split()
                    return f"{self.opcode}{handle_register(r0)}{handle_immediate(imm[1:])}"
                case "C":
                    # mov r4 r5
                    _, r0, r1 = line.split()
                    return f"{self.opcode}00000{handle_register(r0)}{handle_register(r1, flags_allowed=True)}"
                case "D":
                    # ld r0 x
                    _, r0, addr = line.split()
                    return f"{self.opcode}{handle_register(r0)}{handle_address(addr)}"
                case "E":
                    # je label
                    _, addr = line.split()
                    return f"{self.opcode}000{handle_address(addr)}"
                case "F":
                    return f"{self.opcode}{'0' * 11}"
        except ValueError:
            throw_error("SyntaxError: Invalid syntax encountered in instruction")

    def assemble(self, line: str):
        if self.secondary_opcode is not None and "$" in line:
            self._type = "B"
            temp = self.opcode
            self.opcode = self.secondary_opcode
            machine_code = self.final_assemble(line)
            self._type = "C"
            self.opcode = temp
            return machine_code
        else:
            return self.final_assemble(line)


def throw_error(message: str):
    print(message)
    quit()


def handle_register(register: str, flags_allowed: Optional[bool]=False):
    if register == "FLAGS":
        if not flags_allowed:
            throw_error("FLAGSError: Illegal use of FLAGS Register")
        else:
            return "111"
    else:
        return bin(int(register.lstrip("r")))[2:].zfill(3)


def handle_immediate(immediate: str):
    if not immediate.isdigit():
        throw_error("SyntaxError: Invalid Immediate value - must be an integer")
    immediate = bin(int(immediate))[2:]
    if len(immediate) > 8:
        throw_error("OverflowError: Immediate value is too large")
    else:
        return immediate.zfill(8)


def handle_address(address: str):
    if address.isdigit():
        if set(address) != {"0", "1"}:
            throw_error("MemoryAddressError: Invalid Address used")
        if len(address) > 8:
            throw_error("MemoryAddressError: Address longer than 8 bits")
        return address
    else:
        address = VARIABLES.get(address) if address in VARIABLES else LABELS.get(address)
        if address is None:
            throw_error("AddressNotFoundError: Undeclared Variable / Label used")
        else:
            return bin(address)[2:].zfill(8)


INSTRUCTIONS: dict[str, Instruction] = {
    "ld": Instruction("D", "10100"),
    "st": Instruction("D", "10101"),
    "rs": Instruction("B", "11000"),
    "ls": Instruction("B", "11001"),
    "or": Instruction("A", "11011"),
    "je": Instruction("E", "01111"),
    "add": Instruction("A", "10000"),
    "sub": Instruction("A", "10001"),
    "mul": Instruction("A", "10110"),
    "div": Instruction("C", "10111"),
    "xor": Instruction("A", "11010"),
    "and": Instruction("A", "11100"),
    "not": Instruction("C", "11101"),
    "cmp": Instruction("C", "11110"),
    "jmp": Instruction("E", "11111"),
    "jlt": Instruction("E", "01100"),
    "jgt": Instruction("E", "01101"),
    "hlt": Instruction("F", "01010"),
    "mov": Instruction("C", "10011", "10010"),
}

MACHINE_CODE: list[str] = []

temp_code: list[str] = []
counter = 0
while True:
    try:
        line = input().strip()
    except EOFError:
        break

    if line != "":
        temp_code.append(line)
        counter += 1 if line[:3] != "var" else 0


ASSEMBLY_CODE: list[str] = []
VARIABLES: dict[str, int] = {}
program_begun = False

for line in temp_code:
    if line[:3] == "var":
        if program_begun:
            throw_error(f"SyntaxError: Variable declaration after program begins")

        variable = line.split()[1]

        if not variable.isalnum() or not (variable[0].isalpha() and variable[0] != "_"):
            throw_error("SyntaxError: Invalid Variable name")
        elif counter > 512:
            throw_error("MemoryOverflowError: 512 MB Memory Limit Exceeded")
        else:
            VARIABLES[variable] = counter
            counter += 1
    else:
        program_begun = True
        ASSEMBLY_CODE.append(line)


LABELS: dict[str, int] = {}
for i, line in enumerate(ASSEMBLY_CODE):
    if ":" in line:
        label, code = line.split(":")
        if code == "":
            throw_error(f"SyntaxError: Invalid syntax - Empty Label Declaration encountered on Line {i}")
        else:
            LABELS[label] = i


for i, line in enumerate(ASSEMBLY_CODE, start=1):
    line = line.split(":")[-1]
    operation = line.split()[0]

    if operation in INSTRUCTIONS:
        if operation == "hlt" and i != len(ASSEMBLY_CODE):
            throw_error("EOFError: 'hlt' is not the last instruction")

        if i == len(ASSEMBLY_CODE) and operation != "hlt":
            throw_error("EOFError: Missing 'hlt' instruction")

        if operation[0] == "j" and line.split()[1] in VARIABLES:
            throw_error("MemoryAddressError: Misuse of Variable as a Label")

        if operation in ["ld", "st"] and line.split()[1] in LABELS:
            throw_error("MemoryAddressError: Misuse of Label as a Variable")

        machine_code = INSTRUCTIONS[operation].assemble(line)
        MACHINE_CODE.append(machine_code)

    else:
        throw_error(f"SyntaxEror: Invalid syntax encountered on Line {i}")


for line in MACHINE_CODE:
    print(line)