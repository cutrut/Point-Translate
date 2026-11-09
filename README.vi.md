# Point & Translate

Gặp từ lạ thì rê chuột vào từ đó, bấm `2`. Bản dịch hiện ngay cạnh chữ.

Dùng để tra từ lúc chơi game hay đọc visual novel bằng tiếng đang học. App
đọc chữ trên màn hình, kể cả menu hay hộp thoại không bôi đen được. Miễn phí,
chạy trên Windows và đọc **chữ Latin** như tiếng Anh.

[English](README.md)

## Cài rồi chạy

1. Giải nén vào thư mục có quyền ghi. Để `point_and_translate.py` và hai
   file BAT chung một chỗ.
2. Chạy `Check_And_Install.bat`. File này kiểm tra **Python 3.12 x64**, thư
   viện Python, Chrome và engine OneOCR, rồi thử cài những thứ còn thiếu.
   Chờ đến khi báo `[READY]`.
3. Chạy `Start_Point_And_Translate.bat`. Trong cửa sổ Chrome dành cho DeepL,
   chọn ngôn ngữ nguồn và đích, tự làm bước xác thực nếu có, rồi dịch thử một
   câu ngắn. Để cửa sổ Chrome đó mở.
4. Thu nhỏ **Controls**, quay lại game hoặc ứng dụng đang đọc, rồi thử
    rê chuột vào một từ và bấm `2`.

Lần sau chỉ cần chạy `Start_Point_And_Translate.bat`.

Nếu đang dùng Hover Dict, giải nén vào thư mục app cũ, ghi đè
`Check_And_Install.bat` khi được hỏi. Mở bằng file chạy mới để dùng lại
phím đã lưu, cache bản dịch và phiên Chrome.

### Chạy từ CMD

Mở thư mục app trong File Explorer, gõ `cmd` vào thanh địa chỉ rồi nhấn
Enter. Chạy từng dòng, chờ lệnh đầu báo `[READY]` rồi mới chạy lệnh sau:

```bat
Check_And_Install.bat
Start_Point_And_Translate.bat
```

Muốn tự cài thư viện Python thì chạy
`py -3.12 -m pip install --user -r requirements.txt`. File kiểm tra lo
riêng phần Chrome và engine OneOCR.

## Phím bấm

| Phím | Làm gì |
| --- | --- |
| Rê chuột vào từ | Khoanh từ |
| `2` | Đọc và dịch từ ngay dưới con trỏ |
| Giữ `1`, rê qua mấy từ, rồi thả | Dịch phần chữ vừa chọn |
| `3` | Quét lại màn hình |
| `F8` | Bật hoặc tắt con trỏ riêng khi game ẩn hay ghim chuột |
| `Alt` trái + mũi tên | Nhích con trỏ riêng từng bước |
| `Esc` | Thoát app khi đang ở game hoặc ứng dụng đọc |

Rê chuột cũng di chuyển được con trỏ riêng. Game vẫn điều khiển chuột và
camera của nó.

Muốn đổi phím thì vào **Actions** hoặc **Pointer** trong **Controls**. Bấm
vào phím đang hiện, nhấn rồi thả phím mới, sau đó bấm **Save**. Bấm lại
cùng nút hoặc chuyển cửa sổ để hủy. Bấm **Defaults** rồi **Save** để lấy
lại phím mặc định.

Mỗi thao tác dùng một phím riêng. Game vẫn nhận phím như thường. Gán Ctrl
thì lúc bấm Ctrl trong tổ hợp khác, thao tác cũng chạy. Nếu gán `Pause` cho
thao tác cần giữ phím, bấm một lần để bắt đầu và một lần để dừng.
[Giới hạn phím Windows](https://learn.microsoft.com/en-us/windows/powertoys/keyboard-manager)

Phím tắt tạm ngưng khi **Controls** đang được chọn. Bấm **Minimise** để
app chạy tiếp hoặc **X** để thoát. Muốn mở riêng phần đổi phím thì chạy
`Start_Point_And_Translate.bat settings` trong CMD.

## Lúc bị kẹt

- **Cài bị lỗi.** Xem lỗi trong CMD. Nếu thiếu WinGet, cài Python 3.12 x64
  kèm Python Launcher và Tcl/Tk, rồi cài Chrome. Chạy lại file kiểm tra.
  [Python](https://www.python.org/downloads/windows/) · [Chrome](https://www.google.com/chrome/)
- **Thiếu file OneOCR.** File kiểm tra thử lấy từ Snipping Tool hoặc
  cài/cập nhật Snipping Tool qua Microsoft Store. Cài tay thì đặt bộ
  `oneocr.dll`, `oneocr.onemodel` và `onnxruntime.dll` cùng bản x64 vào
  `%USERPROFILE%\.config\oneocr\` rồi chạy lại file kiểm tra. [Cách cài OneOCR](https://github.com/AuroraWright/oneocr)
- **DeepL đứng.** Xem cửa sổ Chrome có yêu cầu xác thực không, kiểm tra lại
  ngôn ngữ và đọc lỗi trong CMD.
- **Game không hiện overlay.** Thử **Borderless Windowed**.
  **Hearts of Iron IV (HOI4)** hiện gặp lỗi tương thích.
- **Vừa đổi ngôn ngữ hoặc backend dịch.** Tắt app rồi xóa
  `hover_dict_cache.db`. Cache tra bản dịch theo chữ gốc.

## App lưu gì

OneOCR đọc chữ trên máy. Phần chữ được tra sẽ gửi sang DeepL.
`keybindings.json` lưu phím, `hover_dict_cache.db` lưu bản dịch và
`BotChromeProfile/` lưu phiên Chrome riêng của app. Tùy chọn OCR và dịch
nằm gần đầu file `point_and_translate.py`.

---

Mã nguồn và tài liệu dùng giấy phép MIT. Các thành phần bên ngoài có điều
khoản riêng. Kiểm thử trực tiếp trên Windows và trong game vẫn còn chờ.
[Danh sách kiểm thử](TESTING.md)

5.3.3 Simple · [Thay đổi](CHANGELOG.md) · [Giấy phép MIT](LICENSE)
