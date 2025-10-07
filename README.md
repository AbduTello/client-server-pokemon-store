# client-server-pokemon-store
This repository contains Programming Assignment 1 for CIS427 (Fall 2025). The project implements an online Pokémon card trading application using a client-server architecture over TCP sockets.

Team (Solo)
- Abdultawwab Tello (Abdulta@umich.edu)

Introduction
- Language: Python 3
- Platform: macOS (tested)
- Data store: SQLite (pokemon_store.db)
- Single-client TCP server; client REPL over TCP

How to Run
1) From project root:
   python3 -m server.server
2) In another terminal:
   python3 -m client.main 127.0.0.1 2780

Sample Commands
LIST 1
BALANCE 1
BUY Pikachu Electric Common 19.99 2 1
SELL Pikachu 1 34.99 1
QUIT
# restart client
SHUTDOWN

Protocol Notes
- Each server reply: status line + optional body + one blank line.
- No blank lines inside the body
- Encoding: UTF-8.

Files Included
- constants.py
- server/server.py, server/db.py, server/protocol.py, server/__init__.py
- client/main.py, client/__init__.py
- README.md (this file)
- (No compiled files)

Known Issues / Assumptions
- SELL aggregates across all variants of a card name.
- Monetary values use float; formatted to 2 decimals.

Roles
- Student 1: server loop, protocol parsing
- Student 2: database layer, client REPL

