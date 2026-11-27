"""
check_cgnat.py - Kiểm tra mạng nhà có dựng VPN server nhận kết nối từ ngoài được không
=====================================================================================
Muốn truy cập VPN về nhà, router nhà phải có IP public thật. Nhiều nhà mạng
dùng CGNAT (Carrier-Grade NAT): router chỉ nhận IP trong dải 100.64.0.0/10,
khi đó port forwarding vô tác dụng.

Cách dùng:
  1. Vào trang quản trị router, xem "WAN IP" (hoặc "Internet IP").
  2. Chạy:  python check_cgnat.py <WAN_IP_cua_router>
     Script tự lấy IP public từ api.ipify.org để so sánh.
     Không muốn gọi ra ngoài thì truyền thêm:  --public <IP_public>
"""

import argparse
import ipaddress
import urllib.request

CGNAT = ipaddress.ip_network("100.64.0.0/10")


def get_public_ip() -> str:
    with urllib.request.urlopen("https://api.ipify.org", timeout=5) as resp:
        return resp.read().decode().strip()


def classify(ip: ipaddress.IPv4Address) -> str:
    if ip in CGNAT:
        return "CGNAT (100.64.0.0/10)"
    if ip.is_private:
        return "IP riêng (RFC 1918)"
    return "IP public"


def main():
    parser = argparse.ArgumentParser(description="Kiểm tra CGNAT / double NAT")
    parser.add_argument("wan_ip", help="WAN IP hiển thị trong trang quản trị router")
    parser.add_argument("--public", help="IP public (mặc định: tự lấy từ api.ipify.org)")
    args = parser.parse_args()

    wan = ipaddress.ip_address(args.wan_ip)
    public = ipaddress.ip_address(args.public or get_public_ip())

    print(f"WAN IP của router : {wan}  -> {classify(wan)}")
    print(f"IP public thực tế : {public}  -> {classify(public)}\n")

    if wan == public:
        print("✅ Router có IP public. Có thể port forward UDP 51820 để dùng WireGuard.")
        print("   Nếu IP public thay đổi mỗi lần khởi động lại modem, hãy dùng DDNS.")
    elif wan in CGNAT:
        print("❌ Nhà mạng đang dùng CGNAT: kết nối từ Internet không vào được router.")
        print("   Cách xử lý: gọi tổng đài xin IP public (thường hỗ trợ miễn phí),")
        print("   hoặc dùng Tailscale/Headscale (không cần mở cổng).")
    elif wan.is_private:
        print("⚠️  Router này nằm sau một router khác (double NAT).")
        print("   Phải port forward trên CẢ HAI router, hoặc chuyển modem nhà mạng sang bridge mode.")
    else:
        print("⚠️  WAN IP và IP public khác nhau: có thể có thêm một lớp NAT ở phía nhà mạng.")


if __name__ == "__main__":
    main()
