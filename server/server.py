import socket
import sys
from typing import Tuple

import protocol
from constants import (
    SERVER_HOST, SERVER_PORT,
    CMD_BUY, CMD_SELL, CMD_LIST, CMD_BALANCE, CMD_QUIT, CMD_SHUTDOWN,
)
from server.db import init_db, buy, sell, list_user_cards, get_user_balance

#shared encoding; fall back if not present in constants
try:
    from constants import ENCODING as _ENC
except Exception:
    _ENC = "utf-8"


def handle_client(sock: socket.socket, dbconn) -> bool:
    """
    Handle one client until QUIT or connection close.
    Returns True if the server should SHUTDOWN (global), else False.
    """
    # Text-mode for line-based protocol
    rfile = sock.makefile("r", encoding=_ENC, newline="\n")
    wfile = sock.makefile("w", encoding=_ENC, newline="\n")

    def send(txt: str):
        # All helpers in protocol already end with '\n'; just write & flush.
        wfile.write(txt)
        wfile.flush()

    shutdown_requested = False
    try:
        while True:
            line = rfile.readline()
            if not line:
                # Client closed connection.
                break

            line_stripped = line.rstrip("\r\n")
            # Spec requires server to print all messages it receives.
            print(f"Received: {line_stripped}")

            # Parse
            try:
                cmd, args = protocol.parse_line(line)
            except ValueError as ve:
                send(protocol.err_format(str(ve)))
                continue
            except KeyError as ke:
                send(protocol.err_invalid(str(ke)))
                continue

            # Dispatch
            try:
                if cmd == CMD_LIST:
                    owner = args["owner_id"]
                    rows = list_user_cards(dbconn, owner)
                    body = protocol.render_list(owner, rows)
                    send(protocol.ok(body))

                elif cmd == CMD_BALANCE:
                    owner = args["owner_id"]
                    bal, first, last, uname = get_user_balance(dbconn, owner)
                    display = protocol.make_display_name(first, last, uname)
                    send(protocol.ok(protocol.render_balance(display, bal)))

                elif cmd == CMD_BUY:
                    nb, ncnt = buy(
                        dbconn,
                        args["owner_id"],
                        args["card_name"],
                        args["card_type"],
                        args["rarity"],
                        args["price"],
                        args["count"],
                    )
                    msg = (
                        f"BOUGHT: New balance: {ncnt} {args['card_name']}."
                        f"  User USD balance ${nb:.2f}"
                    )
                    send(protocol.ok(msg))

                elif cmd == CMD_SELL:
                    nb, remain = sell(
                        dbconn,
                        args["owner_id"],
                        args["card_name"],
                        args["price"],
                        args["count"],
                    )
                    msg = (
                        f"SOLD: New balance: {remain} {args['card_name']}."
                        f" User's balance USD ${nb:.2f}"
                    )
                    send(protocol.ok(msg))

                elif cmd == CMD_QUIT:
                    send(protocol.ok())
                    break  # end this client session, keep server running

                elif cmd == CMD_SHUTDOWN:
                    send(protocol.ok())
                    shutdown_requested = True
                    break

                else:
                    # Shouldn't happen because parse_line gates commands
                    send(protocol.err_invalid("unsupported command"))

            except ValueError as ve:
                # Our DB helpers raise ValueError for expected failures (bad user, funds, etc.)
                send(protocol.err_format(str(ve)))
            except Exception as e:
                # Keep the server robust
                send(protocol.err_format("internal error"))
                print(f"[server] unexpected error: {e}", file=sys.stderr)

    finally:
        try:
            wfile.close()
        except Exception:
            pass
        try:
            rfile.close()
        except Exception:
            pass
        try:
            sock.close()
        except Exception:
            pass

    return shutdown_requested


def main():
    dbconn = init_db()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((SERVER_HOST, SERVER_PORT))
    srv.listen(1)

    print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

    try:
        while True:
            client_sock, addr = srv.accept()
            print(f"Client connected from {addr[0]}:{addr[1]}")
            should_shutdown = handle_client(client_sock, dbconn)
            print("Client disconnected")
            if should_shutdown:
                break
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt: shutting down server...")
    finally:
        try:
            srv.close()
        except Exception:
            pass
        try:
            dbconn.close()
        except Exception:
            pass
        print("Server stopped.")


if __name__ == "__main__":
    main()