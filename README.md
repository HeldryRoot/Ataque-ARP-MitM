# Ataque-ARP-MitM

<img width="654" height="276" alt="image" src="https://github.com/user-attachments/assets/edfcc30b-66cc-4465-95dc-13ea7e5fda80" />

**LABORATORIO DE SEGURIDAD DE REDES**

**ARP MitM**

_Documentación Técnica Profesional_

**Estudiante:**

**Heldry Terrero**

Matrícula: 2025-0719

Materia: Seguridad de Redes

Fecha: Junio 2026

  
  

# Aviso de Uso Responsable

|   |
|---|
|**⚠  AVISO IMPORTANTE — LEA ANTES DE UTILIZAR ESTE MATERIAL**<br><br>Este proyecto fue desarrollado únicamente con fines educativos, académicos<br><br>y de laboratorio controlado, en el marco de la asignatura Seguridad de Redes.<br><br>Los scripts, comandos y técnicas incluidos en este repositorio deben ejecutarse<br><br>SOLAMENTE en entornos propios o autorizados, tales como:<br><br>   • Simuladores: PNetLab, GNS3, EVE-NG<br><br>   • Laboratorios internos de práctica académica<br><br>   • Redes virtuales de prueba bajo supervisión docente<br><br>QUEDA ESTRICTAMENTE PROHIBIDO:<br><br>   • Utilizar este material en redes públicas, corporativas o de terceros<br><br>     sin autorización explícita y por escrito.<br><br>   • Interceptar, alterar o interrumpir comunicaciones ajenas.<br><br>   • Aplicar estas técnicas con fines maliciosos o fraudulentos.<br><br>El uso indebido de estas herramientas puede constituir un delito tipificado<br><br>en las leyes de ciberseguridad y delitos informáticos vigentes.<br><br>El autor de este material no se hace responsable del uso indebido del mismo.|

# Documentación Técnica — Ataque MitM mediante ARP Spoofing

|**Campo**|**Valor**|
|---|---|
|Estudiante|Heldry Terrero|
|Matrícula|2025-0719|
|Materia|Seguridad de Redes|
|Script|arp_mitm.py|
|Fecha|Junio 2026|
|Plataforma|PNetLab — Kali Linux|

# 1. Objetivo del Laboratorio

Demostrar cómo la ausencia de autenticación en el protocolo ARP permite a un atacante posicionarse entre la víctima y el gateway, interceptando y potencialmente modificando todo el tráfico de red.

# 2. Objetivo del Script

Envenenar las tablas ARP de la víctima (20.25.7.10) y del gateway (20.25.7.1) enviando respuestas ARP falsas de forma continua, haciendo que ambos asocien la MAC del atacante con la IP del otro extremo.

# 3. Requisitos

## 3.1 Software

•        Python 3.7 o superior

•        Scapy 2.4.3: sudo apt install python3-scapy

•        Kali Linux con interfaz eth1 conectada al switch

•        Privilegios de root (sudo)

## 3.2 Red

•        Atacante: 20.25.7.100/24 en eth1

•        Víctima: 20.25.7.10/24

•        Gateway/Router: 20.25.7.1/24

•        Red: 20.25.7.0/24

# 4. Parámetros del Script

|**Parámetro**|**Descripción**|**Default**|
|---|---|---|
|-i / --iface|Interfaz de red|Requerido|
|-v / --victim|IP de la víctima|Requerido|
|-g / --gateway|IP del gateway|Requerido|
|-t / --interval|Intervalo entre paquetes ARP (seg)|2.0|
|--sniff|Capturar tráfico interceptado|False|

# 5. Cómo se Ejecutó el Script

**Comando utilizado durante la demostración:**

sudo python3 arp_mitm.py -i eth1 -v 20.25.7.10 -g 20.25.7.1

sudo python3 arp_mitm.py -i eth1 -v 20.25.7.10 -g 20.25.7.1 --sniff

|   |
|---|
|**Resultado esperado en pantalla**<br><br>[*] Resolviendo MACs...<br><br>[+] Atacante : 50:f0:0a:00:04:00<br><br>[+] Victima  : 50:18:67:00:05:00  (20.25.7.10)<br><br>[+] Gateway  : aa:bb:cc:00:01:00  (20.25.7.1)<br><br>[+] IP Forwarding habilitado<br><br>[+] Paquetes ARP enviados: 10|

# 6. Funcionamiento del Ataque

El ataque funciona enviando ARP Replies no solicitados (gratuitous ARP) de forma continua. A la víctima se le dice que la MAC del gateway es la MAC del atacante. Al gateway se le dice que la MAC de la víctima es la MAC del atacante. Con IP Forwarding habilitado, el atacante reenvía el tráfico entre ambos extremos, siendo completamente transparente.

•        Paso 1: Se resuelven las MACs reales de víctima y gateway mediante ARP Request legítimo.

•        Paso 2: Se habilita IP Forwarding en el kernel Linux para reenviar el tráfico interceptado.

•        Paso 3: Se envía ARP Reply a la víctima: 'La IP 20.25.7.1 tiene la MAC del atacante'.

•        Paso 4: Se envía ARP Reply al gateway: 'La IP 20.25.7.10 tiene la MAC del atacante'.

•        Paso 5: Se repite cada 2 segundos para mantener el envenenamiento activo.

•        Paso 6: Al terminar (Ctrl+C), se restauran las tablas ARP originales automáticamente.

# 7. Verificación del Ataque

**Para confirmar que el ataque fue exitoso, se ejecutaron los siguientes comandos:**

arp -a                              (en Windows víctima)

Verificar que 20.25.7.1 tiene MAC del atacante

sudo tcpdump -i eth1 -n             (en Kali, ver tráfico interceptado)

|   |
|---|
|**¿Qué se debe observar?**<br><br>En 'arp -a' de Windows: la IP 20.25.7.1 ahora tiene la MAC 50:f0:0a:00:04:00 (atacante).<br><br>Con --sniff: se ven los paquetes TCP/UDP de la víctima en la consola del atacante.<br><br>La víctima mantiene conectividad (IP Forwarding activo).|

# 8. Contramedidas

Dynamic ARP Inspection (DAI) valida cada paquete ARP contra la base de datos de DHCP Snooping, descartando respuestas ARP que no correspondan a asignaciones DHCP legítimas.

Switch(config)# ip arp inspection vlan 1

Switch(config-if)# ip arp inspection trust    ! Solo en uplinks confiables

arp -s 20.25.7.1 <mac-real>                  ! ARP estático en la víctima

# 9. Conclusión

El ataque ARP MitM ilustra perfectamente las consecuencias de usar protocolos sin autenticación en redes locales. La combinación de DHCP Snooping con Dynamic ARP Inspection elimina prácticamente este vector de ataque en entornos corporativos.

Link de GitHub: https://github.com/HeldryRoot/Ataque-ARP-MitM.git

Link del Video de Youtube: https://youtu.be/ZRtsuEBaK-A?si=RmAPJCY-bA7T-aKo

**Heldry Terrero — Matrícula 2025-0719 — Seguridad de Redes — Junio 2026**
