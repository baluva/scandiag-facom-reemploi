#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCANDIAG (TEXA Laser Examiner / FACOM DX.TSCANPB)
Outil de retro-ingenierie serie et de pilotage.

Le device expose une liaison serie : soit via Bluetooth SPP (port COM virtuel
apres appairage), soit via l'USB natif du STM32F429. Cet outil sert a :
  - lister les ports,
  - ecouter (sniff) et horodater les trames echangees,
  - balayer les baudrates pour trouver celui du device,
  - envoyer des commandes (hex/ascii) et lire les reponses,
  - ouvrir un mini-terminal interactif.

Usage:
  python scandiag_serial.py ports
  python scandiag_serial.py sniff   COMx [baud]
  python scandiag_serial.py scanbaud COMx
  python scandiag_serial.py send    COMx baud "AA 55 01 ..."   (octets en hex)
  python scandiag_serial.py sendtxt COMx baud "ATI"             (texte + CRLF)
  python scandiag_serial.py terminal COMx baud

Dependances: pyserial (deja installe).
"""
import sys
import time

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("pyserial manquant : pip install pyserial")
    sys.exit(1)

COMMON_BAUDS = [115200, 921600, 460800, 230400, 57600, 38400, 19200, 9600, 4800]


def list_ports():
    found = list(serial.tools.list_ports.comports())
    if not found:
        print("Aucun port COM detecte.")
        return
    print("Ports COM disponibles :")
    for p in found:
        print(f"  {p.device:8}  {p.description}   [{p.hwid}]")


def hexdump(data: bytes, width: int = 16) -> str:
    out = []
    for i in range(0, len(data), width):
        chunk = data[i:i + width]
        hexs = " ".join(f"{b:02X}" for b in chunk)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        out.append(f"  {i:04X}  {hexs:<{width*3}}  {text}")
    return "\n".join(out)


def sniff(port: str, baud: int = 115200):
    print(f"[sniff] {port} @ {baud} bauds — Ctrl+C pour arreter. "
          f"Manipule l'appareil / lance le logiciel TEXA pour capturer le trafic.")
    with serial.Serial(port, baud, timeout=0.2) as s:
        buf = bytearray()
        last = time.time()
        try:
            while True:
                data = s.read(4096)
                if data:
                    ts = time.strftime("%H:%M:%S")
                    print(f"\n[{ts}] +{len(data)} octets")
                    print(hexdump(data))
                    buf += data
                    last = time.time()
                elif buf and (time.time() - last) > 2:
                    print(f"  --- pause ({len(buf)} octets cumules) ---")
                    buf.clear()
        except KeyboardInterrupt:
            print("\n[sniff] arret.")


def scanbaud(port: str):
    print(f"[scanbaud] {port} — ecoute 1,5 s par baudrate, "
          f"declenche une action sur l'appareil pendant le test.")
    for baud in COMMON_BAUDS:
        try:
            with serial.Serial(port, baud, timeout=0.3) as s:
                time.sleep(0.1)
                s.reset_input_buffer()
                data = bytearray()
                t0 = time.time()
                while time.time() - t0 < 1.5:
                    data += s.read(256)
                printable = sum(1 for b in data if 32 <= b < 127 or b in (10, 13, 9))
                ratio = (printable / len(data)) if data else 0
                tag = ""
                if data and ratio > 0.8:
                    tag = "  <-- texte lisible (probable !)"
                elif data:
                    tag = "  <-- octets recus"
                print(f"  {baud:>7} bauds : {len(data):4d} octets recus{tag}")
                if data:
                    print(hexdump(bytes(data[:64])))
        except serial.SerialException as e:
            print(f"  {baud:>7} bauds : ERREUR {e}")


def send(port: str, baud: int, payload: bytes, read_s: float = 1.0):
    with serial.Serial(port, baud, timeout=0.2) as s:
        s.reset_input_buffer()
        s.write(payload)
        s.flush()
        print(f"[send] -> {len(payload)} octets : {payload.hex(' ').upper()}")
        time.sleep(0.05)
        resp = bytearray()
        t0 = time.time()
        while time.time() - t0 < read_s:
            resp += s.read(256)
        if resp:
            print(f"[recv] <- {len(resp)} octets :")
            print(hexdump(bytes(resp)))
        else:
            print("[recv] (aucune reponse)")


def terminal(port: str, baud: int):
    print(f"[terminal] {port} @ {baud} — tape une ligne (envoyee + CRLF), "
          f"'quit' pour sortir.")
    with serial.Serial(port, baud, timeout=0.2) as s:
        while True:
            try:
                line = input("> ")
            except (EOFError, KeyboardInterrupt):
                break
            if line.strip().lower() in ("quit", "exit"):
                break
            s.write((line + "\r\n").encode())
            time.sleep(0.2)
            resp = s.read(4096)
            if resp:
                print(hexdump(resp))


def main():
    a = sys.argv[1:]
    if not a or a[0] == "ports":
        list_ports(); return
    cmd = a[0]
    try:
        if cmd == "sniff":
            sniff(a[1], int(a[2]) if len(a) > 2 else 115200)
        elif cmd == "scanbaud":
            scanbaud(a[1])
        elif cmd == "send":
            payload = bytes.fromhex(a[3].replace(",", " "))
            send(a[1], int(a[2]), payload)
        elif cmd == "sendtxt":
            send(a[1], int(a[2]), (a[3] + "\r\n").encode())
        elif cmd == "terminal":
            terminal(a[1], int(a[2]))
        else:
            print(__doc__)
    except IndexError:
        print(__doc__)


if __name__ == "__main__":
    main()
