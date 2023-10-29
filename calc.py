'''
Calc.py
by Marcel Wijaya
(adopted from the parser by Christopher Tao at https://gist.github.com/qiuyujx/fd285e2a2638978ae08f0b5c3eae54ab)
-------------------------------------------------------------------

Calc.py develops:
- Removes the prepared random variables tags and values; instead calc.py imported sys module to accept input from command line interface or shell.
- Filter out the unproper input and returns "nan". those uprpoper inputs includes: blank arguments, non digit characters, unfinished formula, etc.
- Restructure calculation steps of subtraction. (original source had been corrent to  prioritize multiplication and division over addition and summation, however, the calculation still cannot perform correct result if more than 1 substraction occure (eg.: 3-2-1 should have been return zero, but the original source returned 2 as a result it splitted calculation step to be 3-(2-1)

curent known bugs:
- falied to to calculation of division if the denominator is negative value. It is because I filter out double operator in the parser check. Workaround, enclose the denominator ith a parentheses (query 3/(-2(instead of input 3/-2)

Todo:
-


'''
#import pandas as pd
import numpy as np
import re
import sys

# Functions
def parentheses_enclosed(s):
    paren_order = re.findall(r'[\(\)]', s)

    if paren_order.count('(') != paren_order.count(')'):
        return False

    curr_levels = []
    nest_lv = 0
    for p in paren_order:
        if p == '(':
            nest_lv += 1
        else:
            nest_lv -= 1
        curr_levels.append(nest_lv)
    if 0 in curr_levels[:-1]:
        return False
    else:
        return True


def remove_matched_parentheses(s):
    if ')' in s:
        # find the first ')'
        end = s.find(')')
        # find the last '(' before the first ')'
        start = max([i for i, char in enumerate(s[:end]) if char == '(' ])
        # remove the parentheses
        return remove_matched_parentheses(s[:start] + s[end+1:])
    else:
        return s


def interpret(f, df):
    if re.match(r'\Atag[\d]+\Z', f):  # e.g. 'tag1'
        return df[df.tag == f]['value'].values

    elif parentheses_enclosed(f) and \
        re.match(r'\Asum\(.+[\+\-].+\)\Z|\Aavg\(.+[\+\-].+\)\Z|\Amin\(.+[\+\-].+\)\Z|\Amax\(.+[\+\-].+\)\Z', f):

        f_name = f[:3]  # get agg func name
        f_stripped = f[4:-1]  # strip outer func

        while re.match(r'\A\(.+\)\Z', f_stripped) and parentheses_enclosed(f_stripped):
            f_stripped = f_stripped[1:-1]

        comps = re.compile(r'[\+\-]').split(f_stripped)  # split by + or -

        operators = re.findall(r'[\+\-]', f_stripped)
        comps_final = []
        temp_str = ''
        for c in comps:
            temp_str += c
            if re.match(r'\Atag[\d]+\Z', temp_str) or parentheses_enclosed(temp_str):
                comps_final.append(f'{f_name}({temp_str})')
                if len(operators) > 0:
                    comps_final.append(operators.pop(0))
                temp_str = ''
            else:
                temp_str += operators.pop(0)
        return interpret(''.join(comps_final), df)

    elif re.match(r'\Asum\([^\(\)]+\)\Z', f):  # e.g. 'sum(tag1)'
        return np.sum(interpret(f[4:-1], df))

    elif re.match(r'\Aavg\([^\(\)]+\)\Z', f):  # e.g. 'avg(tag1)'
        return np.average(interpret(f[4:-1], df))

    elif re.match(r'\Amin\([^\(\)]+\)\Z', f):  # e.g. 'min(tag1)'
        return np.min(interpret(f[4:-1], df))

    elif re.match(r'\Amax\([^\(\)]+\)\Z', f):  # e.g. 'max(tag1)'
        return np.max(interpret(f[4:-1], df))

    elif re.match(r'\A\(.+\)\Z', f) and parentheses_enclosed(f):  # e.g. '(tag1-tag2)'
        return interpret(f[1:-1], df)

    elif f.replace('.', '', 1).isdigit():
        return float(f)

    else:
        rest_f = remove_matched_parentheses(f)
        #if '+' in rest_f or '-' in rest_f:
        if '+' in rest_f:
            comps = re.compile(r'[\+]').split(f)
        elif '-' in rest_f:
            comps = re.compile(r'[\-]').split(f)
        else:
            comps = re.compile(r'[\*\/]').split(f)

        if comps[0].count('(') != comps[0].count(')'):
            nested_level = comps[0].count('(') - comps[0].count(')')
            pos = len(comps[0])
            for comp in comps[1:]:
                if '(' in comp:
                    nested_level += comp.count('(')
                if ')' in comp:
                    nested_level -= comp.count(')')
                pos += len(comp) + 1  # +1 because of the operator inside parenthesis
                if nested_level == 0:
                    break
        else:
            pos = len(comps[0])

        if (len(f) - pos <= 1): # check whether the last operand is in place, double operators, or missing operands
            return np.nan
        left = f[:pos]  # left component
        right = f[pos+1:]  # right component
        operator = f[pos]  # the operator

        if operator == '+':
            return interpret(left, 1) + interpret(right, 1)
        elif operator == '-':
            if pos == 0: # negative
                #left = "0"
                return (interpret(right,-1) * -1)

            if right[0] == '(':
                right_opr = interpret(right,1) * df
            else:
                right_opr = interpret(right,-1) * df
            #print(right_opr)
            return interpret(left, df) - right_opr
        elif operator == '*':
            return interpret(left, 1) * interpret(right, 1)
        elif operator == '/':
            denominator = interpret(right, df)
            if denominator == 0 or denominator is np.nan:
                return np.nan
            else:
                return interpret(left, 1) / interpret(right, 1)

    return np.nan

# usage
try:
    if sys.argv[1] is None:
        print("kosong")
except:
    print("Error: Arguments was not parsed correctly. Tanya Marcel deh")
else:
    for i in range(1, len(sys.argv)):
        args = sys.argv[i]

    print(interpret(args, 1))
