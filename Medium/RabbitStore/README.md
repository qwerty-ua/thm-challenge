
# Rabbit Store - Demonstrate your web application testing skills and the basics of Linux to escalate your privileges.

Складність: Medium

Ціль: 

## 1. Розвідка (Reconnaissance & Enumeration)

### 1.1. Сканування портів (Nmap):
```bash
└─$ sudo nmap -sC -sV -p- -vv -oN nmap_result.txt 10.113.165.77
```

![nmap](./img/nmap.png)

```bash
└─$ sudo nano /etc/hosts
10.113.165.77   cloudsite.thm
```

### 1.2. Веб-розвідка:
```bash
└─$ gobuster dir -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt   -u http://cloudsite.thm -k -t 50 -x html,php,txt
```

![gobuster](./img/gobuster.png)

```bash
└─$ ffuf -w /usr/share/wordlists/seclists/Discovery/DNS/subdomains-top1million-110000.txt -u http://cloudsite.thm/ -H "Host:FUZZ.cloudsite.thm" -fw 18
```

![ffuf](./img/ffuf.png)

```bash
└─$ sudo nano /etc/hosts
10.113.165.77   cloudsite.thm   storage.cloudsite.thm
```

![storage_cloudsite_thm](./img/storage_cloudsite_thm.png)

![burp_register_1](./img/burp_register_1.png)
