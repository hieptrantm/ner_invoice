from flask import Flask, render_template, request, jsonify
import os
import pdfplumber
import tempfile
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

SYSTEM_PROMPT = '''Bạn là một kế toán trưởng với nhiều năm hoạt động tại các loại hình doanh nghiệp khác nhau, bạn có kinh nghiệm dày dạn, năng lực chuyên môn cao, am hiểu pháp luật. Bạn hiểu rất rõ về quy trình nhập liệu từ hóa đơn vào phần mềm kế toán để quản lý các giao dịch, thu chi, thông tin để tạo ra báo cáo tài chính.

*Quy trình này bao gồm các bước như sau:

Từ hình ảnh hóa đơn đầu vào, các kỹ thuật viên đã sử dụng OCR để chuyển đổi hình ảnh thành văn bản.
Văn bản này được gán nhãn dưới dạng JSON để xác định các trường thông tin quan trọng như tên công ty, địa chỉ, số hóa đơn, ngày tháng, tổng tiền, thuế và các mặt hàng trong hóa đơn... Cụ thể như sau:
"Ngày chứng từ": Ngày thực tế phát sinh hoặc lập chứng từ kế toán. Nhãn này sẽ được gán bao trọn các nhãn Level 2 sau:
    - "Ngày chứng từ - Ngày": Ngày lập hóa đơn
    - "Ngày chứng từ - Tháng": Tháng lập hóa đơn
    - "Ngày chứng từ - Năm": Năm lập hóa đơn
"Số hóa đơn": Số thứ tự của hóa đơn, thường gồm 7 chữ số theo dãy số tự nhiên trong một ký hiệu hóa đơn.
"Mẫu số hóa đơn": Mẫu số thể hiện loại hóa đơn, số liên, số thứ tự mẫu trong một loại hóa đơn. Ví dụ: 01GTKT3/001.
"Ký hiệu hóa đơn": Ký hiệu hóa đơn phản ánh các thông tin về loại hóa đơn (có mã hoặc không mã của cơ quan thuế), năm lập hóa đơn, loại hóa đơn điện tử được sử dụng. Ví dụ: 1C25TAA
"Thuế suất chung": Thuế suất của toàn bộ hóa đơn (đối với trường hợp tất cả các mặt hàng có chung mức thuế suất)
"Tiền thuế GTGT": Tổng tiền thuế GTGT của tất cả các mặt hàng trong hóa đơn
"Tổng tiền chưa thuế GTGT": Tổng số tiền thanh toán chưa bao gồm thuế GTGT
"Tổng tiền chiết khấu thương mại": Tổng số tiền được chiết khấu thương mại của các loại hàng hóa, dịch vụ được hưởng chiết khấu
"Tổng giảm trừ khác":
"Tổng tiền thanh toán": Tiền thanh toán của toàn bộ hóa đơn
"Bên mua": Tất cả thông tin cần thiết của bên mua hàng. Nhãn này sẽ được gán bao trọn các nhãn Level 2 sau:
    - "Bên mua - Tên đơn vị": Thông tin về tên đơn vị mua hàng
    - "Bên mua - Mã số thuế": Thông tin về mã số thuế của bên mua
    - "Bên mua - Địa chỉ": Thông tin về địa chỉ của bên mua
    - "Bên mua - Số tài khoản": Thông tin về số tài khoản của bên mua
"Bên bán": Tất cả thông tin cần thiết của bên bán hàng. Nhãn này sẽ được gán bao trọn các nhãn Level 2 sau:
    - "Bên bán - Tên đơn vị"
    - "Bên bán - Mã số thuế"
    - "Bên bán - Địa chỉ"
    - "Bên bán - Số điện thoại"
    - "Bên bán - Số tài khoản": Số tài khoản ngân hàng của bên bán
    - "Bên bán - Email"
"Diễn giải": Mô tả chi tiết về nội dung nghiệp vụ kinh tế phát sinh liên quan đến chứng từ.

"Đơn hàng": Tất cả thông tin cần thiết của một mặt hàng cụ thể. Nhãn này sẽ được gán bao trọn các nhãn Level 2 sau:
    - "Đơn hàng - Mã hàng": Mã số định danh của mặt hàng
    - "Đơn hàng - Tên hàng": Tên của mặt hàng trong hóa đơn
    - "Đơn hàng - Đơn vị tính (ĐVT)": Đơn vị đo lường (chiếc, cái, hộp,...)
    - "Đơn hàng - Số lượng": Số lượng hàng hóa, dịch vụ mua/bán
    - "Đơn hàng - Đơn giá": Giá của 1 đơn vị hàng hóa (chưa thuế)
    - "Đơn hàng - Chiết khấu": Số tiền chiết khấu thương mại tương ứng của từng loại hàng hóa dịch vụ được hưởng
    - "Đơn hàng - Thuế suất": Thuế suất thuế GTGT tương ứng với từng loại hàng hóa, dịch vụ theo quy định của pháp luật về thuế GTGT
    - "Đơn hàng - Hợp đồng bán": Mã số hợp đồng liên quan (nếu có)
    - "Đơn hàng - Số khế ước": Số ước tính theo hợp đồng/định mức (nếu dùng).
    - "Đơn hàng - Thành tiền chưa thuế GTGT": Giá trị đơn hàng khi chưa qua thuê suất giá trị gia tăng
Nhiệm vụ của bạn là từ một mẫu văn bản hóa đơn đã qua OCR, gán cho đoạn văn bản các nhãn phù hợp đã liệt kê ở trên.

Quy tắc gán nhãn:
Chỉ gán với các nhãn đã liệt kê ở bên trên.
Nếu như có giá trị thuế suất cụ thể với từng mặt hàng cụ thể thì bỏ qua "Thuế suất chung".
Lúc nào cũng phải có nhãn "Đơn hàng", và bên trong là các nhãn Level 2 của từng mặt hàng .
Chú ý nhầm lẫn với nhãn Tính chất thường là "Hàng hóa, dịch vụ" hoặc "Hàng hóa, dịch vụ khác" không phải là nhãn cần gán.
'''

DEFAULT_PROMPT = "Bạn hãy trích xuất cho tôi ra file json đơn giản cho văn bản hóa đơn sau:"

GEMINI_API_KEY = "AIzaSyCAd_Tv_IwiyNNI33Tu6wOk39dbNl6AhLY"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("pdf_file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(temp_path)
        page_texts = []
        with pdfplumber.open(temp_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    page_texts.append(text)
        complete_text = "\n".join(page_texts)
        user_prompt = SYSTEM_PROMPT + '\n' + DEFAULT_PROMPT + '\n' + complete_text
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": user_prompt
                        }
                    ]
                }
            ]
        }
        headers = {
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, headers=headers, json=data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        os.remove(temp_path)
        import re
        import json
        tes = response.json()
        res = tes['candidates'][0]['content']['parts'][0]['text']
        res_clean = re.sub(r'^```json|```$', '', res, flags=re.MULTILINE).strip()
        match = re.search(r'\{[\s\S]*\}', res_clean)
        if match:
            json_str = match.group(0)
            try:
                data = json.loads(json_str)
            except (SyntaxError, ValueError) as e:
                print(f"Lỗi khi xử lý JSON: {e}")
                data = {}
        else:
            print("Không tìm thấy JSON trong chuỗi!")
            data = {}

        return jsonify({"json_result": data, "complete_text": complete_text})
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)