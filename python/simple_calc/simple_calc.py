# -*- coding: utf-8 -*-
"""
--------------------------------------------------------------------------
Simple Calculator
--------------------------------------------------------------------------
License:   
Copyright 2025 - <Ismail Tambawala>

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, 
this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, 
this list of conditions and the following disclaimer in the documentation 
and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors 
may be used to endorse or promote products derived from this software without 
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF 
THE POSSIBILITY OF SUCH DAMAGE.
--------------------------------------------------------------------------

Simple calculator that will 
  - Take in two numbers from the user
  - Take in an operator from the user
  - Perform the mathematical operation and provide the number to the user
  - Repeat

Operations:
  - "+" : addition
  - "-" : subtraction
  - "*" : multiplication
  - "/" : division

Error conditions:
  - Invalid operator --> Program should exit
  - Invalid number   --> Program should exit

--------------------------------------------------------------------------
"""

# NOTE - Add import statements to allow access to Python library functions
# NOTE - Hint:  Look at  https://docs.python.org/3/library/operator.html
import operator


try:
    input_fn = raw_input  # Python 2
except NameError:
    input_fn = input      # Python 3

# ------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------

# NOTE - No constants are needed for this example 

# ------------------------------------------------------------------------
# Global variables
# ------------------------------------------------------------------------

# NOTE - Global variable to map an operator string (e.g. "+") to 
# NOTE - the appropriate function.
operators = {
    # Dictionary syntax:  "key" : "value"
    #   i.e. "function" : operator.<function>
    "+" : operator.add,
    "-" : operator.sub,
    "*" : operator.mul,
    "/" : operator.truediv,
    "%" : operator.mod,
    "**": operator.pow,
    ">>" : lambda a,b: operator.rshift(int(a), int(b)),  # added (cast to int)
    "<<" : lambda a,b: operator.lshift(int(a), int(b))   # added (cast to int)
    
}



# ------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------

def get_user_input():
    try:
        number1 = float(input_fn("Enter 1st number:  "))
        number2 = float(input_fn("Enter 2nd number:  "))
        function = input_fn("Enter operation (+, -, *, /, %, **, >>, <<):  ")
        
        return(number1, number2, function)
        
    except Exception as e:
        print(e)
        print("Invalid Input")
        return (None, None, None)

# End def

# ------------------------------------------------------------------------
# Main script
# ------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        while(True):
            n1, n2, func = get_user_input()
            if (n1 is None) or (n2 is None) or (func is None):
                print("Invalid number or function!")
                break
            
            function = operators[func]
            
            print("your output is: ", function(n1, n2))
            break
            
    except:
        print("ERROR!")
    


