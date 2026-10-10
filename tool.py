#!/usr/bin/env python3
"""Audit UTF-8 line endings, final-newline, and BOM policies without repair."""
from _support import InputError, Parser, Report, cli, guarded, limits, positive, read_file
TOOL="newline-policy-audit"
BOMS=[(b'\xff\xfe\x00\x00','utf-32-le'),(b'\x00\x00\xfe\xff','utf-32-be'),(b'\xff\xfe','utf-16-le'),(b'\xfe\xff','utf-16-be'),(b'\xef\xbb\xbf','utf-8')]

@guarded(TOOL)
def audit(path, *, newline="lf",bom="forbid",final_newline="require",max_bytes=16777216,max_findings=1000):
    limits(max_bytes=max_bytes,max_findings=max_findings)
    if newline not in ('lf','crlf','either') or bom not in ('forbid','require','allow') or final_newline not in ('require','forbid','ignore'):
        raise InputError("invalid newline, BOM, or final-newline policy")
    data=read_file(path,max_bytes);report=Report(TOOL,max_findings)
    mark=next(((prefix,name) for prefix,name in BOMS if data.startswith(prefix)),(b'',None))
    summary={"bytes":len(data),"bom":mark[1]}
    if mark[1] and mark[1]!='utf-8':
        report.add("unsupported_text_encoding_bom");return report.finish(summary)
    if bom=='forbid' and mark[0]:report.add('forbidden_bom')
    if bom=='require' and not mark[0]:report.add('missing_utf8_bom')
    payload=data[len(mark[0]):]
    try:payload.decode('utf-8','strict')
    except UnicodeDecodeError as exc:
        report.add('invalid_utf8',byte_offset=exc.start+len(mark[0]));return report.finish(summary)
    if b'\x00' in payload:report.add('nul_in_text')
    crlf=payload.count(b'\r\n');lf=payload.count(b'\n')-crlf;cr=payload.count(b'\r')-crlf
    summary.update(crlf=crlf,lf=lf,bare_cr=cr,has_final_newline=payload.endswith(b'\n'),empty=not payload)
    if cr:report.add('bare_cr',count=cr)
    if lf and crlf:report.add('mixed_newlines')
    if newline=='lf' and crlf:report.add('unexpected_crlf',count=crlf)
    if newline=='crlf' and lf:report.add('unexpected_lf',count=lf)
    if payload and final_newline=='require' and not payload.endswith(b'\n'):report.add('missing_final_newline')
    if final_newline=='forbid' and payload.endswith(b'\n'):report.add('forbidden_final_newline')
    return report.finish(summary)

def parse_and_audit():
    p=Parser(description=__doc__);p.add_argument('file');p.add_argument('--newline',choices=['lf','crlf','either'],default='lf');p.add_argument('--bom',choices=['forbid','require','allow'],default='forbid');p.add_argument('--final-newline',choices=['require','forbid','ignore'],default='require')
    p.add_argument('--max-bytes',type=positive,default=16777216);p.add_argument('--max-findings',type=positive,default=1000)
    a=vars(p.parse_args());path=a.pop('file');return audit(path,**a)
if __name__=='__main__':raise SystemExit(cli(TOOL,parse_and_audit))
