from flask import Flask, request, render_template_string
import collections
import csv
import html
import io
import math
import re
import xml.etree.ElementTree as ET
import zipfile

app = Flask(__name__)
MAX_VISUALIZATION_CHARS = 500

def format_visible_char(char):
    if char == " ":
        return "space"
    if char == "\n":
        return "\\n"
    if char == "\r":
        return "\\r"
    if char == "\t":
        return "\\t"
    if char and not char.isprintable():
        return f"U+{ord(char):04X}"
    return html.escape(str(char))

# ==========================================
# 1. THUẬT TOÁN LZ77 
# ==========================================
def lz77_compress_web(text, search_window_size, lookahead_window_size):
    if not text:
        return "<p>Vui lòng nhập văn bản!</p>"
        
    html_output = f"<div class='info-text'><b>Chuỗi đầu vào:</b> {text} <br>"
    html_output += f"<b>Search Window:</b> {search_window_size} ô | <b>Lookahead Window:</b> {lookahead_window_size} ô<br>"
    html_output += f"<b>Quy tắc:</b> Độ dài khớp tối đa l ≤ Lookahead - 1 = {max(0, lookahead_window_size - 1)} ô</div>"
    show_steps = len(text) <= MAX_VISUALIZATION_CHARS
    if not show_steps:
        html_output += (
            f"<div class='length-notice'><b>Thông báo:</b> Input có {len(text)} ký tự, vượt quá "
            f"{MAX_VISUALIZATION_CHARS} ký tự. Chương trình chỉ hiển thị kết quả cuối cùng, "
            "không hiển thị mô phỏng từng bước.</div>"
        )
    
    i = 0
    compressed_data = []
    step = 1
    if show_steps:
        html_output += "<h3>Mô phỏng Cửa sổ trượt (Sliding Window):</h3>"
    
    while i < len(text):
        search_start = max(0, i - search_window_size)
        search_buf = text[search_start:i]
        lookahead_buf = text[i:i + lookahead_window_size]
        
        best_match_distance = 0
        best_match_length = 0
        
        max_match_length = max(0, min(len(lookahead_buf) - 1, lookahead_window_size - 1))
        for length in range(1, max_match_length + 1):
            substring = lookahead_buf[:length]
            idx = search_buf.rfind(substring)
            if idx != -1:
                best_match_distance = len(search_buf) - idx
                best_match_length = length
            else:
                break
                
        next_char_idx = i + best_match_length
        next_char = text[next_char_idx] if next_char_idx < len(text) else ''
        token = (best_match_distance, best_match_length, next_char)
        compressed_data.append((step, search_buf, lookahead_buf, token))

        if show_steps:
            html_output += f"<div class='step-container'><b>Bước {step}:</b><br><div class='tape'>"
            focus_end = max(i + lookahead_window_size, next_char_idx + 1)
            visible_start = max(0, search_start - 3)
            visible_end = min(len(text), focus_end + 3)

            if visible_start > 0:
                html_output += "<span class='char skipped'>...</span>"

            for j in range(visible_start, visible_end):
                char = text[j]
                if j < search_start:
                    css_class = "char processed"
                elif search_start <= j < i:
                    css_class = "char search-win"
                elif i <= j < i + lookahead_window_size:
                    if i <= j < i + best_match_length:
                        css_class = "char lookahead-win matched"
                    elif j == next_char_idx:
                        css_class = "char lookahead-win next-char"
                    else:
                        css_class = "char lookahead-win"
                else:
                    css_class = "char unprocessed"
                html_output += f"<span class='{css_class}'>{char}</span>"

            if visible_end < len(text):
                html_output += "<span class='char skipped'>...</span>"

            html_output += "</div>"
            if best_match_length > 0:
                html_output += f"<div class='step-desc'>&rarr; Khớp đoạn <b>'{lookahead_buf[:best_match_length]}'</b>. Lùi lại {best_match_distance} ô, lấy thêm {best_match_length} ô. Ký tự tiếp theo: <b>'{next_char}'</b></div>"
            else:
                html_output += f"<div class='step-desc'>&rarr; Không có chuỗi khớp. Ký tự tiếp theo: <b>'{next_char}'</b></div>"
            html_output += "<table class='step-token-table'>"
            html_output += "<tr><th>Bước</th><th>Khoảng cách lùi (Distance)</th><th>Độ dài khớp (Length)</th><th>Ký tự tiếp (Next)</th><th>Mã Token được thêm</th></tr>"
            html_output += f"<tr><td>{step}</td><td>{token[0]}</td><td>{token[1]}</td><td>{token[2] if token[2] else '<i>(EOF)</i>'}</td><td><b>{token}</b></td></tr>"
            html_output += "</table>"
            html_output += "</div>"
        
        i += best_match_length + 1
        step += 1

    html_output += "<h3>Bảng kết quả Token (Đầu ra LZ77):</h3>"
    html_output += "<table class='result-table'>"
    html_output += "<tr><th>Bước</th><th>Khoảng cách lùi (Distance)</th><th>Độ dài khớp (Length)</th><th>Ký tự tiếp (Next)</th><th>Mã Token xuất ra</th></tr>"
    for s, _, _, tk in compressed_data:
        html_output += f"<tr><td>{s}</td><td>{tk[0]}</td><td>{tk[1]}</td><td>{tk[2] if tk[2] else '<i>(EOF)</i>'}</td><td><b>{tk}</b></td></tr>"
    html_output += "</table>"

    html_output += "<h3>Trực quan hóa quá trình giải mã LZ77:</h3>"
    html_output += "<div class='decode-box'>"
    html_output += "<div class='step-desc'>Đọc lần lượt từng token <b>(Distance, Length, Next)</b>: lùi lại <b>Distance</b> ký tự trong chuỗi đã khôi phục, chép <b>Length</b> ký tự, sau đó nối thêm ký tự <b>Next</b>.</div>"
    html_output += "<table class='decode-table'>"
    html_output += "<tr><th>Bước</th><th>Token</th><th>Thao tác copy</th><th>Đoạn khớp khôi phục</th><th>Ký tự Next</th><th>Chuỗi đã khôi phục</th></tr>"

    def compact_lz77_preview(chars):
        decoded_so_far = "".join(chars)
        if len(decoded_so_far) <= 90:
            return html.escape(decoded_so_far)
        return f"{html.escape(decoded_so_far[:40])} ... {html.escape(decoded_so_far[-40:])}"

    decoded_chars = []
    first_decode_rows = []
    tail_decode_rows = []
    all_decode_rows = []

    for step_no, _, _, token in compressed_data:
        distance, length, next_char = token
        matched_chars = []
        for _ in range(length):
            if distance > 0 and distance <= len(decoded_chars):
                copied_char = decoded_chars[-distance]
                decoded_chars.append(copied_char)
                matched_chars.append(copied_char)
        if next_char:
            decoded_chars.append(next_char)

        copy_action = f"Lùi {distance} ký tự, chép {length} ký tự" if length > 0 else "Không copy"
        matched_text = "".join(matched_chars) if matched_chars else "-"
        next_display = format_visible_char(next_char) if next_char else "<i>(EOF)</i>"
        row_html = (
            f"<tr><td>{step_no}</td><td><b>{token}</b></td><td>{copy_action}</td>"
            f"<td>{html.escape(matched_text)}</td><td>{next_display}</td>"
            f"<td>{compact_lz77_preview(decoded_chars)}</td></tr>"
        )

        if step_no <= 10:
            first_decode_rows.append(row_html)
        if step_no <= 20:
            all_decode_rows.append(row_html)
        tail_decode_rows.append(row_html)
        if len(tail_decode_rows) > 10:
            tail_decode_rows.pop(0)

    total_decode_rows = len(compressed_data)
    if total_decode_rows > 20:
        html_output += "".join(first_decode_rows)
        hidden_count = total_decode_rows - 20
        html_output += f"<tr class='decode-ellipsis'><td colspan='6'>... ẩn {hidden_count} dòng ở giữa ...</td></tr>"
        html_output += "".join(tail_decode_rows)
    else:
        html_output += "".join(all_decode_rows)
    html_output += "</table></div>"
    html_output += f"<div class='decoded-result'><b>Kết quả giải mã:</b> {html.escape(''.join(decoded_chars))}</div>"

    return html_output

# ==========================================
# 2. THUẬT TOÁN HUFFMAN (Có vẽ Sơ Đồ Cây)
# ==========================================
class HuffmanNode:
    _id_counter = 0  # Dùng để cấp ID độc nhất cho mỗi node vẽ sơ đồ
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
        self.id = f"node_{HuffmanNode._id_counter}"
        self.queue_order = 0
        HuffmanNode._id_counter += 1

def huffman_compress_web(text):
    if not text:
        return "<p>Vui lòng nhập văn bản!</p>"
    
    # Reset ID counter mỗi lần chạy
    HuffmanNode._id_counter = 0
        
    html_output = f"<div class='info-text'><b>Chuỗi đầu vào:</b> {text}</div>"
    frequencies = collections.Counter(text)

    html_output += "<h3>Bảng tần suất ký tự:</h3>"
    html_output += "<table class='frequency-table'>"
    html_output += "<tr><th>Ký tự</th>"
    for char in frequencies.keys():
        display_char = format_visible_char(char)
        html_output += f"<td><b>{display_char}</b></td>"
    html_output += "</tr>"
    html_output += "<tr><th>Số lần xuất hiện</th>"
    for freq in frequencies.values():
        html_output += f"<td>{freq}</td>"
    html_output += "</tr>"
    html_output += "</table>"
    show_steps = len(text) <= MAX_VISUALIZATION_CHARS
    if not show_steps:
        html_output += (
            f"<div class='length-notice'><b>Thông báo:</b> Input có {len(text)} ký tự, vượt quá "
            f"{MAX_VISUALIZATION_CHARS} ký tự. Chương trình chỉ hiển thị kết quả cuối cùng, "
            "không hiển thị quá trình xây cây từng bước.</div>"
        )

    def display_char(char):
        return format_visible_char(char)

    def node_symbols(node):
        if node.char is not None:
            return display_char(node.char)
        return node_symbols(node.left) + node_symbols(node.right)

    def ascii_key(value):
        return tuple(ord(char) for char in value)

    def sort_nodes(nodes):
        return sorted(nodes, key=lambda node: (node.freq, node.queue_order))

    def render_node_card(node, is_new=False, is_final=False):
        label = "Σ" if is_final and node.char is None else node_symbols(node)
        new_class = " is-new" if is_new else ""
        return (
            f"<div class='huff-node{new_class}'>"
            f"<div class='huff-freq'>{node.freq}</div>"
            f"<div class='huff-symbol'>{label}</div>"
            f"</div>"
        )

    def render_tree(node, new_node=None, is_final=False, show_bits=False):
        def render_tree_item(current, final_root=False, bit_label=None):
            is_new = new_node is current
            edge_label = f"<span class='edge-bit'>{bit_label}</span>" if bit_label is not None else ""
            children_html = ""
            if current.left or current.right:
                children_html = (
                    "<ul class='huff-bit-edges'>"
                    f"{render_tree_item(current.left, bit_label='0' if show_bits else None)}"
                    f"{render_tree_item(current.right, bit_label='1' if show_bits else None)}"
                    "</ul>"
                )
            return f"<li>{edge_label}{render_node_card(current, is_new, final_root)}{children_html}</li>"

        bit_class = " show-bits" if show_bits else ""
        return f"<div class='huff-tree{bit_class}'><ul>{render_tree_item(node, is_final)}</ul></div>"

    def render_snapshot(title, queue_nodes, forest_roots, new_node=None, description=""):
        snapshot_html = f"<div class='huffman-step'><div class='huffman-step-title'>{title}</div>"
        if description:
            snapshot_html += f"<div class='step-desc'>{description}</div>"

        snapshot_html += "<div class='huffman-stage'>"
        snapshot_html += "<div class='huffman-queue'>"
        for node in sort_nodes(queue_nodes):
            snapshot_html += render_node_card(node, new_node is node, len(queue_nodes) == 1 and node.char is None)
        snapshot_html += "</div>"

        snapshot_html += "<div class='huffman-forest'>"
        if forest_roots:
            for node in sort_nodes(forest_roots):
                snapshot_html += render_tree(node, new_node, len(queue_nodes) == 1 and node is forest_roots[0])
        else:
            snapshot_html += "<div class='huffman-empty'>Chưa có cây con được gộp</div>"
        snapshot_html += "</div></div></div>"
        return snapshot_html
    
    queue = [HuffmanNode(char, freq) for char, freq in frequencies.items()]
    queue = sorted(queue, key=lambda node: (node.freq, ascii_key(str(node.char))))
    next_queue_order = 0
    for node in queue:
        node.queue_order = next_queue_order
        next_queue_order += 1

    if show_steps:
        html_output += "<h3>Quá trình xây cây Huffman tuần tự:</h3>"
        html_output += "<div class='rule-box'><b>Quy tắc xây cây:</b> Hàng đợi được sắp tăng dần theo số lần xuất hiện, nếu bằng nhau thì theo mã ASCII. Mỗi lần lấy 2 node đầu hàng đợi: node lấy đầu tiên đặt bên phải, node lấy thứ hai đặt bên trái. Nếu node mới sau khi gộp có cùng tần suất với node đang đợi, ưu tiên node đang đợi trước.</div>"
        snapshots_html = render_snapshot("Bước 0: Sắp xếp các ký tự theo tần suất tăng dần, nếu bằng nhau thì theo mã ASCII", queue, [])
    step = 1
    while len(queue) > 1:
        queue = sort_nodes(queue)
        node1 = queue.pop(0)
        node2 = queue.pop(0)
        merged = HuffmanNode(None, node1.freq + node2.freq)
        merged.left, merged.right = node2, node1
        merged.queue_order = next_queue_order
        next_queue_order += 1
        queue.append(merged)
        queue = sort_nodes(queue)

        if show_steps:
            queue_now = sort_nodes(queue)
            forest_now = [node for node in queue_now if node.left or node.right]
            desc = (
                f"Lấy hai node đầu hàng đợi: <b>{node_symbols(node1)} ({node1.freq})</b> đặt bên phải, "
                f"<b>{node_symbols(node2)} ({node2.freq})</b> đặt bên trái "
                f"&rarr; <b>{node_symbols(merged)} ({merged.freq})</b>. "
                "Nếu node mới có cùng tần suất với node đang đợi, node đang đợi được ưu tiên trước."
            )
            snapshots_html += render_snapshot(f"Bước {step}: Tạo node {node_symbols(merged)}", queue_now, forest_now, merged, desc)
        step += 1

    if show_steps:
        html_output += f"<div class='huffman-process'>{snapshots_html}</div>"
    
    root = queue[0] if queue else None

    if show_steps:
        html_output += "<h3>Gán mã bit cho các cạnh của cây Huffman:</h3>"
        html_output += "<div class='huffman-step final-code-tree'>"
        html_output += "<div class='huffman-step-title'>Quy ước: nhánh trái = 0, nhánh phải = 1</div>"
        html_output += "<div class='step-desc'>Đi từ gốc đến từng ký tự lá, ghép các bit trên đường đi để thu được mã Huffman của ký tự đó.</div>"
        html_output += f"<div class='huffman-final-tree'>{render_tree(root, is_final=True, show_bits=True)}</div>"
        html_output += "</div>"
    
    # --- TẠO BẢNG MÃ BIT ---
    huffman_codes = {}
    def generate_codes(node, current_code):
        if node is None: return
        if node.char is not None:
            huffman_codes[node.char] = current_code or "0"
            return
        generate_codes(node.left, current_code + "0")
        generate_codes(node.right, current_code + "1")
        
    generate_codes(root, "")
    
    html_output += "<h3>Bảng Mã Huffman:</h3>"
    html_output += "<table class='result-table'>"
    html_output += "<tr><th>Ký tự</th><th>Tần suất</th><th>Mã Bit</th></tr>"
    for char, freq in frequencies.items():
        char_display = format_visible_char(char)
        html_output += f"<tr><td><b>{char_display}</b></td><td>{freq}</td><td><b style='color:#d93025;'>{huffman_codes[char]}</b></td></tr>"
    html_output += "</table>"
    
    encoded_text = "".join(huffman_codes[char] for char in text) if len(huffman_codes) > 1 else "0" * len(text)
    html_output += f"<h3>Kết quả sau mã hóa:</h3>"
    html_output += f"<div class='final-result'><b>{encoded_text}</b></div>"

    html_output += "<h3>Trực quan hóa quá trình giải mã Huffman:</h3>"
    decode_map = {code: char for char, code in huffman_codes.items()}
    decoded_chars = []
    current_code = ""
    html_output += "<div class='decode-box'>"
    html_output += "<div class='step-desc'>Dựa vào bảng mã Huffman: đọc dần chuỗi bit cho đến khi khớp một mã trong bảng, xuất ký tự tương ứng rồi reset mã tạm thời. Bảng dưới đây chỉ hiển thị tối đa 10 dòng đầu và 10 dòng cuối để phần decode gọn hơn.</div>"
    html_output += "<table class='decode-table'>"
    html_output += "<tr><th>Bước</th><th>Khoảng bit</th><th>Mã Huffman đọc được</th><th>Ký tự xuất ra</th><th>Chuỗi đã khôi phục</th></tr>"

    def compact_decoded_preview(chars):
        decoded_so_far = "".join(chars)
        if len(decoded_so_far) <= 90:
            return html.escape(decoded_so_far)
        return f"{html.escape(decoded_so_far[:40])} ... {html.escape(decoded_so_far[-40:])}"

    def make_decode_row(step_number, bit_range, code, char):
        return (
            f"<tr><td>{step_number}</td><td>{bit_range}</td><td><b>{code}</b></td>"
            f"<td>{display_char(char)}</td>"
            f"<td>{compact_decoded_preview(decoded_chars)}</td></tr>"
        )

    first_decode_rows = []
    tail_decode_rows = []
    all_decode_rows = []
    decode_step = 1
    code_start = 1
    for idx, bit in enumerate(encoded_text, start=1):
        current_code += bit
        matched_char = decode_map.get(current_code, "")
        if matched_char:
            decoded_chars.append(matched_char)
            bit_range = f"{code_start}" if code_start == idx else f"{code_start}-{idx}"
            row_html = make_decode_row(decode_step, bit_range, current_code, matched_char)
            if decode_step <= 10:
                first_decode_rows.append(row_html)
            if decode_step <= 20:
                all_decode_rows.append(row_html)
            tail_decode_rows.append(row_html)
            if len(tail_decode_rows) > 10:
                tail_decode_rows.pop(0)
            decode_step += 1
            code_start = idx + 1
            current_code = ""

    decoded_text = "".join(decoded_chars)
    total_decode_rows = decode_step - 1
    if total_decode_rows > 20:
        html_output += "".join(first_decode_rows)
        hidden_count = total_decode_rows - 20
        html_output += (
            f"<tr class='decode-ellipsis'><td colspan='5'>... ẩn {hidden_count} dòng ở giữa ...</td></tr>"
        )
        html_output += "".join(tail_decode_rows)
    else:
        html_output += "".join(all_decode_rows)
    html_output += "</table></div>"

    html_output += f"<div class='decoded-result'><b>Kết quả giải mã:</b> {html.escape(decoded_text)}</div>"

    fixed_code_length = max(1, math.ceil(math.log2(len(frequencies))))
    uncompressed_size = len(text) * fixed_code_length
    compressed_size = len(encoded_text)
    compression_ratio = uncompressed_size / compressed_size if compressed_size else 0
    html_output += "<h3>Tỉ lệ nén (Compression Ratio):</h3>"
    html_output += "<div class='compression-box'>"
    html_output += "<p><b>Tỉ lệ nén</b> dùng để đánh giá dữ liệu được nén nhỏ đi bao nhiêu lần so với ban đầu.</p>"
    html_output += (
        f"<p>Trong mô phỏng này, <b>Uncompressed Size</b> được tính theo mã hóa cố định "
        f"(<i>fixed-length encoding</i>): có {len(frequencies)} ký tự khác nhau nên mỗi ký tự cần "
        f"<b>⌈log<sub>2</sub>({len(frequencies)})⌉ = {fixed_code_length} bit</b>.</p>"
    )
    html_output += (
        "<div class='compression-formula'>"
        "CR = <span class='fraction'><span>Uncompressed Size</span><span>Compressed Size</span></span>"
        f" = <span class='fraction'><span>{uncompressed_size} bits</span><span>{compressed_size} bits</span></span>"
        f" = <b>{compression_ratio:.2f}</b>"
        "</div>"
    )
    html_output += "<ul class='compression-notes'>"
    html_output += "<li>Miền giá trị: <b>CR ≥ 1</b> khi dữ liệu sau nén không lớn hơn dữ liệu ban đầu.</li>"
    html_output += "<li><b>CR càng lớn</b> thì hiệu quả nén càng cao.</li>"
    html_output += "</ul>"
    html_output += (
        f"<p>Với chuỗi hiện tại, tỉ lệ nén là <b>{compression_ratio:.2f}</b>, "
        f"tức là dữ liệu ban đầu lớn gấp khoảng <b>{compression_ratio:.2f} lần</b> dữ liệu sau nén "
        f"({len(text)} ký tự × {fixed_code_length} bit = {uncompressed_size} bits, so với {compressed_size} bits sau mã hóa Huffman).</p>"
    )
    html_output += "</div>"
    
    return html_output

def xlsx_col_to_index(cell_ref):
    match = re.match(r"([A-Z]+)", cell_ref or "")
    if not match:
        return 0
    index = 0
    for char in match.group(1):
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index - 1

def read_uploaded_xlsx(raw):
    ns = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(io.BytesIO(raw)) as workbook_zip:
        shared_strings = []
        if "xl/sharedStrings.xml" in workbook_zip.namelist():
            root = ET.fromstring(workbook_zip.read("xl/sharedStrings.xml"))
            for item in root.findall("main:si", ns):
                parts = [text_node.text or "" for text_node in item.findall(".//main:t", ns)]
                shared_strings.append("".join(parts))

        workbook_root = ET.fromstring(workbook_zip.read("xl/workbook.xml"))
        first_sheet = workbook_root.find("main:sheets/main:sheet", ns)
        if first_sheet is None:
            raise ValueError("File XLSX không có sheet dữ liệu.")

        rel_id = first_sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        rels_root = ET.fromstring(workbook_zip.read("xl/_rels/workbook.xml.rels"))
        sheet_target = None
        for rel in rels_root:
            if rel.attrib.get("Id") == rel_id:
                sheet_target = rel.attrib.get("Target")
                break
        if not sheet_target:
            raise ValueError("Không tìm thấy sheet đầu tiên trong file XLSX.")

        if sheet_target.startswith("/"):
            sheet_path = sheet_target.lstrip("/")
        else:
            sheet_path = "xl/" + sheet_target
        sheet_root = ET.fromstring(workbook_zip.read(sheet_path))
        parsed_rows = []
        for row in sheet_root.findall(".//main:sheetData/main:row", ns):
            values = {}
            max_index = -1
            for cell in row.findall("main:c", ns):
                cell_ref = cell.attrib.get("r", "")
                col_index = xlsx_col_to_index(cell_ref)
                max_index = max(max_index, col_index)
                cell_type = cell.attrib.get("t")
                value_node = cell.find("main:v", ns)
                inline_node = cell.find("main:is/main:t", ns)

                if cell_type == "inlineStr":
                    value = inline_node.text if inline_node is not None and inline_node.text is not None else ""
                elif value_node is None:
                    value = ""
                elif cell_type == "s":
                    string_index = int(value_node.text)
                    value = shared_strings[string_index] if string_index < len(shared_strings) else ""
                elif cell_type == "b":
                    value = "TRUE" if value_node.text == "1" else "FALSE"
                else:
                    value = value_node.text or ""
                    if re.fullmatch(r"-?\d+\.0+", value):
                        value = value.split(".", 1)[0]

                values[col_index] = str(value)

            if max_index >= 0:
                parsed_rows.append([values.get(index, "") for index in range(max_index + 1)])

    if not parsed_rows:
        raise ValueError("Sheet đầu tiên trong XLSX đang rỗng.")

    headers = [header.strip().lower() for header in parsed_rows[0]]
    return [
        {headers[index]: row[index].strip() if index < len(row) else "" for index in range(len(headers)) if headers[index]}
        for row in parsed_rows[1:]
        if any(cell.strip() for cell in row)
    ]

def read_uploaded_table(file_storage):
    if not file_storage or not file_storage.filename:
        raise ValueError("Vui lòng chọn file XLSX để decode.")
    raw = file_storage.read()
    if not raw:
        raise ValueError("File upload đang rỗng.")
    if raw.startswith(b"PK\x03\x04"):
        return read_uploaded_xlsx(raw)
    if raw.startswith(b"\xd0\xcf\x11\xe0"):
        raise ValueError("File bạn upload là .xls cũ. Hãy lưu lại dưới dạng .xlsx.")

    decode_errors = []
    text = None
    encodings = ["utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "cp1258", "cp1252", "latin-1"]
    for encoding in encodings:
        try:
            candidate = raw.decode(encoding)
            if candidate.count("\x00") > max(1, len(candidate) // 20):
                continue
            text = candidate
            break
        except UnicodeDecodeError as exc:
            decode_errors.append(f"{encoding}: {exc}")

    if text is None:
        raise ValueError("Không đọc được file. Hãy upload file .xlsx.")

    first_line = next((line for line in text.splitlines() if line.strip()), "")
    delimiter = max([",", ";", "\t"], key=lambda item: first_line.count(item))
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)
    if reader.fieldnames:
        reader.fieldnames = [field.strip().lower() if field else field for field in reader.fieldnames]
    return list(reader)

def read_uploaded_text(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    raw = file_storage.read()
    if not raw:
        return ""
    for encoding in ("utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "cp1258", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            if text.count("\x00") > max(1, len(text) // 20):
                continue
            return text
        except UnicodeDecodeError:
            continue
    raise ValueError("Không đọc được file .txt. Hãy lưu file dưới dạng UTF-8.")

def decode_csv_char(value):
    if value is None:
        return ""
    value = value.strip()
    special_values = {
        "<space>": " ",
        "space": " ",
        "\\s": " ",
        "<empty>": "",
        "<eof>": "",
        "eof": "",
    }
    return special_values.get(value.lower(), value)

def compact_text_preview(text):
    if len(text) <= 90:
        return html.escape(text)
    return f"{html.escape(text[:40])} ... {html.escape(text[-40:])}"

def render_compact_rows(rows, column_count):
    if len(rows) > 20:
        hidden_count = len(rows) - 20
        return (
            "".join(rows[:10])
            + f"<tr class='decode-ellipsis'><td colspan='{column_count}'>... ẩn {hidden_count} dòng ở giữa ...</td></tr>"
            + "".join(rows[-10:])
        )
    return "".join(rows)

def lz77_decode_csv_web(file_storage):
    rows = read_uploaded_table(file_storage)
    required = {"distance", "length", "next"}
    if not rows or not required.issubset(rows[0].keys()):
        raise ValueError("XLSX LZ77 cần có hàng header: distance,length,next")

    html_output = "<div class='info-text'><b>Luồng decode XLSX:</b> LZ77 từ bảng token.</div>"
    html_output += "<h3>Bảng token đọc từ XLSX:</h3>"
    html_output += "<table class='result-table'><tr><th>Bước</th><th>Distance</th><th>Length</th><th>Next</th><th>Token</th></tr>"

    tokens = []
    for idx, row in enumerate(rows, start=1):
        distance = int(row.get("distance", "").strip())
        length = int(row.get("length", "").strip())
        next_char = decode_csv_char(row.get("next", ""))
        token = (distance, length, next_char)
        tokens.append(token)
        next_display = format_visible_char(next_char) if next_char else "<i>(EOF)</i>"
        html_output += f"<tr><td>{idx}</td><td>{distance}</td><td>{length}</td><td>{next_display}</td><td><b>{token}</b></td></tr>"
    html_output += "</table>"

    html_output += "<h3>Trực quan hóa quá trình giải mã LZ77:</h3>"
    html_output += "<div class='decode-box'>"
    html_output += "<div class='step-desc'>Đọc từng token từ XLSX: lùi Distance ký tự, copy Length ký tự, rồi nối thêm Next.</div>"
    html_output += "<table class='decode-table'>"
    html_output += "<tr><th>Bước</th><th>Token</th><th>Thao tác copy</th><th>Đoạn khớp khôi phục</th><th>Ký tự Next</th><th>Chuỗi đã khôi phục</th></tr>"

    decoded_chars = []
    decode_rows = []
    for idx, token in enumerate(tokens, start=1):
        distance, length, next_char = token
        matched_chars = []
        for _ in range(length):
            if distance <= 0 or distance > len(decoded_chars):
                raise ValueError(f"Token dòng {idx} không hợp lệ: Distance vượt quá chuỗi đã khôi phục.")
            copied_char = decoded_chars[-distance]
            decoded_chars.append(copied_char)
            matched_chars.append(copied_char)
        if next_char:
            decoded_chars.append(next_char)

        matched_text = "".join(matched_chars) if matched_chars else "-"
        next_display = format_visible_char(next_char) if next_char else "<i>(EOF)</i>"
        copy_action = f"Lùi {distance} ký tự, chép {length} ký tự" if length else "Không copy"
        decode_rows.append(
            f"<tr><td>{idx}</td><td><b>{token}</b></td><td>{copy_action}</td>"
            f"<td>{html.escape(matched_text)}</td><td>{next_display}</td>"
            f"<td>{compact_text_preview(''.join(decoded_chars))}</td></tr>"
        )

    html_output += render_compact_rows(decode_rows, 6)
    html_output += "</table></div>"
    html_output += f"<div class='decoded-result'><b>Kết quả giải mã:</b> {html.escape(''.join(decoded_chars))}</div>"
    return html_output

def huffman_decode_csv_web(file_storage):
    rows = read_uploaded_table(file_storage)
    if not rows or not {"encoded_bits", "char", "code"}.issubset(rows[0].keys()):
        raise ValueError("XLSX Huffman cần có hàng header: encoded_bits,char,code")

    encoded_bits = ""
    decode_map = {}
    for row in rows:
        bits = (row.get("encoded_bits") or "").strip()
        if bits:
            encoded_bits = bits
        char_value = row.get("char")
        code = (row.get("code") or "").strip()
        if code:
            decode_map[code] = decode_csv_char(char_value)

    if not encoded_bits:
        raise ValueError("XLSX Huffman cần có một dòng chứa encoded_bits.")
    if not decode_map:
        raise ValueError("XLSX Huffman cần có các dòng char/code để tạo bảng mã.")

    html_output = "<div class='info-text'><b>Luồng decode XLSX:</b> Huffman từ chuỗi bit và bảng mã.</div>"
    html_output += "<h3>Chuỗi bit cần giải mã:</h3>"
    html_output += f"<div class='final-result'><b>{html.escape(encoded_bits)}</b></div>"
    html_output += "<h3>Bảng mã Huffman đọc từ XLSX:</h3>"
    html_output += "<table class='result-table'><tr><th>Ký tự</th><th>Mã Bit</th></tr>"
    for code, char in sorted(decode_map.items(), key=lambda item: (len(item[0]), item[0])):
        display = format_visible_char(char)
        html_output += f"<tr><td><b>{display}</b></td><td><b style='color:#d93025;'>{html.escape(code)}</b></td></tr>"
    html_output += "</table>"

    html_output += "<h3>Trực quan hóa quá trình giải mã Huffman:</h3>"
    html_output += "<div class='decode-box'>"
    html_output += "<div class='step-desc'>Đọc dần chuỗi bit. Khi mã tạm thời khớp một mã trong bảng XLSX, xuất ký tự tương ứng rồi reset mã tạm thời.</div>"
    html_output += "<table class='decode-table'>"
    html_output += "<tr><th>Bước</th><th>Khoảng bit</th><th>Mã Huffman đọc được</th><th>Ký tự xuất ra</th><th>Chuỗi đã khôi phục</th></tr>"

    decoded_chars = []
    current_code = ""
    code_start = 1
    step = 1
    decode_rows = []
    for idx, bit in enumerate(encoded_bits, start=1):
        current_code += bit
        matched_char = decode_map.get(current_code)
        if matched_char is not None:
            decoded_chars.append(matched_char)
            bit_range = f"{code_start}" if code_start == idx else f"{code_start}-{idx}"
            display = format_visible_char(matched_char)
            decode_rows.append(
                f"<tr><td>{step}</td><td>{bit_range}</td><td><b>{html.escape(current_code)}</b></td>"
                f"<td>{display}</td><td>{compact_text_preview(''.join(decoded_chars))}</td></tr>"
            )
            step += 1
            code_start = idx + 1
            current_code = ""

    if current_code:
        raise ValueError(f"Chuỗi bit kết thúc với mã chưa khớp: {current_code}")

    html_output += render_compact_rows(decode_rows, 5)
    html_output += "</table></div>"
    html_output += f"<div class='decoded-result'><b>Kết quả giải mã:</b> {html.escape(''.join(decoded_chars))}</div>"
    return html_output

# ==========================================
# 3. GIAO DIỆN HTML + CSS NÂNG CAO
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Mô Phỏng Nén Dữ Liệu</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({ startOnLoad: true, theme: 'default' });
    </script>
    
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; }
        .container { width: min(100%, 1800px); margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); box-sizing: border-box; }
        h2 { text-align: center; color: #2c3e50; }
        h3 { color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; margin-top: 30px; }
        
        .form-group { margin-bottom: 15px; }
        label { font-weight: bold; display: block; margin-bottom: 5px; }
        input[type="number"], input[type="file"], select, textarea { width: 100%; padding: 12px; border: 1px solid #bdc3c7; border-radius: 4px; box-sizing: border-box; font-size: 16px; }
        textarea { min-height: 46px; max-height: 360px; resize: vertical; line-height: 1.45; overflow-y: auto; font-family: inherit; }
        .input-hint { margin-top: 6px; font-size: 13px; color: #64748b; line-height: 1.4; }
        .char-counter { margin-top: 6px; text-align: right; font-size: 13px; color: #5f6c7b; }
        .char-counter.over-limit { color: #c0392b; font-weight: 700; }
        .csv-guide { background: #f8fbfd; border: 1px solid #dfe9f3; border-radius: 6px; padding: 12px 15px; margin-top: 10px; font-size: 14px; line-height: 1.55; }
        .csv-guide code { background: #eef3f7; padding: 2px 4px; border-radius: 3px; }
        button { background-color: #2980b9; color: white; border: none; padding: 12px 20px; border-radius: 4px; cursor: pointer; font-size: 16px; width: 100%; font-weight: bold; margin-top: 10px;}
        button:hover { background-color: #2471a3; }
        
        .settings-row { display: flex; gap: 15px; margin-top: 10px; background: #fdfefe; padding: 15px; border: 1px dashed #bdc3c7; border-radius: 5px;}
        .settings-col { flex: 1; }
        
        .result-box { margin-top: 25px; }
        .info-text { background: #e8f4f8; padding: 10px 15px; border-left: 4px solid #3498db; border-radius: 4px; font-size: 15px; }
        .length-notice { background: #fff8e1; border-left: 4px solid #f39c12; color: #5f4200; padding: 12px 15px; border-radius: 4px; margin-top: 14px; line-height: 1.5; }
        .rule-box { background: #f7fbff; border-left: 4px solid #2980b9; color: #2c3e50; padding: 12px 15px; border-radius: 4px; margin: 12px 0 16px; line-height: 1.5; }
        
        .step-container { margin-bottom: 20px; background: #fff; border: 1px solid #ecf0f1; padding: 15px; border-radius: 6px; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
        .tape { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; margin-bottom: 10px; }
        .char { display: inline-flex; justify-content: center; align-items: center; width: 30px; height: 35px; font-weight: bold; font-family: monospace; font-size: 16px; border: 1px solid #bdc3c7; border-radius: 3px; }
        
        .processed { background-color: #ecf0f1; color: #7f8c8d; border-color: #d5dbdb; }
        .search-win { background-color: #d6eaf8; color: #21618c; border-color: #85c1e9; } 
        .lookahead-win { background-color: #d5f5e3; color: #1e8449; border-color: #82e0aa; } 
        .unprocessed { background-color: white; color: #333; }
        .matched { background-color: #f9e79f; border-color: #f1c40f; color: #b7950b; box-shadow: inset 0 0 5px rgba(0,0,0,0.1); }
        .next-char { background-color: #fadbd8; border-color: #e74c3c; color: #922b21; }
        .skipped { width: 42px; background-color: #f7f9fa; color: #95a5a6; border-style: dashed; font-weight: 700; }
        
        .step-desc { font-size: 14px; color: #555; }
        .step-token-table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }
        .step-token-table th, .step-token-table td { border: 1px solid #ddd; padding: 7px 8px; text-align: center; }
        .step-token-table th { background-color: #edf3f8; color: #2c3e50; font-weight: 700; }
        .step-token-table td:last-child { font-family: monospace; }
        .decode-box { background: #fff; border: 1px solid #ecf0f1; border-radius: 6px; padding: 14px; overflow-x: auto; }
        .decode-table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }
        .decode-table th, .decode-table td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        .decode-table th { background-color: #2c3e50; color: white; }
        .decode-table td:last-child { text-align: left; font-family: monospace; word-break: break-all; }
        .decode-table .decode-ellipsis td { text-align: center; color: #7f8c8d; font-style: italic; background: #f8f9fa; font-family: inherit; }
        .decoded-result { margin-top: 12px; background: #eafaf1; border-left: 4px solid #27ae60; color: #145a32; padding: 12px 15px; border-radius: 4px; word-break: break-word; }
        .result-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .result-table th, .result-table td { border: 1px solid #ddd; padding: 10px; text-align: center; }
        .result-table th { background-color: #2c3e50; color: white; }
        .result-table tr:nth-child(even) { background-color: #f9f9f9; }
        .frequency-table { width: auto; max-width: 100%; border-collapse: collapse; margin-top: 15px; display: block; overflow-x: auto; white-space: nowrap; }
        .frequency-table th, .frequency-table td { border-bottom: 1px solid #555; padding: 8px 14px; text-align: center; font-size: 18px; }
        .frequency-table th { border-right: 1px solid #555; text-align: left; font-weight: 500; background: white; color: #111; }
        .frequency-table td { min-width: 28px; font-style: italic; }
        
        .tree-log li { margin-bottom: 8px; font-family: monospace; font-size: 14px; }
        .mermaid-container { background: white; padding: 20px; border: 1px solid #ddd; border-radius: 5px; text-align: center; overflow-x: auto;}
        .huffman-process { display: flex; flex-direction: column; gap: 22px; }
        .huffman-step { background: #fff; border: 1px solid #ecf0f1; border-radius: 6px; padding: 16px; overflow-x: auto; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
        .huffman-step-title { font-weight: 700; color: #2c3e50; margin-bottom: 8px; }
        .huffman-stage { display: grid; grid-template-columns: 180px max-content; column-gap: 110px; align-items: center; min-height: 260px; width: max-content; min-width: 100%; }
        .huffman-queue { display: flex; flex-direction: column; gap: 16px; align-items: center; align-self: start; padding: 10px 24px 0 0; border-right: 2px solid #ecf0f1; min-width: 180px; }
        .huffman-forest { display: flex; gap: 78px; align-items: flex-start; justify-content: flex-start; min-width: 620px; padding: 32px 60px 10px 36px; }
        .huffman-empty { color: #7f8c8d; font-style: italic; align-self: center; }
        .huff-tree { display: inline-block; text-align: center; }
        .huff-tree ul { position: relative; display: flex; justify-content: center; margin: 0; padding: 36px 0 0; }
        .huff-tree > ul { padding-top: 0; }
        .huff-tree li { position: relative; display: flex; flex-direction: column; align-items: center; list-style-type: none; padding: 36px 18px 0; }
        .huff-tree li::before, .huff-tree li::after { content: ""; position: absolute; top: 0; width: 50%; height: 36px; border-top: 2px solid #111; }
        .huff-tree li::before { right: 50%; border-right: 2px solid #111; }
        .huff-tree li::after { left: 50%; border-left: 2px solid #111; }
        .huff-tree li:only-child { padding-top: 0; }
        .huff-tree li:only-child::before, .huff-tree li:only-child::after { display: none; }
        .huff-tree li:first-child::before, .huff-tree li:last-child::after { border: none; }
        .huff-tree li:last-child::before { border-radius: 0 6px 0 0; }
        .huff-tree li:first-child::after { border-radius: 6px 0 0 0; }
        .huff-tree ul ul::before { content: ""; position: absolute; top: 0; left: 50%; width: 0; height: 36px; border-left: 2px solid #111; }
        .edge-bit { display: none; }
        .huff-tree.show-bits .edge-bit { display: inline-flex; position: absolute; top: 17px; left: 50%; z-index: 3; align-items: center; justify-content: center; width: 24px; height: 22px; transform: translate(-50%, -50%); background: #fff; border: 1px solid #2c3e50; border-radius: 999px; color: #d93025; font-weight: 700; font-size: 14px; line-height: 1; }
        .huffman-final-tree { min-width: 620px; overflow-x: auto; padding: 28px 20px 10px; text-align: center; }
        .final-code-tree { overflow-x: auto; }
        .huff-node { width: 92px; min-height: 58px; border: 2px solid #111; background: #fff; display: grid; grid-template-rows: 30px 1fr; text-align: center; font-family: Arial, sans-serif; flex: 0 0 auto; position: relative; z-index: 1; }
        .huff-node.is-new { box-shadow: 0 0 0 4px rgba(241, 196, 15, 0.24); border-color: #b7950b; }
        .huff-freq { background: #fff2cc; border-bottom: 2px solid #111; display: flex; align-items: center; justify-content: center; font-size: 24px; line-height: 1; }
        .huff-symbol { display: flex; align-items: center; justify-content: center; min-height: 28px; padding: 2px 4px; font-size: 23px; line-height: 1.1; word-break: break-word; }
        .final-result { font-family: monospace; font-size: 18px; word-break: break-all; background: #2c3e50; color: #2ecc71; padding: 15px; border-radius: 5px; text-align: center; letter-spacing: 2px;}
        .compression-box { background: #fff; border: 1px solid #ecf0f1; border-left: 4px solid #3f37b3; border-radius: 6px; padding: 16px 18px; font-size: 16px; line-height: 1.6; }
        .compression-box p { margin: 0 0 12px; }
        .compression-formula { display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap; margin: 14px 0; font-family: "Courier New", monospace; font-size: 18px; }
        .fraction { display: inline-grid; grid-template-rows: auto auto; text-align: center; line-height: 1.2; vertical-align: middle; }
        .fraction span:first-child { border-bottom: 1px solid #111; padding: 0 8px 3px; }
        .fraction span:last-child { padding: 3px 8px 0; }
        .compression-notes { margin: 10px 0 14px 22px; padding: 0; }
        .compression-notes li { margin-bottom: 4px; }
        
        .legend { display: flex; gap: 15px; font-size: 13px; margin-top: 10px; margin-bottom: 20px; justify-content: center; flex-wrap: wrap;}
        .legend-item { display: flex; align-items: center; gap: 5px; }
        .box { width: 15px; height: 15px; border: 1px solid #ccc; border-radius: 2px; }
        @media (max-width: 760px) {
            body { padding: 10px; }
            .container { padding: 18px; }
            .huffman-stage { grid-template-columns: 150px max-content; column-gap: 60px; }
            .huffman-queue { min-width: 150px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Mô Phỏng Nén Dữ Liệu Nâng Cao</h2>
        <form method="POST" enctype="multipart/form-data">
            <div class="form-group">
                <label>Chọn luồng xử lý:</label>
                <select name="mode" id="mode-select" onchange="toggleMode()">
                    <option value="visualize" {% if request.form.get('mode', 'visualize') == 'visualize' %}selected{% endif %}>Mô phỏng encode + decode từng bước</option>
                    <option value="decode_csv" {% if request.form.get('mode') == 'decode_csv' %}selected{% endif %}>Decode từ file XLSX</option>
                </select>
            </div>

            <div id="visualize-inputs">
            <div class="form-group">
                <label>Nhập văn bản cần nén:</label>
                <textarea name="text_input" id="text-input" rows="1" placeholder="VD: ABABABABA">{{ request.form.get('text_input', '') }}</textarea>
                <div id="char-counter" class="char-counter">0 / 500 ký tự</div>
                <div class="input-hint">Có thể nhập trực tiếp hoặc upload file .txt bên dưới. Nếu chọn file, nội dung file sẽ được ưu tiên.</div>
                <input type="file" name="text_file" id="text-file" accept=".txt,text/plain">
            </div>
            </div>
            
            <div class="form-group">
                <label>Chọn thuật toán:</label>
                <select name="algorithm" id="algo-select" onchange="toggleSettings()">
                    <option value="lz77" {% if request.form.get('algorithm') == 'lz77' %}selected{% endif %}>Thuật toán LZ77 (Sliding Window)</option>
                    <option value="huffman" {% if request.form.get('algorithm') == 'huffman' %}selected{% endif %}>Mã hóa Huffman Coding</option>
                </select>
            </div>
            
            <div id="lz77-settings" class="settings-row" style="display: none;">
                <div class="settings-col">
                    <label>Search Window (Mặc định: 13):</label>
                    <input type="number" name="sw_size" min="1" value="{{ request.form.get('sw_size', '') }}" placeholder="Để trống = mặc định (13)">
                </div>
                <div class="settings-col">
                    <label>Lookahead Window (Mặc định: 6):</label>
                    <input type="number" name="lw_size" min="1" value="{{ request.form.get('lw_size', '') }}" placeholder="Để trống = mặc định (6)">
                </div>
            </div>

            <div id="decode-csv-inputs" style="display: none;">
                <div class="form-group">
                    <label>Upload file XLSX để decode:</label>
                    <input type="file" name="csv_file" id="csv-file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
                    <div class="csv-guide" id="lz77-csv-guide">
                        <b>Định dạng XLSX cho LZ77:</b> sheet đầu tiên cần có hàng header <code>distance</code>, <code>length</code>, <code>next</code>.<br>
                        Ví dụ các cột:<br>
                        <code>distance | length | next</code><br>
                        <code>0 | 0 | A</code><br>
                        <code>3 | 2 | B</code><br>
                        Dùng <code>&lt;space&gt;</code> cho dấu cách, để trống hoặc <code>&lt;EOF&gt;</code> nếu không có ký tự Next.
                    </div>
                    <div class="csv-guide" id="huffman-csv-guide">
                        <b>Định dạng XLSX cho Huffman:</b> sheet đầu tiên cần có hàng header <code>encoded_bits</code>, <code>char</code>, <code>code</code>.<br>
                        Ví dụ các cột:<br>
                        <code>encoded_bits | char | code</code><br>
                        <code>010110 |  | </code><br>
                        <code> | A | 0</code><br>
                        <code> | B | 10</code><br>
                        Dùng <code>&lt;space&gt;</code> cho dấu cách trong cột <code>char</code>.
                    </div>
                </div>
            </div>

            <button type="submit">Chạy Mô Phỏng</button>
        </form>

        {% if result_html %}
        <div class="result-box">
            {% if request.form.get('algorithm') == 'lz77' %}
            <div class="legend">
                <div class="legend-item"><div class="box" style="background:#ecf0f1;"></div> Đã xử lý (Trôi qua)</div>
                <div class="legend-item"><div class="box" style="background:#d6eaf8;"></div> Search Window</div>
                <div class="legend-item"><div class="box" style="background:#d5f5e3;"></div> Lookahead</div>
                <div class="legend-item"><div class="box" style="background:#f9e79f;"></div> Ký tự khớp</div>
                <div class="legend-item"><div class="box" style="background:#fadbd8;"></div> Ký tự tiếp theo</div>
            </div>
            {% endif %}
            
            {{ result_html | safe }}
        </div>
        {% endif %}
    </div>
    
    <script>
        function toggleSettings() {
            var algo = document.getElementById("algo-select").value;
            var lz77_settings = document.getElementById("lz77-settings");
            var mode = document.getElementById("mode-select").value;
            var lz77Guide = document.getElementById("lz77-csv-guide");
            var huffmanGuide = document.getElementById("huffman-csv-guide");
            if (algo === "lz77" && mode === "visualize") {
                lz77_settings.style.display = "flex";
            } else {
                lz77_settings.style.display = "none";
            }
            if (lz77Guide && huffmanGuide) {
                lz77Guide.style.display = algo === "lz77" ? "block" : "none";
                huffmanGuide.style.display = algo === "huffman" ? "block" : "none";
            }
        }
        function toggleMode() {
            var mode = document.getElementById("mode-select").value;
            var visualizeInputs = document.getElementById("visualize-inputs");
            var decodeCsvInputs = document.getElementById("decode-csv-inputs");
            var textInput = document.getElementById("text-input");
            var csvFile = document.getElementById("csv-file");
            visualizeInputs.style.display = mode === "visualize" ? "block" : "none";
            decodeCsvInputs.style.display = mode === "decode_csv" ? "block" : "none";
            textInput.required = false;
            csvFile.required = mode === "decode_csv";
            toggleSettings();
        }
        function autoResizeTextInput() {
            var input = document.getElementById("text-input");
            if (!input) return;
            var lineHeight = parseFloat(window.getComputedStyle(input).lineHeight);
            var maxHeight = (lineHeight * 15) + 24;
            input.style.height = "auto";
            input.style.height = Math.min(input.scrollHeight, maxHeight) + "px";
        }
        function updateCharCounter() {
            var input = document.getElementById("text-input");
            var counter = document.getElementById("char-counter");
            if (!input || !counter) return;
            var length = input.value.length;
            counter.textContent = length + " / 500 ký tự";
            counter.classList.toggle("over-limit", length > 500);
        }
        function handleTextInputChange() {
            autoResizeTextInput();
            updateCharCounter();
        }
        document.getElementById("text-input").addEventListener("input", handleTextInputChange);
        // Chạy lần đầu khi load trang
        window.onload = function() {
            toggleMode();
            toggleSettings();
            handleTextInputChange();
        };
    </script>
</body>
</html>
"""

# ==========================================
# 4. XỬ LÝ ROUTING BẰNG FLASK
# ==========================================
@app.route("/", methods=["GET", "POST"])
def index():
    result_html = None
    if request.method == "POST":
        mode = request.form.get("mode", "visualize")
        text_input = request.form.get("text_input", "")
        algorithm = request.form.get("algorithm")

        if mode == "decode_csv":
            try:
                if algorithm == "lz77":
                    result_html = lz77_decode_csv_web(request.files.get("csv_file"))
                elif algorithm == "huffman":
                    result_html = huffman_decode_csv_web(request.files.get("csv_file"))
            except Exception as exc:
                result_html = f"<div class='length-notice'><b>Lỗi đọc XLSX:</b> {html.escape(str(exc))}</div>"

        else:
            try:
                uploaded_text = read_uploaded_text(request.files.get("text_file"))
                if uploaded_text is not None:
                    text_input = uploaded_text
            except Exception as exc:
                result_html = f"<div class='length-notice'><b>Lỗi đọc TXT:</b> {html.escape(str(exc))}</div>"
                return render_template_string(HTML_TEMPLATE, result_html=result_html)
            if not text_input:
                result_html = "<div class='length-notice'><b>Thiếu input:</b> Vui lòng nhập văn bản hoặc upload file .txt.</div>"
                return render_template_string(HTML_TEMPLATE, result_html=result_html)

        if mode != "decode_csv" and algorithm == "lz77":
            # Xử lý lấy thông số window, nếu rỗng thì lấy mặc định
            sw_input = request.form.get("sw_size")
            lw_input = request.form.get("lw_size")
            
            sw = int(sw_input) if sw_input and sw_input.isdigit() else 13
            lw = int(lw_input) if lw_input and lw_input.isdigit() else 6
            
            result_html = lz77_compress_web(text_input, sw, lw)
            
        elif mode != "decode_csv" and algorithm == "huffman":
            result_html = huffman_compress_web(text_input)
            
    return render_template_string(HTML_TEMPLATE, result_html=result_html)

if __name__ == "__main__":
    app.run(debug=True)
