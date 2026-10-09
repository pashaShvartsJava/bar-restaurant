import qrcode

BASE_URL = "https://10.157.173.192:8443/menu_page/qr_code_menu"
TABLE_NUMBER = 5

for table_number in range(1, 9):
    url = f"{BASE_URL}?table_number={table_number}"
    qr = qrcode.make(url)
    qr.save(f"table_{table_number}.png")