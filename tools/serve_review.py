"""Serve a public listening packet on localhost, with seekable audio byte ranges."""
import argparse
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re


class ReviewHandler(SimpleHTTPRequestHandler):
    protocol_version='HTTP/1.1'

    def send_head(self):
        root=Path(self.directory).resolve()
        target=Path(self.translate_path(self.path)).resolve()
        if target==root: target=root/'review.html'
        if not target.is_relative_to(root):
            self.send_error(403);return None
        if not target.is_file():
            self.send_error(404);return None
        try:
            stream=target.open('rb')
        except OSError:
            self.send_error(404);return None
        stat=os.fstat(stream.fileno());modified=self.date_time_string(stat.st_mtime)
        size=stat.st_size;start,end=0,size-1;status=200
        requested=self.headers.get('Range')
        # A single contiguous range is sufficient for native HTML audio seeking.
        if requested and self.headers.get('If-Range',modified)==modified:
            match=re.fullmatch(r'bytes=(\d*)-(\d*)',requested.strip())
            try:
                if not match or not any(match.groups()): raise ValueError()
                a,b=match.groups()
                if a:
                    start=int(a);end=min(int(b),size-1) if b else size-1
                else:
                    suffix=int(b)
                    if suffix<=0:raise ValueError()
                    start=max(0,size-suffix)
                if start>=size or start<0 or end<start:raise ValueError()
            except ValueError:
                stream.close();self.send_response(416)
                self.send_header('Content-Range',f'bytes */{size}')
                self.send_header('Content-Length','0');self.end_headers();return None
            status=206
        self.send_response(status)
        self.send_header('Content-Type',self.guess_type(str(target)))
        self.send_header('Accept-Ranges','bytes')
        self.send_header('Content-Length',str(max(0,end-start+1)))
        self.send_header('Last-Modified',modified)
        self.send_header('Cache-Control','no-cache')
        if status==206:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers();stream.seek(start);self.remaining=max(0,end-start+1)
        return stream

    def copyfile(self,source,outputfile):
        try:
            while self.remaining:
                chunk=source.read(min(65536,self.remaining))
                if not chunk:break
                outputfile.write(chunk);self.remaining-=len(chunk)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):
            pass  # Native media controls cancel requests when seeking/switching.


def make_server(directory,port=0):
    directory=Path(directory).resolve()
    if not (directory/'review.html').is_file() or any((directory/name).exists() for name in ['private-key.json','experiment.json']):
        raise ValueError('Serve only the packet public directory containing review.html')
    return ThreadingHTTPServer(('127.0.0.1',port),partial(ReviewHandler,directory=str(directory)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path);parser.add_argument('--port',type=int,default=0)
    args=parser.parse_args()
    with make_server(args.directory,args.port) as server:
        print(f'Review: http://127.0.0.1:{server.server_port}/review.html',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
