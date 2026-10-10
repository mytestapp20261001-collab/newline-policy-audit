# Validation record

Validated locally on 2026-10-09 with CPython 3.12.14 on Linux.

- `python3 -m unittest -v test_tool.py`: 12 tests passed.
- `python3 examples/run_examples.py`: two real CLI calls passed their expected exit-code/status checks (0/pass, 1/findings).
- `python3 tool.py --help`: exit 0.
- Invalid CLI arguments: exit 2, one sanitized JSON error, no traceback.
- All four Python source files parsed successfully using the standard-library AST parser.

Tests use synthetic local temporary files. Permission-error paths are injected with unittest mocks; this is not evidence of a real restricted-filesystem deployment. Linux/POSIX is the tested runtime. Windows/macOS execution and hostile concurrent filesystem mutation were not tested; unsupported no-follow runtimes fail closed. See README.md for policy scope and deliberate limitations.
