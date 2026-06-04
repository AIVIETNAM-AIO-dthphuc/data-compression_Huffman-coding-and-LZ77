# Mo phong nen du lieu LZ77 va Huffman Coding

Ung dung Flask nay dung de minh hoa hai thuat toan nen du lieu: LZ77 va Huffman Coding. App co hai luong chinh:

- Mo phong encode + decode tung buoc: nhap van ban truc tiep hoac upload file `.txt`.
- Decode tu file XLSX: upload bang token LZ77 hoac bang ma Huffman da co san.

## 1. Cau truc thu muc

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

File `.csv` trong testcase Huffman la file cu/doi chieu. Luong upload hien tai nen dung `.xlsx`.

## 2. Cai dat va chay ung dung

Can co Python va Flask.

```bash
pip install flask
cd "E:\CS112 - Seminar"
python app.py
```

Mo trinh duyet tai:

```text
http://127.0.0.1:5000
```

## 3. Luong 1: Mo phong encode + decode tung buoc

Chon `Mo phong encode + decode tung buoc`, sau do chon mot trong hai thuat toan:

- Thuat toan LZ77 (Sliding Window)
- Ma hoa Huffman Coding

Nguoi dung co the cung cap input bang mot trong hai cach:

- Nhap truc tiep vao o `Nhap van ban can nen`
- Upload file `.txt`

Neu vua nhap tay vua upload `.txt`, app se uu tien noi dung trong file `.txt`.

### Testcase cho luong encode

Dung cac file trong:

```text
testcase/encode
```

Goi y:

- `encode_input_01.txt`, `encode_input_02.txt`, `encode_input_03.txt`: input ngan, phu hop de xem tung buoc.
- `encode_input_04.txt` va `encode_input_10.txt`: input dai hon, dung de kiem tra che do rut gon khi qua nguong.
- `encode_input_06.txt` den `encode_input_09.txt`: cac testcase van ban khac nhau, co the dung cho ca LZ77 va Huffman.
- `encode_input_05..txt` co hai dau cham trong ten file, can chon dung ten khi upload.

Neu input `<= 500` ky tu, app hien thi tung buoc. Neu input `> 500` ky tu, app chi hien thi cac ket qua chinh de tranh giao dien qua nang.

## 4. LZ77 trong luong mo phong

Co the cau hinh:

- Search Window
- Lookahead Window

Neu de trong:

```text
Search Window = 13
Lookahead Window = 6
```

Quy tac dang dung:

```text
Do dai khop toi da l <= Lookahead - 1
```

Ket qua hien thi gom:

- Mo phong cua so truot theo tung buoc
- Token duoc them o moi buoc
- Bang token cuoi cung
- Bang decode LZ77
- Ket qua giai ma

Bang decode dai se duoc rut gon theo dang 10 dong dau, mot dong `...`, va 10 dong cuoi.

## 5. Huffman Coding trong luong mo phong

App hien thi:

- Bang tan suat ky tu
- Qua trinh xay cay Huffman
- Buoc gan bit tren canh: nhanh trai = `0`, nhanh phai = `1`
- Bang ma Huffman
- Chuoi bit sau ma hoa
- Truc quan hoa decode dua tren bang ma Huffman
- Ket qua giai ma
- Ti le nen (Compression Ratio)

Quy tac xay cay Huffman:

- Hang doi duoc sap tang dan theo so lan xuat hien.
- Neu bang so lan xuat hien, sap tiep theo ma ASCII.
- Moi lan lay 2 node dau hang doi: node dau tien dat ben phai, node thu hai dat ben trai.
- Neu node moi sau khi gop co cung tan suat voi node dang doi, uu tien node dang doi truoc.

Ky tu dac biet duoc hien thi ro:

```text
space -> ky tu khoang trang
\n    -> newline
\r    -> carriage return
\t    -> tab
```

## 6. Ti le nen Huffman

```text
Compression Ratio = Uncompressed Size / Compressed Size
```

Trong app:

```text
Uncompressed Size = so ky tu input * ceil(log2(so ky tu khac nhau))
Compressed Size   = so bit sau ma hoa Huffman
```

App dung kich thuoc ban dau theo fixed-length encoding, khong mac dinh moi ky tu la 8 bit.

## 7. Luong 2: Decode tu file XLSX

Chon `Decode tu file XLSX`, sau do chon thuat toan va upload file `.xlsx` tu thu muc testcase decode.

App doc sheet dau tien cua file XLSX. Hang dau tien phai la header.

## 8. XLSX cho LZ77

Dung cac file mau trong:

```text
testcase/decode/lz77
```

Danh sach testcase:

- `decode_LZ77_input_01.xlsx`
- `decode_LZ77_input_02.xlsx`
- `decode_LZ77_input_03.xlsx`
- `decode_LZ77_input_04.xlsx`
- `decode_LZ77_input_05.xlsx`

Dinh dang sheet dau tien:

| distance | length | next |
|---:|---:|---|
| 0 | 0 | a |
| 0 | 0 | b |
| 0 | 0 | c |
| 3 | 2 | d |

Y nghia:

- `distance`: so ky tu lui lai trong chuoi da khoi phuc.
- `length`: so ky tu can copy.
- `next`: ky tu tiep theo.
- Dung `<space>` neu `next` la dau cach.
- De trong hoac dung `<EOF>` neu khong co ky tu next.

## 9. XLSX cho Huffman

Dung cac file mau trong:

```text
testcase/decode/huffman_coding
```

Danh sach testcase:

- `decode_Huffman_input_01.xlsx`
- `decode_Huffman_input_02.xlsx`
- `decode_Huffman_input_03.xlsx`
- `decode_Huffman_input_04.xlsx`
- `decode_Huffman_input_05.xlsx`

Dinh dang sheet dau tien:

| encoded_bits | char | code |
|---|---|---|
| 010110 |  |  |
|  | A | 0 |
|  | B | 10 |
|  | `<space>` | 110 |

Y nghia:

- `encoded_bits`: chuoi bit can giai ma. Chi can mot dong co gia tri nay.
- `char`: ky tu goc.
- `code`: ma Huffman tuong ung voi ky tu.
- Dung `<space>` trong cot `char` neu ky tu la dau cach.

Luu y quan trong: cot `code` nen duoc dinh dang la **Text** trong Excel, neu khong cac ma nhu `0010` co the bi Excel doi thanh `10`.

## 10. Luu y ve file va Unicode

- File `.txt` nen luu bang UTF-8.
- File decode nen dung `.xlsx`, khong doi duoi thu cong tu `.csv` hoac `.xls`.
- Van ban tieng Viet Unicode duoc ho tro.
- Van ban nhieu dong co the tao ra ky tu `\n` hoac `\r`; cac ky tu nay van duoc tinh trong Huffman va se hien thi ro trong bang.

## 11. Loi thuong gap

### Khong upload duoc XLSX

Kiem tra file co that su la `.xlsx` hay khong. File `.xls` cu hoac file bi doi duoi thu cong co the khong doc duoc.

### Huffman decode sai voi ma co so 0 dau

Dinh dang cot `code` trong Excel la **Text** truoc khi nhap ma bit.

### Khong thay mo phong tung buoc

Input co the da vuot 500 ky tu. Khi do app tu dong rut gon hien thi.

### O ky tu trong bang Huffman bi trong

Neu ky tu la newline/carriage return/tab, app se hien thi `\n`, `\r`, `\t`. Neu van trong, hay kiem tra input co ky tu dieu khien dac biet khac hay khong.
