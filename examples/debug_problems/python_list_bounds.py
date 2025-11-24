"""
Example: List index out of bounds

Functions don't handle empty lists or invalid indices.
"""

BUGGY_CODE = """def get_element(lst: list, index: int):
    '''Get element at index from list'''
    return lst[index]

def get_first_and_last(lst: list) -> tuple:
    '''Get first and last elements'''
    return (lst[0], lst[-1])
"""

DESCRIPTION = """
Issues:
1. No bounds checking
2. Crashes on empty lists
3. No handling of invalid indices
"""

EXPECTED_FIXES = """
The agents should:
1. Add bounds checking
2. Handle empty list case (return None or raise meaningful error)
3. Validate index is within range
"""
