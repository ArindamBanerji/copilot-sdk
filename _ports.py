import socket
for port in [8010, 8020, 8030, 8002, 8001]:
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=2)
        s.close()
        print(f"  {port}: UP")
    except:
        print(f"  {port}: DOWN")
