# semantic.py
# Phase 3b – Semantic Analysis (lightweight)
#
# Performs simple semantic analysis on source code:
#   - Symbol table construction (tracks assignments)
#   - Undeclared variable detection
#   - Duplicate assignment warnings
#
# This is NOT a full type checker. It focuses on:
#   - Existence of variables before use
#   - Assignment-before-use validation
#   - Tracking which variables are defined where
#
# Educational value:
#   - Shows how semantic analysis differs from syntax analysis
#   - Demonstrates symbol tables in compiler design
#   - Provides meaningful feedback for programmer education


import re
from typing import Dict, List, Tuple, Any


class SemanticError:
    """Represents a semantic analysis error or warning."""
    
    def __init__(self, error_type: str, message: str, line: int, column: int = 0):
        """
        Initialize a semantic error.
        
        Args:
            error_type: 'error' or 'warning'
            message: Human-readable error message
            line: Line number where issue occurs (1-based)
            column: Column number (0-based, optional)
        """
        self.error_type = error_type
        self.message = message
        self.line = line
        self.column = column

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            'type': self.error_type,
            'message': self.message,
            'line': self.line,
            'column': self.column,
        }


class SemanticAnalyzer:
    """
    Lightweight semantic analyzer for educational compiler system.
    
    Tracks symbol definitions and detects semantic issues like:
    - Undeclared variable usage
    - Duplicate assignments
    - Variable tracking across scope
    """

    def __init__(self, source: str):
        """
        Initialize analyzer with source code.
        
        Args:
            source: Source code string
        """
        self.source = source
        self.lines = source.split('\n')
        self.symbol_table: Dict[str, List[int]] = {}  # name -> [lines where defined]
        self.undefined_uses: List[SemanticError] = []
        self.duplicate_assigns: List[SemanticError] = []
        self.all_errors: List[SemanticError] = []
        self.reserved_words = {
            'print', 'if', 'else', 'while', 'for', 'return',
            'true', 'false', 'int', 'float', 'string', 'bool'
        }

    def analyze(self) -> Dict[str, Any]:
        """
        Perform semantic analysis on the source code.
        
        Returns:
            dict with keys:
                'symbol_table': {name: [lines_where_defined]}
                'undefined_variables': [list of variable names]
                'duplicate_assignments': [list of variable names]
                'errors': [list of semantic error dicts]
                'warnings': [list of semantic warning dicts]
                'error_count': int
                'warning_count': int
        """
        # First pass: collect all assignments (symbol table construction)
        self._build_symbol_table()

        # Second pass: check for undeclared variable uses
        self._detect_undeclared_variables()

        # Third pass: detect duplicate assignments
        self._detect_duplicate_assignments()

        # Separate errors and warnings
        errors = [e for e in self.all_errors if e.error_type == 'error']
        warnings = [e for e in self.all_errors if e.error_type == 'warning']

        return {
            'symbol_table': self.symbol_table,
            'undefined_variables': self._get_undefined_names(),
            'duplicate_assignments': self._get_duplicate_assign_names(),
            'errors': [e.to_dict() for e in errors],
            'warnings': [e.to_dict() for e in warnings],
            'error_count': len(errors),
            'warning_count': len(warnings),
        }

    def _build_symbol_table(self) -> None:
        """
        First pass: Build symbol table by finding all assignments.
        
        Matches patterns like:
            x = <expression>
            x=<expression>
        """
        # Pattern: variable_name = something
        assignment_pattern = r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*='

        for line_num, line in enumerate(self.lines, start=1):
            match = re.match(assignment_pattern, line)
            if match:
                var_name = match.group(1)
                if var_name not in self.symbol_table:
                    self.symbol_table[var_name] = []
                self.symbol_table[var_name].append(line_num)

    def _detect_undeclared_variables(self) -> None:
        """
        Second pass: Detect usage of undefined variables.
        
        Looks for variable names used in expressions before they are defined.
        """
        # Pattern: any identifier (word characters and underscores)
        identifier_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b'

        for line_num, line in enumerate(self.lines, start=1):
            # Skip pure assignment lines (LHS of assignment is always defined)
            if '=' in line:
                # Find the part after the first assignment operator
                rhs_start = line.find('=') + 1
                rhs = line[rhs_start:]
            else:
                rhs = line

            # Find all identifiers in the expression
            for match in re.finditer(identifier_pattern, rhs):
                var_name = match.group(1)
                col_num = match.start() - len(line) + len(line.lstrip())

                if var_name in self.reserved_words:
                    continue

                # Check if this variable is defined
                if var_name not in self.symbol_table:
                    # Check if it's defined at or before this line
                    error = SemanticError(
                        error_type='error',
                        message=f"Undeclared variable '{var_name}' used before assignment",
                        line=line_num,
                        column=match.start()
                    )
                    self.all_errors.append(error)
                else:
                    # Variable is defined, but check if it's defined before this line
                    defined_lines = self.symbol_table[var_name]
                    if not any(def_line < line_num for def_line in defined_lines):
                        error = SemanticError(
                            error_type='error',
                            message=f"Variable '{var_name}' used before assignment on line {line_num}",
                            line=line_num,
                            column=match.start()
                        )
                        self.all_errors.append(error)
                    break  # Only flag first use on each line

    def _detect_duplicate_assignments(self) -> None:
        """
        Third pass: Warn about variables assigned multiple times.
        
        This helps educators identify redundant or confusing variable reuse.
        """
        for var_name, lines in self.symbol_table.items():
            if len(lines) > 1:
                # Variable is assigned multiple times
                for i, line_num in enumerate(lines[1:], start=2):
                    # Create a warning for assignments after the first
                    line_text = self.lines[line_num - 1]
                    warning = SemanticError(
                        error_type='warning',
                        message=f"Variable '{var_name}' reassigned (previously defined on line {lines[0]})",
                        line=line_num,
                        column=0
                    )
                    self.all_errors.append(warning)

    def _get_undefined_names(self) -> List[str]:
        """Get unique list of undefined variable names."""
        undefined = set()
        for error in self.all_errors:
            if error.error_type == 'error' and 'Undeclared' in error.message:
                # Extract variable name from error message
                match = re.search(r"'([a-zA-Z_][a-zA-Z0-9_]*)'", error.message)
                if match:
                    undefined.add(match.group(1))
        return sorted(list(undefined))

    def _get_duplicate_assign_names(self) -> List[str]:
        """Get unique list of variables with duplicate assignments."""
        dup_names = []
        for var_name, lines in self.symbol_table.items():
            if len(lines) > 1:
                dup_names.append(var_name)
        return sorted(dup_names)
