
# Billing - Some mistakes can be costly. 

Складність: Easy

Ціль: 10.114.135.208

1. Розвідка (Reconnaissance & Enumeration)

    1.1. Сканування портів (Nmap):

     `sudo nmap -sS -sV -sC -Pn -p- -vv 10.114.135.208`    

     ![nmap](./img/nmap_scan.png)
        
    1.2. Веб-розвідка:

     ![html main page](./img/html_main.png)

     `gobuster dir -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt  -u http://10.114.135.208/ -t 50 -k -x html,txt,php`
     
     ![gobuster 1](./img/gobuster_1.png)

     `gobuster dir -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt  -u http://10.114.135.208/mbilling -t 50 -k -x html,txt,php`

     ![gobuster 2](./img/gobuster_2.png)

     ![CVE-2023-30258](./img/magnus_exploit_1.png)

     ![CVE-2023-30258](./img/magnus_exploit_2.png)

3. Точка входу (Initial Access / Foothold)

    2.1. Експлуатація вразливості:

      ![MSF](./img/msf_1.png)
   
    2.2. Отримання реверс-шеллу:

     ![MSF reverse shell](./img/msf_2.png)

3. Підвищення привілеїв (Privilege Escalation)

    3.1. Вертикальне підвищення (asterisk -> Root):

      ![user.txt](./img/user_txt.png)

      ![sudo -l](./img/sudo-l.png)

      Перепробував різні варіації, але вони не працювали, пробую ще цей варіант.

      ![GTFObins](./img/gtfobins.png)

      ![fail2ban root 1](./img/f2b_root_1.png)

      ![fail2ban root 2](./img/f2b_root_2.png)

      ![rootbash & root.txt](./img/root_txt.png)

     

     

      

