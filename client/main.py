import argparse
import socket
import sys

from constants import SERVER_HOST, SERVER_PORT

try:
    from constants import ENCODING as _ENC
except Exception:
    _ENC = "utf-8"

def recv_until_blank_line(sock) -> str:
    """
    Read status + optional body until a blank line terminator.
    Falls back to returning whatever is available if the server
    doesn't send a blank line (still works with short replies).
    """
    sock.settimeout(2.0)
    data = []
    rfile = sock.makefile("r", encoding=_ENC, newline="\n")
    # Always read at least one line (the status)
    line = rfile.readline()
    if not line:
        return ""
    data.append(line.rstrip("\n"))

    # Keep reading until we hit a blank line or EOF/timeout
    while True:
        try:
            line = rfile.readline()
            if not line:
                break
            if line == "\n":
                break
            data.append(line.rstrip("\n"))
        except Exception:
            break
    return "\n".join(data)

def main():
    ap = argparse.ArgumentParser(description="Pokémon Cards client")
    ap.add_argument("host", nargs="?", default=SERVER_HOST, help="server host/IP")
    ap.add_argument("port", nargs="?", type=int, default=SERVER_PORT, help="server port")
    args = ap.parse_args()

    addr = (args.host, args.port)
    print(f"Connecting to {addr[0]}:{addr[1]} ...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)

    wfile = s.makefile("w", encoding=_ENC, newline="\n")

    try:
        print("Connected. Type commands (BUY/SELL/LIST/BALANCE/QUIT/SHUTDOWN). Ctrl+C to exit.")
        while True:
            try:
                line = input("> ").strip()
            except EOFError:
                line = "QUIT"
            except KeyboardInterrupt:
                print()
                line = "QUIT"

            if not line:
                continue

            # Always send a newline-terminated command
            wfile.write(line + "\n")
            wfile.flush()

            # Read and print the server reply
            reply = recv_until_blank_line(s)
            if reply:
                print(reply)
            else:
                print("(no response)")

            # If we sent QUIT, leave after ack
            if line.upper() == "QUIT":
                break

            # If we sent SHUTDOWN, server will close after 200 OK
            if line.upper() == "SHUTDOWN":
                break
    finally:
        try:
            wfile.close()
        except Exception:
            pass
        s.close()

if __name__ == "__main__":
    main()
