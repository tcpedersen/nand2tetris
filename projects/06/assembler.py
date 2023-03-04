import sys
import re


COMP_MAP = {
    '0'  : ('0', '101010'),
    '1'  : ('0', '111111'),
    '-1' : ('0', '111010'),
    'D'  : ('0', '001100'),
    'A'  : ('0', '110000'),
    'M'  : ('1', '110000'),
    '!D' : ('0', '001101'),
    '!A' : ('0', '110001'),
    '!M' : ('1', '110001'),
    '-D' : ('0', '001111'),
    '-A' : ('0', '110011'),
    '-M' : ('1', '110011'),
    'D+1': ('0', '011111'),
    'A+1': ('0', '110111'),
    'M+1': ('1', '110111'),
    'D-1': ('0', '001110'),
    'A-1': ('0', '110010'),
    'M-1': ('1', '110010'),
    'D+A': ('0', '000010'),
    'D+M': ('1', '000010'),
    'D-A': ('0', '010011'),
    'D-M': ('1', '010011'),
    'A-D': ('0', '000111'),
    'M-D': ('1', '000111'),
    'D&A': ('0', '000000'),
    'D&M': ('1', '000000'),
    'D|A': ('0', '010101'),
    'D|M': ('1', '010101'),
}


DEST_MAP = {
    'M'  : '001',
    'D'  : '010',
    'MD' : '011',
    'A'  : '100',
    'AM' : '101',
    'AD' : '110',
    'AMD': '111',
}


JUMP_MAP = {
    'JGT': '001',
    'JEQ': '010',
    'JGE': '011',
    'JLT': '100',
    'JNE': '101',
    'JLE': '110',
    'JMP': '111',
}


SYMBOL_TABLE = {
    'SP': '0',
    'LCL': '1',
    'ARG': '2',
    'THIS': '3',
    'THAT': '4',
    'R0': '0',
    'R1': '1',
    'R2': '2',
    'R3': '3',
    'R4': '4',
    'R5': '5',
    'R6': '6',
    'R7': '7',
    'R8': '8',
    'R9': '9',
    'R10': '10',
    'R11': '11',
    'R12': '12',
    'R13': '13',
    'R14': '14',
    'R15': '15',
    'SCREEN': '16384',
    'KBD': '24576',
}


def handle_ainstr(instr):
    return f'0{int(instr):015b}'


def handle_comp(comp):
    return f'{COMP_MAP[comp][0]}{COMP_MAP[comp][1]}'


def handle_dest(dest):
    if dest is None:
        return '000'
    return f'{DEST_MAP[dest]}'


def handle_jump(jump):
    if jump is None:
        return '000'
    return f'{JUMP_MAP[jump]}'


def handle_cinstr(comp, dest, jump):
    return f'111{handle_comp(comp)}{handle_dest(dest)}{handle_jump(jump)}'


def assemble_single_line(asm_instruction):
    is_a_instruction = re.match(r'^@([0-9]+)', asm_instruction)
    if is_a_instruction:
        return handle_ainstr(is_a_instruction.groups()[0])

    is_c_instruction = re.match(r'([AMD]+)=([^;]+);([A-Z]{3})', asm_instruction)
    if is_c_instruction:
        dest, comp, jump = is_c_instruction.groups()
        return handle_cinstr(comp, dest, jump)
 
    is_c_instruction = re.match(r'([AMD]+)=([^;]+)', asm_instruction)
    if is_c_instruction:
        dest, comp = is_c_instruction.groups()
        return handle_cinstr(comp, dest, None)

    is_c_instruction = re.match(r'([^;]+);([A-Z]{3})', asm_instruction)
    if is_c_instruction:
        comp, jump = is_c_instruction.groups()
        return handle_cinstr(comp, None, jump)

    return None


def build_symbol_table(asm_code):
    new_asm_code = []
    for line in asm_code:
        line = re.sub(r'[\n\t\s]*', '', line)

        # Ignore empty lines.
        if line == '':
            continue

        # Ignore comments.
        if line.startswith(r'//'):
            continue

        # Delete comments on lines.
        if r'//' in line:
            line = line.split(r'//')[0]

        # Handle label definition.
        is_label_definition = re.match(r'^\((.+)\)', line)
        if is_label_definition:
            label = is_label_definition.groups()[0]
            SYMBOL_TABLE[label] = str(len(new_asm_code))
            continue

        new_asm_code.append(line)

    return new_asm_code


def handle_variables(asm_code):
    RAM = 16
    new_asm_code = []
    
    for line in asm_code:
        is_a_instruction = re.match(r'^@([^/]+)', line)
        if is_a_instruction and not re.match(r'^@[0-9]+', line):
            variable = is_a_instruction.groups()[0]
            if variable not in SYMBOL_TABLE:
                SYMBOL_TABLE[variable] = str(RAM)
                RAM += 1
            line = line.replace(variable, SYMBOL_TABLE[variable])
        new_asm_code.append(line)

    return new_asm_code


def assemble(asm_code):
    asm_code = build_symbol_table(asm_code)
    asm_code = handle_variables(asm_code)

    machine_code = []
    for line in asm_code:
        bin_code = assemble_single_line(line)
        if bin_code is not None:
            machine_code.append(bin_code)

    return machine_code


if __name__ == '__main__':
    filepath = sys.argv[1]

    with open(filepath, 'r') as prog:
        content = prog.read().splitlines()
        bin_code = assemble(content)

    for line in bin_code:
        print(line)

