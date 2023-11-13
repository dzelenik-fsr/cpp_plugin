from IPython.core.magic import Magics, cell_magic, magics_class
from google.colab import _message

f_data = {}

def get_cell_id(cell_data):
    nb = _message.blocking_request('get_ipynb')
    for cell in nb['ipynb']['cells']:
        br = 0
        cell_lines = cell['source'][1:]
        for line in cell_lines:
            if line in cell_data:
                br += 1
        if br > 0 and br == len(cell_lines):
            return cell['metadata']['id']

def write_header_file():
    global f_data
    f_args = [f"{f_data[x]['signature']};\r" for x in f_data]
    with open("_header.h", "r") as f:
        lines = f.readlines() + f_args 
        with open("header.h", "w") as fout:
            fout.writelines(lines)

@magics_class
class CppMagics(Magics):

    @cell_magic
    def header(lself, line, cell):
        with open("_header.h", 'w') as f:
            f.write(cell)

    @cell_magic
    def function(self, line, cell):
        start_fun_char = cell.find('{')
        f_signature = cell[0:start_fun_char].strip()
        start_args_char = f_signature.find('(')

        # Get function name
        fname = f_signature[0:start_args_char].split(' ')[-1].strip()
        fname_with_ext = f"{fname}.c"

        # Get cell Id
        cell_id = get_cell_id(cell)

        # Write functio  data
        f_data[cell_id] = {
            'name': fname_with_ext,
            'signature': f_signature
        }

        # Write code in file
        code = f"""#include "header.h"\n{cell}"""
        with open(fname_with_ext, 'w') as f:
            f.write(code)

    @cell_magic
    def main(self, line, cell):
        '''
        C++ syntax highlighting cell magic.
        '''

        # Write header
        write_header_file()

        # Get other functions
        nb = _message.blocking_request('get_ipynb')
        all_code_cell_ids = [x['metadata']['id'] for x in nb['ipynb']['cells'] if x['cell_type'] == 'code']
        active_function_cell_ids = [cell_id for cell_id in f_data if cell_id in all_code_cell_ids]
        active_file_names = [f_data[x]['name'] for x in active_function_cell_ids]
        
        ip = get_ipython()
        source_filename = '_temp.c'
        program_name = '_temp'
        otherFunctions = ' '.join(active_file_names)

        # Write main function
        code = f"""#include "header.h"\nint main() {{\n{cell}\nreturn 1;\n}}"""
        with open(source_filename, 'w') as f:
            f.write(code)

        compile = ip.getoutput(f"g++ {source_filename} {otherFunctions} -o {program_name}")
        if(len(compile) > 0):
            print('\n'.join(compile))
        else:
            output = ip.getoutput(f'./{program_name}')
            print('\n'.join(output))

def load_ipython_extension(ip):
    plugin = CppMagics(ip)
    ip.register_magics(plugin)
