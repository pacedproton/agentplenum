"""
Example: Integer overflow handling

The multiply_safe function should detect overflow but doesn't handle all cases.
"""

BUGGY_CODE = """def add_numbers(a: int, b: int) -> int:
    '''Add two integers'''
    return a + b

def multiply_safe(a: int, b: int, max_value: int = 1000000) -> int:
    '''Multiply two numbers, return -1 if overflow'''
    result = a * b
    return result if result <= max_value else -1
"""

DESCRIPTION = """
This code has issues with edge cases:
1. multiply_safe doesn't handle negative numbers properly
2. No validation of inputs
3. add_numbers doesn't check for overflow
"""

EXPECTED_FIXES = """
The agents should:
1. Add overflow checking to add_numbers
2. Fix multiply_safe to handle negative numbers
3. Add proper input validation
"""
