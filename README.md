# Mô phỏng nén dữ liệu LZ77 và Huffman Coding

Ứng dụng Flask này dùng để minh họa hai thuật toán nén dữ liệu: LZ77 và Huffman Coding. App có hai luồng chính:

* Mô phỏng encode + decode từng bước: nhập văn bản trực tiếp hoặc upload file `.txt`.
* Decode từ file XLSX: upload bảng token LZ77 hoặc bảng mã Huffman đã có sẵn.

## 1. Cấu trúc thư mục

```text
E:\CS112 - Seminar
├── app.py
├── README.md
├── cs112-seminar.pptx
└── testcase
    ├── encode
    │   ├── encode_input_01.txt
    │   ├── encode_input_02.txt
    │   ├── encode_input_03.txt
    │   ├── encode_input_04.txt
    │   ├── encode_input_05..txt
    │   ├── encode_input_06.txt
    │   ├── encode_input_07.txt
    │   ├── encode_input_08.txt
    │   ├── encode_input_09.txt
    │   └── encode_input_10.txt
    └── decode
        ├── lz77
        │   ├── decode_LZ77_input_01.xlsx
        │   ├── decode_LZ77_input_02.xlsx
        │   ├── decode_LZ77_input_03.xlsx
        │   ├── decode_LZ77_input_04.xlsx
        │   └── decode_LZ77_input_05.xlsx
        └── huffman_coding
            ├── decode_Huffman_input_01.xlsx
            ├── decode_Huffman_input_02.xlsx
            ├── decode_Huffman_input_03.xlsx
            ├── decode_Huffman_input_04.xlsx
            ├── decode_Huffman_input_05.xlsx
            └── decode_Huffman_input_05.csv
```

File `.csv` trong testcase Huffman là file cũ/đối chiếu. Luồng upload hiện tại nên dùng `.xlsx`.

## 2. Cài đặt và chạy ứng dụng

Cần có Python và Flask.

```bash
pip install flask
cd "E:\CS112 - Seminar"
python app.py
```

Mở trình duyệt tại:

```text
http://127.0.0.1:5000
```

## 3. Luồng 1: Mô phỏng encode + decode từng bước

Chọn `Mô phỏng encode + decode từng bước`, sau đó chọn một trong hai thuật toán:

* Thuật toán LZ77 (Sliding Window)
* Mã hóa Huffman Coding

Người dùng có thể cung cấp input bằng một trong hai cách:

* Nhập trực tiếp vào ô `Nhập văn bản cần nén`
* Upload file `.txt`

Nếu vừa nhập tay vừa upload `.txt`, app sẽ ưu tiên nội dung trong file `.txt`.

### Testcase cho luồng encode

Dùng các file trong:

```text
testcase/encode
```

Gợi ý:

* `encode_input_01.txt`, `encode_input_02.txt`, `encode_input_03.txt`: input ngắn, phù hợp để xem từng bước.
* `encode_input_04.txt` và `encode_input_10.txt`: input dài hơn, dùng để kiểm tra chế độ rút gọn khi quá ngưỡng.
* `encode_input_06.txt` đến `encode_input_09.txt`: các testcase văn bản khác nhau, có thể dùng cho cả LZ77 và Huffman.
* `encode_input_05..txt` có hai dấu chấm trong tên file, cần chọn đúng tên khi upload.

Nếu input `<= 500` ký tự, app hiển thị từng bước. Nếu input `> 500` ký tự, app chỉ hiển thị các kết quả chính để tránh giao diện quá nặng.

## 4. LZ77 trong luồng mô phỏng

Có thể cấu hình:

* Search Window
* Lookahead Window

Nếu để trống:

```text
Search Window = 13
Lookahead Window = 6
```

Quy tắc đang dùng:

```text
Độ dài khớp tối đa l <= Lookahead - 1
```

Kết quả hiển thị gồm:

* Mô phỏng cửa sổ trượt theo từng bước
* Token được thêm ở mỗi bước
* Bảng token cuối cùng
* Bảng decode LZ77
* Kết quả giải mã

Bảng decode dài sẽ được rút gọn theo dạng 10 dòng đầu, một dòng `...`, và 10 dòng cuối.

## 5. Huffman Coding trong luồng mô phỏng

App hiển thị:

* Bảng tần suất ký tự
* Quá trình xây cây Huffman
* Bước gán bit trên cạnh: nhánh trái = `0`, nhánh phải = `1`
* Bảng mã Huffman
* Chuỗi bit sau mã hóa
* Trực quan hóa decode dựa trên bảng mã Huffman
* Kết quả giải mã
* Tỉ lệ nén (Compression Ratio)

Quy tắc xây cây Huffman:

* Hàng đợi được sắp tăng dần theo số lần xuất hiện.
* Nếu bằng số lần xuất hiện, sắp tiếp theo mã ASCII.
* Mỗi lần lấy 2 node đầu hàng đợi: node đầu tiên đặt bên phải, node thứ hai đặt bên trái.
* Nếu node mới sau khi gộp có cùng tần suất với node đang đợi, ưu tiên node đang đợi trước.

Ký tự đặc biệt được hiển thị rõ:

```text
space -> ký tự khoảng trắng
\n    -> newline
\r    -> carriage return
\t    -> tab
```

## 6. Tỉ lệ nén Huffman

```text
Compression Ratio = Uncompressed Size / Compressed Size
```

Trong app:

```text
Uncompressed Size = số ký tự input * ceil(log2(số ký tự khác nhau))
Compressed Size   = số bit sau mã hóa Huffman
```

App dùng kích thước ban đầu theo fixed-length encoding, không mặc định mỗi ký tự là 8 bit.

## 7. Luồng 2: Decode từ file XLSX

Chọn `Decode từ file XLSX`, sau đó chọn thuật toán và upload file `.xlsx` từ thư mục testcase decode.

App đọc sheet đầu tiên của file XLSX. Hàng đầu tiên phải là header.

## 8. XLSX cho LZ77

Dùng các file mẫu trong:

```text
testcase/decode/lz77
```

Danh sách testcase:

* `decode_LZ77_input_01.xlsx`
* `decode_LZ77_input_02.xlsx`
* `decode_LZ77_input_03.xlsx`
* `decode_LZ77_input_04.xlsx`
* `decode_LZ77_input_05.xlsx`

Định dạng sheet đầu tiên:

| distance | length | next |
| -------: | -----: | ---- |
|        0 |      0 | a    |
|        0 |      0 | b    |
|        0 |      0 | c    |
|        3 |      2 | d    |

Ý nghĩa:

* `distance`: số ký tự lùi lại trong chuỗi đã khôi phục.
* `length`: số ký tự cần copy.
* `next`: ký tự tiếp theo.
* Dùng `<space>` nếu `next` là dấu cách.
* Để trống hoặc dùng `<EOF>` nếu không có ký tự next.

## 9. XLSX cho Huffman

Dùng các file mẫu trong:

```text
testcase/decode/huffman_coding
```

Danh sách testcase:

* `decode_Huffman_input_01.xlsx`
* `decode_Huffman_input_02.xlsx`
* `decode_Huffman_input_03.xlsx`
* `decode_Huffman_input_04.xlsx`
* `decode_Huffman_input_05.xlsx`

Định dạng sheet đầu tiên:

| encoded_bits | char      | code |
| ------------ | --------- | ---- |
| 010110       |           |      |
|              | A         | 0    |
|              | B         | 10   |
|              | `<space>` | 110  |

Ý nghĩa:

* `encoded_bits`: chuỗi bit cần giải mã. Chỉ cần một dòng có giá trị này.
* `char`: ký tự gốc.
* `code`: mã Huffman tương ứng với ký tự.
* Dùng `<space>` trong cột `char` nếu ký tự là dấu cách.

Lưu ý quan trọng: cột `code` nên được định dạng là **Text** trong Excel, nếu không các mã như `0010` có thể bị Excel đổi thành `10`.

## 10. Lưu ý về file và Unicode

* File `.txt` nên lưu bằng UTF-8.
* File decode nên dùng `.xlsx`, không đổi đuôi thủ công từ `.csv` hoặc `.xls`.
* Văn bản tiếng Việt Unicode được hỗ trợ.
* Văn bản nhiều dòng có thể tạo ra ký tự `\n` hoặc `\r`; các ký tự này vẫn được tính trong Huffman và sẽ hiển thị rõ trong bảng.

## 11. Lỗi thường gặp

### Không upload được XLSX

Kiểm tra file có thật sự là `.xlsx` hay không. File `.xls` cũ hoặc file bị đổi đuôi thủ công có thể không đọc được.

### Huffman decode sai với mã có số 0 đầu

Định dạng cột `code` trong Excel là **Text** trước khi nhập mã bit.

### Không thấy mô phỏng từng bước

Input có thể đã vượt 500 ký tự. Khi đó app tự động rút gọn hiển thị.

### Ô ký tự trong bảng Huffman bị trống

Nếu ký tự là newline/carriage return/tab, app sẽ hiển thị `\n`, `\r`, `\t`. Nếu vẫn trống, hãy kiểm tra input có ký tự điều khiển đặc biệt khác hay không.
