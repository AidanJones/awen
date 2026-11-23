import http.client
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import serve_review


class RangeTests(unittest.TestCase):
    def setUp(self):
        quiet=patch.object(serve_review.ReviewHandler,'log_message',lambda *_:None);quiet.start();self.addCleanup(quiet.stop)
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);public=self.root/'public';public.mkdir()
        (public/'review.html').write_text('REVIEW',encoding='utf8')
        (self.root/'private-key.json').write_text('PRIVATE',encoding='utf8')
        self.audio=bytes(range(256))*8;(public/'audio.wav').write_bytes(self.audio)
        self.server=serve_review.make_server(public)
        self.thread=threading.Thread(target=lambda:self.server.serve_forever(poll_interval=.02),daemon=True);self.thread.start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)

    def request(self,method='GET',path='/audio.wav',headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        try:
            conn.request(method,path,headers=headers or {});r=conn.getresponse()
            return r.status,dict(r.getheaders()),r.read()
        finally:conn.close()

    def test_full_file_and_root(self):
        status,h,body=self.request();self.assertEqual(status,200);self.assertEqual(body,self.audio)
        self.assertEqual(h['Accept-Ranges'],'bytes');self.assertEqual(int(h['Content-Length']),len(body))
        self.assertEqual(self.request(path='/')[2],b'REVIEW')

    def test_forward_backward_suffix_open_and_clamped_ranges(self):
        for range_,start,end in [('bytes=1000-1100',1000,1100),('bytes=10-99',10,99),('bytes=-20',2028,2047),('bytes=2000-',2000,2047),('bytes=2000-9999',2000,2047)]:
            status,h,body=self.request(headers={'Range':range_})
            self.assertEqual(status,206);self.assertEqual(body,self.audio[start:end+1])
            self.assertEqual(h['Content-Range'],f'bytes {start}-{end}/2048')
            self.assertEqual(int(h['Content-Length']),len(body))

    def test_head_range_no_body(self):
        status,h,body=self.request('HEAD',headers={'Range':'bytes=20-29'})
        self.assertEqual(status,206);self.assertEqual(h['Content-Length'],'10');self.assertEqual(body,b'')

    def test_invalid_and_unsatisfiable_ranges(self):
        for range_ in ['bytes=9999-','bytes=10-2','bytes=-0','bytes=-','bytes=0-1,4-5','bad']:
            status,h,body=self.request(headers={'Range':range_})
            self.assertEqual(status,416);self.assertEqual(h['Content-Range'],'bytes */2048');self.assertEqual(body,b'')

    def test_if_range_falls_back_to_full_response(self):
        status,_,body=self.request(headers={'Range':'bytes=0-1','If-Range':'old-validator'})
        self.assertEqual(status,200);self.assertEqual(body,self.audio)

    def test_matching_if_range_date_allows_seek(self):
        _,headers,_=self.request('HEAD')
        status,_,body=self.request(headers={'Range':'bytes=100-109','If-Range':headers['Last-Modified']})
        self.assertEqual(status,206);self.assertEqual(body,self.audio[100:110])

    def test_no_directory_or_private_key_exposure(self):
        (self.root/'public/sub').mkdir()
        for path in ['/../private-key.json','/%2e%2e/private-key.json','/sub/']:
            status,_,body=self.request(path=path);self.assertEqual(status,404);self.assertNotIn(b'PRIVATE',body)
        with self.assertRaises(ValueError):serve_review.make_server(self.root)

    def test_standalone_explorer_bundle_is_accepted(self):
        folder=self.root/'explorer';folder.mkdir();(folder/'explore.html').write_text('EXPLORER',encoding='utf8')
        server=serve_review.make_server(folder)
        self.assertEqual(server.server_address[0],'127.0.0.1');server.server_close()


if __name__=='__main__':unittest.main()
