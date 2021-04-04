import sys

for line in sys.stdin:
    if line=='\n' or line=='= \n':
        continue
    else:
        print(line,end="")