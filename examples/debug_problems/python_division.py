"""
Example: Division by zero

The safe_divide function claims to be safe but will crash on zero division.
"""

BUGGY_CODE = """def divide(a: float, b: float) -> float:
    '''Divide two numbers'''
    return a / b

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    '''Safely divide, return default if division by zero'''
    return a / b
"""

DESCRIPTION = """
Issues:
1. safe_divide doesn't actually handle division by zero
2. No error handling
3. Should return default value on zero division
"""

EXPECTED_FIXES = """
The agents should:
1. Add try/except or if check for zero
2. Return default value when b == 0
3. Possibly add validation for edge cases (infinity, NaN)
"""
