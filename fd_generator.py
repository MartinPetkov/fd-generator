import re
import pprint
import itertools


FDCollection = {}
fd_pattern = re.compile('^\s*[a-zA-Z]+\s*->\s*[a-zA-Z]+\s*$')
filename_pattern = re.compile('^\w+(.\w+)?$')
output_file = None

class FD:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return self.left + '->' + self.right

    def get_left(self):
        return self.left

    def get_right(self):
        return self.right
        
    
def print_main_menu():
    print ''
    print '======================================================================='
    print 'Choose one of the following options:'
    print '\l {<FDs>} <name> - Manually load in a set of FDs, in the form {A->C,AB->CD}.'
    print '\c <attrs> <FD_set_name> - Generate the closure of the subset attrs.'
    print '\\ac <FD_set_name> <L> - Generates all closures of L within FD_set_name.'
    print '\d {<subset>+ = <closure>} <FD_set_name> <L> - Infer the functional dependencies.'
    print '\p <FD_set_name> <L> - Project the FDs onto L.'
    print '\\f <FD_set_name> - Print the FDs in the set (blank for all).'
    print '\o <filename> - Specify an output file for \c, \\ac, \d and \p.'
    print '\q - Quit'
    print '======================================================================='
    print ''
    

def write_to_file(cmd, args, result):
    output_file.write(cmd + ' ' + ' '.join(args) + ':\n' + \
                      pprint.pformat(result) + '\n\n')

	
def interpret_command(cmd, args):
    if cmd == '\l' or cmd == '\d':
        if '{' in args and '}' in args:
            ind = args.find('}') + 1
            args = [args[0:ind]] + args[ind+1:].split()
        else:
            print 'Badly formatted arguments.'
            return
    else:
        args = args.split()
    
    if cmd == '\l':
        if len(args) != 2:
            print 'Wrong number of arguments, must be exactly 2.'
            return
            
        load_fds(args[0], args[1])
        
    elif cmd == '\c':
        if len(args) != 2:
            print 'Wrong number of arguments, must be exactly 2.'
            return
        
        result = generate_closure(args[0], args[1])
        if result:
            print result
            if output_file:
                write_to_file(cmd, args, result)

    elif cmd == '\\ac':
        if len(args) != 2:
            print 'Wrong number of arguments, must be exactly 2.'
            return
        
        result = generate_all_closures(args[0], args[1])
        if result:
            pprint.pprint(result)
            if output_file:
                write_to_file(cmd, args, result)
        
    elif cmd == '\d':
        if len(args) != 3:
            print 'Wrong number of arguments, must be exactly 3.'
            return
            
        result = infer_fds(args[0], args[1], args[2])
        if result:
            print result
            if output_file:
                write_to_file(cmd, args, result)
        
    elif cmd == '\p':
        if len(args) != 2:
            print 'Wrong number of arguments, must be exactly 2.'
            return

        result = project_fds(args[0], args[1])
        if result:
            pprint.pprint(result)
            if output_file:
                write_to_file(cmd, args, result)
        
    elif cmd == '\\f':
        if len(args) > 1:
            print 'Wrong number of arguments, must be <= 1.'
            return

        if len(args) < 1:
            print_fds('')
        else:
            print_fds(args[0])
            
    elif cmd == '\o':
        if len(args) != 1:
            print 'Wrong number of arguments, must be exactly 1.'
            return
        
        filename = args[0]
        if not filename_pattern.match(filename):
            print 'Invalid file name.'
            return
        
        try:
            global output_file
            output_file = open(args[0], 'a')
        except IOError:
            print 'Unable to open file.'
            
        print 'Set output file to ' + filename
        
    elif cmd == '\q':
        return
    else:
        print 'Unrecognized command.'


def load_fds(fds, name):
    fds = fds.replace('{', '').replace('}', '')
    fds = fds.split(',')
    for i in range(len(fds)):
        if not fd_pattern.match(fds[i]):
            print 'Badly formatted FDs: must be in the form A->B, with any \
            number of letters and any number of spaces around the arrow.'
            return
        else:
            current_fd = fds[i].split('->')
            fds[i] = FD(current_fd[0].strip(), current_fd[1].strip())
    
    FDCollection[name] = fds
    print 'Successfully added ' + name + ' = ' + str(FDCollection[name])


def generate_closure(attrs, fd_set_name):
    if not fd_set_name in FDCollection:
        print 'Could not find FD set called ' + fd_set_name
        return None
    
    fd_set = FDCollection[fd_set_name]

    closure = attrs
    found = True
    while(found):
        found = False
        for fd in fd_set:
            if set(fd.get_left()).issubset(set(closure)):
                for c in fd.get_right():
                    if not c in closure:
                        closure = closure + c
                        found = True

    return closure


def generate_all_closures(fd_set_name, L):
    all_closures = {}
    substrs_L = get_all_combinations(L)
    for substr in substrs_L:
        closure = generate_closure(substr, fd_set_name)
        if substr != closure:
            all_closures[substr] = closure

    return all_closures


def get_all_combinations(s):
    length = len(s)
    all_combinations = []
    
    for i in range(1, len(s)+1):
        all_combinations = all_combinations + \
            [ ''.join(chars) for chars in itertools.combinations(s, i) ]

    return all_combinations


def infer_fds(closure, fd_set_name, L):
    subset, reachable = closure.replace('{', '')\
        .replace('}', '').replace(' ', '').split('=')
    subset = subset.replace('+', '')

    fd = subset + '->'
    for symbol in reachable:
        if symbol not in subset and symbol in L:
            fd = fd + symbol

    return fd


def project_fds(fd_set_name, L):
    all_closures = generate_all_closures(fd_set_name, L)

    projection = {}
    temp_projection = {}
    keys = []

    for subset,reachable in all_closures.iteritems():
        closure = subset + '=' + reachable
        fds = infer_fds(closure, fd_set_name, L)
        fd_left, fd_right = fds.split('->')

        if set(L).issubset(set(reachable)):
            keys.append(subset)
        
        if fd_right:
            temp_projection[closure] = fds
    
    keys.sort(key=len)
    to_remove = []
    for i in range(0, len(keys)):
        for j in range(i+1, len(keys)):
            if set(keys[i]).issubset(set(keys[j])) and not keys[j] in to_remove:
                to_remove.append(keys[j])
    
    for k in temp_projection.keys():
        if not k.split('=')[0] in to_remove:
            projection[k] = temp_projection[k]

    return projection


def print_fds(fd_set_name):
    if not fd_set_name:
        pprint.pprint(FDCollection)
    elif fd_set_name in FDCollection:
        print FDCollection[fd_set_name]
    else:
        print 'Could not find FD set called ' + fd_set_name

	
if __name__ == '__main__':
    cmd = ''
    while(cmd != '\q'):
        print_main_menu()
        input = raw_input('Enter a command: ').strip()
        ind = input.find(' ')
        if ind == -1:
            ind = len(input)
                    
        cmd, args = input[0:ind], input[ind+1:]
        interpret_command(cmd, args)
        
    if output_file:
        output_file.close()


#\l {ABE->CF, DF->BD, C->DF, E->A, AF->B} S
