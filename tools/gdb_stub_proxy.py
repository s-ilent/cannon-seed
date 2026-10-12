#!/usr/bin/env python3
"""gdb_stub_proxy.py — connect any gdb to the PCSX-Redux gdb stub.

PCSX-Redux's gdb server reports its thread as `p1.t1`: in the `qC` reply
(`QCp1.t1`) and as the `qXfer:threads:read` XML thread id. gdb parses remote
thread ids strictly as `p<pid>.<tid>` with numeric fields, so `target remote`
aborts at connect with `invalid remote ptid: p1.t1`. `set remote
threads-packet off` removes only the XML instance — the `qC` packet still
kills the session.

This proxy sits between gdb and the stub and rewrites that id to the
conformant `p1.1` in every text reply. Hex register/memory payloads cannot
contain the literal, and binary/console packets (`x`, `X`, `O`) pass through
untouched, so the rewrite cannot corrupt data.

    python3 tools/gdb_stub_proxy.py &     # 127.0.0.1:3334 -> 127.0.0.1:3333
    gdb -ex "target remote localhost:3334"

One gdb at a time; the stub itself accepts one client. Reconnects are fine.
"""

import argparse
import select
import socket
import sys

BAD = b"p1.t1"
GOOD = b"p1.1"

# Packet types whose payload is binary/console data: never rewrite these.
OPAQUE = (b"x", b"X", b"O")


def checksum(payload: bytes) -> bytes:
    return b"%02x" % (sum(payload) & 0xFF)


class ReplyFilter:
    """Frames the stub->gdb byte stream and rewrites thread ids in place.

    RSP framing: a packet is `$<payload>#<2 hex>`. Bytes outside packets
    (ack '+'/'-', the 0x03 interrupt) pass through. Payloads never contain a
    raw '$' or '#' — binary data is escaped — so naive framing is exact.
    """

    IDLE, PAYLOAD, CKSUM = range(3)

    def __init__(self, sink, log=sys.stderr):
        self._sink = sink
        self._log = log
        self._state = self.IDLE
        self._raw = bytearray()      # whole packet, for pass-through
        self._payload = bytearray()  # payload only, for matching
        self._csum = bytearray()

    def feed(self, data: bytes) -> None:
        for b in data:
            if self._state == self.IDLE:
                if b == 0x24:  # '$'
                    self._state = self.PAYLOAD
                    self._raw = bytearray(b"$")
                    self._payload = bytearray()
                else:
                    self._sink(bytes([b]))
            elif self._state == self.PAYLOAD:
                self._raw.append(b)
                if b == 0x23:  # '#'
                    self._state = self.CKSUM
                    self._csum = bytearray()
                else:
                    self._payload.append(b)
            else:  # CKSUM
                self._raw.append(b)
                self._csum.append(b)
                if len(self._csum) == 2:
                    self._emit()

    def _emit(self) -> None:
        p = bytes(self._payload)
        if not p.startswith(OPAQUE) and BAD in p:
            p2 = p.replace(BAD, GOOD)
            self._log.write(
                f"[gdb_stub_proxy] rewrite {p!r} -> {p2!r}\n"
            )
            self._sink(b"$" + p2 + b"#" + checksum(p2))
        else:
            self._sink(bytes(self._raw))
        self._state = self.IDLE


def serve(host: str, listen_port: int, stub_port: int) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, listen_port))
    srv.listen(1)
    print(f"[gdb_stub_proxy] {host}:{listen_port} -> stub {host}:{stub_port}",
          file=sys.stderr, flush=True)
    while True:
        client, _ = srv.accept()
        try:
            stub = socket.create_connection((host, stub_port))
        except OSError as e:
            print(f"[gdb_stub_proxy] stub connect failed: {e}",
                  file=sys.stderr, flush=True)
            client.close()
            continue
        filt = ReplyFilter(client.sendall)
        try:
            while True:
                readable, _, _ = select.select([client, stub], [], [])
                if client in readable:
                    data = client.recv(65536)
                    if not data:
                        break
                    stub.sendall(data)
                if stub in readable:
                    data = stub.recv(65536)
                    if not data:
                        break
                    filt.feed(data)
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            client.close()
            stub.close()
            print("[gdb_stub_proxy] client disconnected", file=sys.stderr,
                  flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--listen", type=int, default=3334,
                    help="port gdb connects to (default 3334)")
    ap.add_argument("--stub", type=int, default=3333,
                    help="port the emulator stub listens on (default 3333)")
    args = ap.parse_args()
    try:
        serve(args.host, args.listen, args.stub)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
