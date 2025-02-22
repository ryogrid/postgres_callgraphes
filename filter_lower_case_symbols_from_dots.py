import sys
import re

def should_remove_line(line):
    match = re.match(r'\s*"([^"]+)"\s*->\s*"([^"]+)"', line)
    if match:
        left, right = match.groups()
        if left == "main" or right == "main":
            return False
        return left[0].islower() or right[0].islower() or left == "Assert" or right == "Assert"
    return False

def process_file(input_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    main_lines = []
    other_lines = []
    
    for line in lines:
        if '->' in line and ('"main"' in line):
            main_lines.append(line)
        elif not should_remove_line(line):
            other_lines.append(line)
    
    sorted_lines = main_lines + other_lines
    
    for line in sorted_lines:
        print(line, end='')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    process_file(input_file)



