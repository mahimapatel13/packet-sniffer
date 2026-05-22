from scapy.all import sniff, IP, TCP, UDP, ICMP, conf


conf.use_pcap = True
protocols = {
    1: "ICMP",
    6: "TCP",
    17: "UDP"
}

def process(packet):
    print("\nPacket:")

    if packet.haslayer(IP):
        print(f"Source IP: {packet[IP].src}")
        print(f"Destination IP: {packet[IP].dst}")
        proto = protocols.get(packet[IP].proto, "Unknown")
        # print(f"Protocol: {packet[IP].proto}")
        
        print(f"Protocol: {proto}")

    if packet.haslayer(TCP):
        print(f"TCP Port: {packet[TCP].sport} -> {packet[TCP].dport}")

    if packet.haslayer(UDP):
        print(f"UDP Port: {packet[UDP].sport} -> {packet[UDP].dport}")

sniff(iface="Wi-Fi", prn=process, store=False)