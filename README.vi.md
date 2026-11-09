# Hover Dict — bản gọn

Trỏ vào chữ trên màn hình, bấm phím và đọc bản dịch cạnh từ. Dùng OneOCR và
DeepL cho game, visual novel hoặc ứng dụng không cho chọn chữ.

**Chỉ hỗ trợ chữ dùng bảng Latin, ví dụ tiếng Anh.** Một số game, gồm
**Hearts of Iron IV (HOI4)**, hiện không hoạt động với công cụ này.

[English](README.md)

**Phiên bản: 5.3.3 Simple** · [Thay đổi](CHANGELOG.md) · [Kiểm thử](TESTING.md) · [MIT License](LICENSE)

## Có những file nào?

| File | Dùng làm gì? |
| --- | --- |
| `Start_Hover_Dict.bat` | Bấm đúp để mở Chrome DeepL và chạy app |
| `hover_dict.py` | Toàn bộ app, gồm cả cửa sổ đổi phím |
| `Check_And_Install.bat` | Kiểm tra và cài những thứ còn thiếu |
| `requirements.txt` | Danh sách thư viện Python, dùng khi muốn cài bằng CMD |
| `README.md`, `README.vi.md` | Hướng dẫn tiếng Anh và tiếng Việt |
| `CHANGELOG.md`, `TESTING.md` | Thay đổi của bản mới và checklist kiểm thử Windows |
| `LICENSE` | Giấy phép MIT cho Hover Dict |

Đặt ba file chạy cùng thư mục. Giữ nguyên tên file trong ZIP.

## Cài và chạy

1. Giải nén ZIP vào một thư mục có quyền ghi. App dùng **Windows, Python 3.12 x64**.
2. Chạy **`Check_And_Install.bat`**. File này kiểm tra đúng Python mà launcher
   sử dụng, rồi dùng pip cài các thư viện còn thiếu. Những gói đã import được
   sẽ được giữ lại; không cần tạo môi trường `.venv`.
3. Nếu thiếu Python hoặc Chrome, bộ kiểm tra thử cài qua WinGet. Với OneOCR,
   nó kiểm tra ba file engine, thử lấy từ Snipping Tool trên máy và thử
   cài/cập nhật Snipping Tool qua Microsoft Store nếu chưa tìm thấy.
   Nếu không thể hoàn tất, nó báo rõ mục còn thiếu; xử lý theo thông báo rồi chạy lại.
4. Khi báo **`[READY]`**, mở **`Start_Hover_Dict.bat`**.
5. Vào tab DeepL trong cửa sổ Chrome riêng. **Kiểm tra và tự hoàn tất CAPTCHA/
   xác thực nếu có**, rồi chọn đúng **ngôn ngữ nguồn và ngôn ngữ đích**.
   Dịch thử một câu và giữ cửa sổ Chrome này mở.
6. Thu nhỏ cửa sổ Hover Dict hoặc chuyển về game/ứng dụng đang đọc, trỏ vào
   chữ rồi bấm phím dịch (`2` mặc định).

Những lần sau chỉ cần chạy `Start_Hover_Dict.bat`. Nếu báo thiếu thư viện,
chạy lại `Check_And_Install.bat`.

**Nâng cấp từ 5.3.2:** file app đã đổi thành `hover_dict.py`. Thay đồng thời
hai file BAT và file Python. Giữ lại `keybindings.json`, `hover_dict_cache.db`
và `BotChromeProfile/` trong cùng thư mục để tiếp tục dùng cấu hình và dữ liệu
cũ. Hai file BAT mới không còn gọi file Python tên cũ.

## Muốn nhập lệnh trong CMD

Mở thư mục app bằng **File Explorer** → bấm thanh địa chỉ → gõ `cmd` →
nhấn **Enter**. Trong cửa sổ CMD vừa mở, nhập từng lệnh và nhấn **Enter**:

```bat
Check_And_Install.bat
Start_Hover_Dict.bat
```

Chờ lệnh kiểm tra kết thúc và báo `[READY]` trước khi chạy lệnh mở app.
Nếu muốn tự cài thư viện sau khi đã có Python 3.12:

```bat
py -3.12 -m pip install --user -r requirements.txt
```

Pip cài các thư viện Python; ba file engine OneOCR và Chrome được kiểm tra
riêng bởi `Check_And_Install.bat`. Không cần chạy `playwright install`, vì
app kết nối vào Chrome đang mở.

## Đổi phím ngay trong app

Giao diện app và các thông báo dùng **tiếng Anh**.

1. Trong cửa sổ **Controls**, mở tab **Actions** hoặc **Pointer**.
2. Bấm nút đang hiện phím hiện tại cạnh thao tác muốn đổi.
3. Nhấn rồi thả phím muốn gán. Nút sẽ hiện phím vừa nhận. Bấm lại nút đó hoặc
   chuyển sang cửa sổ khác để hủy việc chọn phím.
4. Bấm **Save**, rồi **Minimise** hoặc quay về game. Phím mới có hiệu lực ngay.

Có thể gán các phím Windows nhận được: dấu câu, Ctrl/Alt/Shift/Win, numpad,
F1–F24, Print Screen, phím media… Không cần gõ tên phím hoặc chọn trong danh sách.
Mỗi thao tác dùng một phím đơn, chưa gán cả tổ hợp như `Ctrl+2` thành một binding.
Phím trùng bị từ chối. Nút **Defaults** chọn lại phím mặc định; bấm **Save** để
áp dụng. App tự đọc lại cấu hình đã lưu từ bản trước.

Nếu gán một phím bổ trợ cho thao tác, thao tác đó cũng chạy khi nhấn phím ấy
trong một tổ hợp khác. Các phím thao tác vẫn được Windows/game nhận đồng thời. **Pause** chỉ gửi tín hiệu bấm: khi gán cho gom từ hoặc
phím giữ di chuyển con trỏ, bấm một lần để bắt đầu và bấm lần nữa để dừng.
Phím chỉ hoạt động trong phần cứng như Fn và các tổ hợp hệ thống dành riêng
có thể không được Windows gửi tới app; xem [giới hạn phím Windows](https://learn.microsoft.com/en-us/windows/powertoys/keyboard-manager).

Khi cửa sổ **Controls** đang được chọn, phím tắt dịch tạm ngưng. Đóng bằng dấu
**X** sẽ thoát app; muốn tiếp tục dùng thì bấm **Minimise**. Chỉ muốn chỉnh phím
mà chưa chạy OCR: mở CMD như trên rồi nhập:

```bat
Start_Hover_Dict.bat settings
```

## Phím mặc định

| Phím | Chức năng |
| --- | --- |
| Rê vào chữ | Khoanh từ, chưa dịch |
| `2` | Chụp ảnh mới và dịch từ tại con trỏ |
| Giữ `1`, rê qua từ, rồi thả | Gom và dịch một cụm từ |
| `3` | Quét OCR lại toàn màn hình |
| `F8` | Hiện/ẩn con trỏ ảo cho một số game hoặc VN ẩn/ghim chuột |
| `Alt` trái + mũi tên | Chỉnh vị trí con trỏ ảo từng bước |
| `Esc` | Thoát app khi đang ở game/ứng dụng đọc |

**Con trỏ ảo** là dấu ngắm riêng để chỉ vào chữ khi game/VN ẩn con trỏ thật
hoặc ghim nó giữa màn hình. Rê chuột để di chuyển dấu ngắm, hoặc dùng phím
chỉnh vị trí. Nó không mở khóa chuột hoặc dừng camera của game. Tùy game mà
hoạt động được; lưu ý về HOI4 ở trên vẫn áp dụng.

## Khi thiếu engine hoặc gặp lỗi

- Nếu không có WinGet, cài [Python 3.12 x64](https://www.python.org/downloads/windows/)
  kèm **Python Launcher** và **Tcl/Tk**, cùng [Chrome](https://www.google.com/chrome/),
  rồi mở lại file kiểm tra.
- Nếu không tự lấy được engine, làm theo [hướng dẫn OneOCR](https://github.com/AuroraWright/oneocr).
  Đặt bộ ba `oneocr.dll`, `oneocr.onemodel`, `onnxruntime.dll` **cùng bản x64**
  vào `%USERPROFILE%\.config\oneocr\`, rồi chạy kiểm tra lại.
- Không hiện overlay trong game: thử **Borderless Windowed**. Không phải mọi game đều tương thích.
- Không dịch: xem lỗi trong CMD, kiểm tra xác thực và ngôn ngữ trên tab DeepL.
- Đổi ngôn ngữ nguồn/đích hoặc backend: tắt app rồi xóa `hover_dict_cache.db`,
  vì cache hiện chỉ phân biệt nội dung đầu vào.

App tự tạo `keybindings.json` khi lưu phím, `hover_dict_cache.db` khi dùng cache
và `BotChromeProfile/` khi mở Chrome riêng; không cần tải hay tạo chúng thủ công.
OCR chạy local, nội dung được chọn gửi tới DeepL. Cấu hình OCR/backend nâng cao
nằm đầu file Python. Phạm vi hỗ trợ chỉ gồm chữ Latin.

## Tình trạng kiểm thử

Bản này có kiểm tra tự động cho cú pháp Python, trợ giúp dòng lệnh, thông báo
trên hệ điều hành không được hỗ trợ, nhận/lưu phím và logic hỗ trợ cài đặt.
Tên file mà launcher gọi và nội dung ZIP cũng được kiểm tra. Các bước đó chưa
xác minh cài đặt Windows, engine OCR thật, hook bàn phím, Chrome/DeepL hay
overlay trong game. Kiểm thử Windows thực tế **chưa hoàn tất**; dùng
[TESTING.md](TESTING.md) để ghi kết quả trước khi công bố khả năng tương thích.

## Giấy phép và thành phần bên ngoài

Mã nguồn và tài liệu Hover Dict dùng [giấy phép MIT](LICENSE), copyright (c)
2026 cutrut. Các thư viện Python, Chrome, file engine Microsoft Snipping
Tool/OneOCR và DeepL tuân theo giấy phép, điều khoản riêng của từng bên.
Bản phát hành không kèm file nhị phân engine OCR; xem
[hướng dẫn OneOCR](https://github.com/AuroraWright/oneocr).
