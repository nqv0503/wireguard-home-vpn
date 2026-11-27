# 🔐 VPN truy cập mạng nhà từ xa (WireGuard)

Dựng **VPN server WireGuard** tại nhà để khi ở ngoài (quán cà phê, trường học, 4G), điện thoại và laptop vẫn **kết nối an toàn về mạng nhà**: Wi-Fi công cộng không đọc trộm được dữ liệu, vẫn truy cập được thiết bị trong LAN, và vẫn được Pi-hole lọc quảng cáo.

*Self-hosted WireGuard VPN (wg-easy on Docker) for secure remote access to a home network, including NAT/port-forwarding analysis for double-NAT and CGNAT setups.*

> 📌 **Trạng thái:** file cấu hình, script kiểm tra và hướng dẫn đã sẵn sàng. Kết quả đo tốc độ và ảnh chụp sẽ bổ sung sau khi triển khai.

## Sơ đồ hoạt động
```
  Điện thoại (4G / Wi-Fi quán cà phê)
  IP trong VPN: 10.8.0.2
        │
        │  UDP 51820, mã hóa ChaCha20-Poly1305
        ▼
   ┌─────────┐   port forward   ┌──────────────────┐
   │ Router  │ ───UDP 51820───▶ │ WireGuard server │ 10.8.0.1 (trong đường hầm)
   │ IP public│                 │ 192.168.0.3 (LAN)│
   └─────────┘                  └────────┬─────────┘
                                         │ NAT (MASQUERADE)
                     ┌───────────────────┼──────────────────┐
                     ▼                   ▼                  ▼
               Pi-hole (DNS)      Thiết bị trong LAN     Internet
```

## Cấu trúc repo
| File | Nội dung |
|---|---|
| `docker-compose.yml` | Chạy WireGuard kèm giao diện web wg-easy |
| `.env.example` | Tên miền/IP public, mật khẩu web (bcrypt), DNS |
| `wg0.conf.example` | Cấu hình WireGuard viết tay, có chú thích từng dòng |
| `scripts/check_cgnat.py` | Kiểm tra router có IP public hay bị CGNAT / double NAT |
| `docs/setup-guide.md` | Hướng dẫn chi tiết: DDNS, port forwarding, cấp cấu hình cho điện thoại |

## Bước 0: Kiểm tra mạng có dựng VPN được không
VPN server muốn nhận kết nối từ Internet thì router phải có **IP public**. Nhiều nhà mạng ở Việt Nam dùng **CGNAT**, khi đó mở cổng cũng vô ích.
```bash
python scripts/check_cgnat.py <WAN_IP_trong_trang_quản_trị_router>
```
Script phân biệt được 3 trường hợp (kết quả chạy thử):
```
WAN IP của router : 100.72.10.5  -> CGNAT (100.64.0.0/10)
❌ Nhà mạng đang dùng CGNAT: kết nối từ Internet không vào được router.

WAN IP của router : 192.168.1.6  -> IP riêng (RFC 1918)
⚠️  Router này nằm sau một router khác (double NAT).
   Phải port forward trên CẢ HAI router, hoặc chuyển modem nhà mạng sang bridge mode.

WAN IP của router : 113.161.1.1  -> IP public
✅ Router có IP public. Có thể port forward UDP 51820 để dùng WireGuard.
```

## Triển khai nhanh
```bash
git clone https://github.com/nqv0503/wireguard-home-vpn.git
cd wireguard-home-vpn
cp .env.example .env            # điền WG_HOST, PASSWORD_HASH, WG_DNS
docker compose up -d
```
1. Port forward **UDP 51820** trên router về máy chủ VPN.
2. Mở `http://<IP-máy-chủ>:51821`, tạo client mới.
3. Trên điện thoại, cài app **WireGuard** và quét **mã QR**.
4. Tắt Wi-Fi, dùng 4G, bật VPN rồi thử truy cập `http://192.168.0.1`.

Chi tiết xem [docs/setup-guide.md](docs/setup-guide.md).

## Vì sao chọn WireGuard?
| | WireGuard | OpenVPN |
|---|---|---|
| Số dòng code | khoảng 4.000 | hơn 100.000 |
| Giao thức | Chỉ UDP | UDP hoặc TCP |
| Mã hóa | Cố định: Curve25519, ChaCha20-Poly1305, BLAKE2s | Tùy chọn qua OpenSSL |
| Bắt tay | 1 vòng (1-RTT), kết nối gần như tức thì | Bắt tay TLS, chậm hơn |
| Đổi mạng (Wi-Fi sang 4G) | Tự nối lại, không rớt | Thường phải kết nối lại |

Mỗi thiết bị có một **cặp khóa công khai/bí mật**, giống SSH. Server chỉ chấp nhận các public key đã khai báo, và `AllowedIPs` vừa đóng vai trò bảng định tuyến vừa là bộ lọc gói (*cryptokey routing*).

## Kiến thức áp dụng
- **VPN và mã hóa**: khóa công khai Curve25519, mã hóa đối xứng, đường hầm lớp 3
- **NAT**: SNAT/MASQUERADE bằng iptables, port forwarding (DNAT), double NAT, CGNAT (RFC 6598)
- **Định tuyến**: full tunnel (`0.0.0.0/0`) và split tunnel (`192.168.0.0/24`), bật `ip_forward`
- **DDNS**: ánh xạ tên miền vào IP public thay đổi theo thời gian
- **Bảo mật**: không mở giao diện quản trị ra Internet, chỉ mở một cổng UDP

## Giới hạn và phương án dự phòng
- **Bị CGNAT:** xin nhà mạng cấp IP public, hoặc dùng **Tailscale/Headscale** (WireGuard có sẵn cơ chế xuyên NAT, không cần mở cổng).
- **Mạng công ty/trường chặn UDP:** WireGuard không chạy qua TCP. Khi đó phải dùng giải pháp khác.

## Liên quan
- [pihole-dns-sinkhole](https://github.com/nqv0503/pihole-dns-sinkhole): DNS lọc quảng cáo, dùng làm `WG_DEFAULT_DNS`

## Tác giả
**Nguyễn Quốc Việt** · [GitHub](https://github.com/nqv0503) · Giấy phép [MIT](LICENSE)
