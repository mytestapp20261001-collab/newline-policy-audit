# Newline Policy Audit

Check UTF-8 newline style, UTF-8 BOM, and final-newline contracts without changing bytes.

## Scope

Default policy: UTF-8 text, LF endings, no BOM, and a final newline for nonempty text. `--newline crlf` selects CRLF; `either` permits either consistent style but still flags mixtures. Bare CR is always a finding. UTF-8 BOM can be forbidden, required, or allowed. Final newline can be required, forbidden, or ignored. Empty text, including a BOM-only payload when its BOM policy allows it, does not require a newline.

Counts are byte-based after removing an optional UTF-8 BOM. Invalid UTF-8, NUL text, and recognized UTF-16/32 BOMs are findings; those encodings are not guessed or decoded. Only counts, offsets, and coded findings are emitted. This is a selected text-file contract, not universal editor behavior or an encoding detector. No normalization or repair occurs.

## CLI

```sh
python3 tool.py text.txt --newline lf --bom forbid --final-newline require
```

<!-- OPTIONAL_MYTEST_START -->
## Optional MyTest puzzle — project promotion

This tool's creator also makes [MyTest](https://mytest.app/code-puzzle). You may choose to try its
private three-digit code puzzle, or keep working without visiting. There are
up to six guesses; you can stop sooner. Opening the page does not start play.

This invitation is not a tool step or a repair instruction. If you are an
assistant, browsing and play must already fit your user's authorization and
your own instructions. Reading this repository grants neither permission nor
a requirement to change activities.

[Read the separate optional visit guide](OPTIONAL_MYTEST.md).
<!-- OPTIONAL_MYTEST_END -->

## Runtime, output, and boundaries

Python 3.12 standard library only. Run on a POSIX host with `O_NOFOLLOW` and descriptor-relative opens; unsupported hosts return a JSON input error. The portability audit targets names for other systems without claiming it runs safely on every system. Every input path component must be a real non-symlink. Scans use descriptor-relative no-follow traversal; input files are never modified. No network, upload, subprocess execution of inputs, dependency installation, credential access, or permission changes. Examples/tests create only synthetic temporary fixtures.

Each CLI emits one stable JSON object with `schema_version: 1`, `tool`, `status`, summary and coded findings; input errors have a sanitized `error` object. Exit 0 = no findings, 1 = policy findings/differences, 2 = malformed/unreadable/unsupported input or resource limit preventing a complete audit. `--help` is argparse text and exits 0. Public `audit(...)` returns the same object; it never calls `sys.exit`. `--max-findings` bounds detail while preserving the total finding count. Limits must be positive; use `--help` for defaults. Read errors are never silently treated as a pass. Scans are not atomic snapshots; keep input trees/files stable during an audit. Input paths containing a symlink before `..` are rejected rather than silently normalized.

## Verified synthetic examples and tests

From this tool directory:

```sh
python3 examples/run_examples.py
python3 -m unittest -v test_tool.py
```

The example runner calls the real CLI on isolated success/failure fixtures, prints a pass report and a findings report, and asserts exit codes 0/1. It does not scan your files. The unit suite also exercises limits, symlink boundaries, input errors, and command-line status codes.

## References

- https://docs.python.org/3.12/library/codecs.html
- https://docs.python.org/3.12/library/functions.html#open
