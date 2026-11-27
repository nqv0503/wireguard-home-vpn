# Hướng dẫn triển khai chi tiết

## 1. Kiểm tra IP public và CGNAT
1. Đăng nhập trang quản trị router, ghi lại **WAN IP**.
2. Chạy `python scripts/check_cgnat.py <WAN_IP>`.
3. Xử lý theo kết quả:
   - **IP public:** sang bước 2.
   - **CGNAT:** gọi tổng đài nhà mạng (VNPT, Viettel, FPT) yêu cầu cấp IP public cho đường truyền gia đình, hoặc chuyển sang Tailscale.
   - **Double NAT:** port forward trên cả hai router (xem bước 4).

## 2. Đăng ký DDNS
IP public của gia đình thường **thay đổi** mỗi khi modem khởi động lại. DDNS cấp cho bạn một tên miền cố định, tự cập nhật theo IP mới.
- Dịch vụ miễn phí: **DuckDNS** (duckdns.org) hoặc **No-IP**.
- Nhiều router có sẵn mục **DDNS**: điền tài khoản vào đó là router tự cập nhật.
- Điền tên miền vào `WG_HOST` trong file `.env`.

## 3. Chạy WireGuard server
Máy chủ là Linux trong LAN, cài Docker giống dự án Pi-hole.
```bash
cp .env.example .env
docker run --rm ghcr.io/wg-easy/wg-easy:14 wgpw 'mat-khau-cua-ban'   # in ra PASSWORD_HASH
nano .env
docker compose up -d
docker logs -f wg-easy
```

## 4. Port forwarding
Trên router (mục **NAT / Port Forwarding / Virtual Server**):

| Trường | Giá trị |
|---|---|
| Giao thức | **UDP** |
| Cổng ngoài | 51820 |
| IP nội bộ | IP máy chủ VPN (ví dụ `192.168.0.3`, nên đặt IP tĩnh) |
| Cổng nội bộ | 51820 |

**Trường hợp double NAT** (ví dụ: modem nhà mạng `192.168.1.1`, phía sau là router Wi-Fi có WAN `192.168.1.6`):
```
Internet ─▶ Modem (IP public) ─UDP 51820─▶ Router Wi-Fi (192.168.1.6) ─UDP 51820─▶ Máy chủ VPN (192.168.0.3)
          forward lần 1 về 192.168.1.6      forward lần 2 về 192.168.0.3
```
Hoặc gọn hơn: chuyển modem nhà mạng sang **bridge mode** để chỉ còn một lớp NAT.

⚠️ **Không** mở cổng 51821 (giao diện web) ra Internet.

## 5. Tạo cấu hình cho điện thoại
1. Mở `http://<IP-máy-chủ>:51821` **từ trong LAN**.
2. Bấm **New Client**, đặt tên (ví dụ `iphone`).
3. Cài app **WireGuard** trên điện thoại, chọn **Add tunnel → Scan QR code**.

## 6. Kiểm tra
Tắt Wi-Fi trên điện thoại, dùng 4G, bật VPN rồi kiểm tra:

| Kiểm tra | Kết quả mong đợi |
|---|---|
| Trong app WireGuard | Có số liệu "Latest handshake" và dữ liệu gửi/nhận tăng dần |
| Mở `http://192.168.0.1` | Vào được trang quản trị router nhà |
| Tra IP trên trang whatismyip | Hiện IP public **của nhà bạn**, không phải IP của 4G |
| Mở trang có quảng cáo | Quảng cáo bị chặn (nếu `WG_DNS` trỏ về Pi-hole) |

Trên máy chủ, xem danh sách peer đang kết nối:
```bash
docker exec wg-easy wg show
```

## Xử lý sự cố
| Hiện tượng | Nguyên nhân thường gặp |
|---|---|
| Không bao giờ có handshake | Chưa port forward, forward nhầm TCP, bị CGNAT, hoặc `WG_HOST` sai |
| Có handshake nhưng không vào được web | Thiếu `ip_forward` hoặc thiếu luật NAT. Kiểm tra `sysctls` trong compose |
| Vào được Internet nhưng không phân giải được tên miền | `WG_DNS` trỏ tới DNS không truy cập được từ trong đường hầm |
| Kết nối được ở nhà nhưng ra ngoài thì không | Trong nhà kết nối qua IP LAN; ra ngoài mới thật sự đi qua port forward. Kiểm tra lại bước 4 |
