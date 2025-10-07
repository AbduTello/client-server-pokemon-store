from typing import Tuple, Dict, Any, List
from constants import (
    CMD_BUY, CMD_SELL, CMD_LIST, CMD_BALANCE, CMD_QUIT, CMD_SHUTDOWN,
    RESP_OK, RESP_INVALID, RESP_FORMAT_ERR
)


# Parsing

def parse_line(line: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parse one newline-terminated client line into (command, args).
    Raises:
      - ValueError for format/type issues (use 403)
      - KeyError for unknown command (use 400)
    Command shapes (exactly as in the assignment):
      BUY <name> <type> <rarity> <price> <count> <owner_id>
      SELL <name> <count> <price> <owner_id>
      LIST <owner_id>
      BALANCE <owner_id>
      QUIT
      SHUTDOWN
    """
    if not line:
        raise ValueError("empty line")

    parts = line.strip().split()
    if not parts:
        raise ValueError("empty line")

    cmd = parts[0].upper()

    if cmd == CMD_BUY:
        # Example: BUY Pikachu Electric Common 19.99 2 1
        if len(parts) != 7:
            raise ValueError("BUY expects: BUY <name> <type> <rarity> <price> <count> <owner_id>")
        _, name, ctype, rarity, price, count, owner = parts
        try:
            return CMD_BUY, {
                "card_name": name,
                "card_type": ctype,
                "rarity": rarity,
                "price": float(price),
                "count": int(count),
                "owner_id": int(owner),
            }
        except ValueError:
            raise ValueError("BUY has invalid number types")

    if cmd == CMD_SELL:
        # Example: SELL Pikachu 1 34.99 1
        if len(parts) != 5:
            raise ValueError("SELL expects: SELL <name> <count> <price> <owner_id>")
        _, name, count, price, owner = parts
        try:
            return CMD_SELL, {
                "card_name": name,
                "count": int(count),
                "price": float(price),
                "owner_id": int(owner),
            }
        except ValueError:
            raise ValueError("SELL has invalid number types")

    if cmd == CMD_LIST:
        if len(parts) != 2:
            raise ValueError("LIST expects: LIST <owner_id>")
        return CMD_LIST, {"owner_id": int(parts[1])}

    if cmd == CMD_BALANCE:
        if len(parts) != 2:
            raise ValueError("BALANCE expects: BALANCE <owner_id>")
        return CMD_BALANCE, {"owner_id": int(parts[1])}

    if cmd == CMD_QUIT:
        if len(parts) != 1:
            raise ValueError("QUIT expects no arguments")
        return CMD_QUIT, {}

    if cmd == CMD_SHUTDOWN:
        if len(parts) != 1:
            raise ValueError("SHUTDOWN expects no arguments")
        return CMD_SHUTDOWN, {}

    # Unknown command
    raise KeyError(f"unknown command: {cmd}")



# Wire helpers (strings only)

def ok(body: str = "") -> str:
    """Return a success response terminated with a newline (and body if provided)."""
    return RESP_OK + "\n" + (body + "\n" if body else "")

def err_format(msg: str) -> str:
    """403 message format error + short detail."""
    return RESP_FORMAT_ERR + "\n" + (msg + "\n" if msg else "")

def err_invalid(msg: str) -> str:
    """400 invalid command + short detail."""
    return RESP_INVALID + "\n" + (msg + "\n" if msg else "")


# Rendering helpers for server replies

def render_list(owner_id: int, rows: List[Dict[str, Any]]) -> str:
    """
    Produce a human-friendly table for LIST results.
    """
    lines = []
    lines.append(f"The list of records in the Pokémon cards table for current user, user {owner_id}:")
    lines.append("")
    header = f"{'ID':<4} {'Card Name':<12} {'Type':<10} {'Rarity':<10} {'Count':<5} {'OwnerID':<7}"
    lines.append(header)
    for r in rows:
        lines.append(
            f"{int(r['ID']):<4} "
            f"{str(r['card_name']):<12} "
            f"{str(r['card_type']):<10} "
            f"{str(r['rarity']):<10} "
            f"{int(r['count']):<5} "
            f"{int(r['owner_id']):<7}"
        )
    return "\n".join(lines)

def render_balance(owner_display: str, balance: float) -> str:
    """Produce the BALANCE line like the example."""
    return f"Balance for user {owner_display}: ${balance:.2f}"

def make_display_name(first_name: str, last_name: str, user_name: str) -> str:
    """Prefer 'First Last' if present, otherwise fall back to user_name."""
    first = (first_name or "").strip()
    last = (last_name or "").strip()
    full = (first + " " + last).strip()
    return full if full else (user_name or "").strip() or "Unknown"
