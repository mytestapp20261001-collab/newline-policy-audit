import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).parent))
spec=importlib.util.spec_from_file_location("audit_tool",Path(__file__).with_name("tool.py"))
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()
    def codes(self,result):return {x["code"] for x in result.get("findings",[])}
    def call(self,*args):
        result=subprocess.run([sys.executable,str(Path(__file__).with_name("tool.py")),*map(str,args)],capture_output=True,text=True)
        return result.returncode,json.loads(result.stdout)
    def test_bad_cli(self):
        code,result=self.call("--unknown");self.assertEqual(code,2);self.assertEqual(result["status"],"error")
    def test_examples(self):
        result=subprocess.run([sys.executable,str(Path(__file__).parent/"examples"/"run_examples.py")],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        reports=[json.loads(x) for x in result.stdout.splitlines()]
        self.assertEqual([r["status"] for r in reports],["pass","findings"])

    def write(self,data):
        p=self.root/'input.txt';p.write_bytes(data);return p
    def test_lf_and_cli(self):
        p=self.write(b'one\ntwo\n');r=tool.audit(p);self.assertEqual(r['status'],'pass');self.assertEqual(r['summary']['lf'],2);self.assertEqual(self.call(p)[0],0)
    def test_mixed_barecr_and_final(self):
        p=self.write(b'a\r\nb\nc\rd');r=tool.audit(p);self.assertTrue({'mixed_newlines','bare_cr','missing_final_newline','unexpected_crlf'}<=self.codes(r));self.assertEqual(self.call(p)[0],1)
    def test_crlf_contract(self):
        p=self.write(b'x\r\n');self.assertEqual(tool.audit(p,newline='crlf')['status'],'pass');self.assertIn('unexpected_crlf',self.codes(tool.audit(p)))
        self.assertIn('forbidden_final_newline',self.codes(tool.audit(p,newline='crlf',final_newline='forbid')))
    def test_bom_contract(self):
        p=self.write(b'\xef\xbb\xbfx\n');self.assertIn('forbidden_bom',self.codes(tool.audit(p)));self.assertEqual(tool.audit(p,bom='require')['status'],'pass')
        p=self.write(b'x\n');self.assertIn('missing_utf8_bom',self.codes(tool.audit(p,bom='require')))
    def test_encoding_and_binary(self):
        self.assertIn('invalid_utf8',self.codes(tool.audit(self.write(b'\xff\n'))));self.assertIn('unsupported_text_encoding_bom',self.codes(tool.audit(self.write(b'\xff\xfex\x00'))));self.assertIn('nul_in_text',self.codes(tool.audit(self.write(b'x\x00\n'))))
    def test_empty_limits_and_permissions(self):
        p=self.write(b'');self.assertEqual(tool.audit(p)['status'],'pass');p.write_bytes(b'xx');self.assertEqual(tool.audit(p,max_bytes=1)['status'],'error');self.assertEqual(tool.audit(p,newline='invalid')['status'],'error')
        with mock.patch.object(tool,'read_file',side_effect=PermissionError):self.assertEqual(tool.audit(p)['status'],'error')
    def test_symlink_and_no_mutation(self):
        p=self.write(b'x\r\n');q=self.root/'link';q.symlink_to(p);self.assertEqual(tool.audit(q)['status'],'error');tool.audit(p);self.assertEqual(p.read_bytes(),b'x\r\n')

    def test_support_rejects_symlink_before_dotdot(self):
        import _support
        (self.root/'actual').mkdir();(self.root/'alias').symlink_to('actual');(self.root/'safe').write_bytes(b'x')
        with self.assertRaises((OSError,_support.InputError)):
            with _support.anchored(str(self.root)+'/alias/../safe'):
                self.fail('must not normalize away a symlink component')
    def test_support_detects_pre_read_mutation(self):
        import _support
        p=self.root/'changed';p.write_bytes(b'a');before=p.stat();p.write_bytes(b'longer')
        with _support.anchored(self.root,True) as fd:
            with self.assertRaises(_support.InputError):_support.read_at(fd,'changed',before,100)
    def test_support_entry_budget_and_host_guard(self):
        import _support
        (self.root/'a').mkdir();(self.root/'a'/'x').touch();(self.root/'b').touch()
        with _support.anchored(self.root,True) as fd:
            with self.assertRaises(_support.InputError):list(_support.walk(fd,max_entries=2))
        with mock.patch.object(_support.os,'name','unsupported'):
            with self.assertRaises(_support.InputError):_support._flags()

if __name__=="__main__":unittest.main()
