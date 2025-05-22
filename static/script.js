// filepath: InvoiceNER/static/script.js
console.log('Đã load script.js');
const LABELS = [
    "Ngày chứng từ", "Số hóa đơn", "Mẫu số hóa đơn", "Ký hiệu hóa đơn", "Thuế suất chung", "Tiền thuế GTGT", "Tổng tiền chưa thuế GTGT", "Tổng tiền chiết khấu thương mại", "Tổng giảm trừ khác", "Tổng tiền thanh toán",
    "Bên mua", "Bên mua - Tên đơn vị", "Bên mua - Mã số thuế", "Bên mua - Địa chỉ", "Bên mua - Số tài khoản",
    "Bên bán", "Bên bán - Tên đơn vị", "Bên bán - Mã số thuế", "Bên bán - Địa chỉ", "Bên bán - Số điện thoại", "Bên bán - Số tài khoản", "Bên bán - Email",
    "Diễn giải",
    "Đơn hàng"
];

document.getElementById('pdf_file').addEventListener('change', function(e) {
    const file = e.target.files[0];
    const preview = document.getElementById('pdf-preview');
    preview.innerHTML = '';
    if (file) {
        preview.textContent = `Bạn đã chọn file: ${file.name}`;
        const reader = new FileReader();
        reader.onload = function(ev) {
            const typedarray = new Uint8Array(ev.target.result);
            pdfjsLib.getDocument({data: typedarray}).promise.then(function(pdf) {
                pdf.getPage(1).then(function(page) {
                    const viewport = page.getViewport({scale: 1.2});
                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;
                    preview.innerHTML = '';
                    preview.appendChild(canvas);
                    page.render({canvasContext: context, viewport: viewport});
                });
            }).catch(function(err) {
                preview.textContent = 'Không thể xem trước PDF.';
            });
        };
        reader.readAsArrayBuffer(file);
    } else {
        preview.textContent = '';
    }
});

const form = document.getElementById('upload-form');
form.addEventListener('submit', function(e) {
    e.preventDefault();
    const fileInput = document.getElementById('pdf_file');
    if (!fileInput.files[0]) return;
    const formData = new FormData();
    formData.append('pdf_file', fileInput.files[0]);
    fetch('/', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        console.log('Kết quả trả về:', data);
        if (data.error) {
            alert('Lỗi: ' + data.error);
            return;
        }
        document.getElementById('ocr-content').textContent = data.complete_text || '';
        document.getElementById('ocr-text').style.display = 'block';
        renderResult(data.json_result || {});
    })
    .catch(err => {
        alert('Lỗi gửi file hoặc server!');
    });
});

function flattenResultJson(json) {
    const flat = {...json};
    if (typeof flat["Bên mua"] === "object" && flat["Bên mua"] !== null) {
        Object.entries(flat["Bên mua"]).forEach(([k, v]) => {
            flat[k] = v;
        });
        delete flat["Bên mua"];
    }
    if (typeof flat["Bên bán"] === "object" && flat["Bên bán"] !== null) {
        Object.entries(flat["Bên bán"]).forEach(([k, v]) => {
            flat[k] = v;
        });
        delete flat["Bên bán"];
    }
    return flat;
}

function renderResult(json) {
    console.log('JSON nhận được:', json);
    const resultDiv = document.getElementById('result-fields');
    resultDiv.innerHTML = '';
    const flatJson = flattenResultJson(json);
    LABELS.forEach(label => {
        if (label === 'Đơn hàng') {
            const items = json['Đơn hàng'] || [];
            const html = Array.isArray(items) && items.length > 0 ?
                items.map((item, idx) => renderOrderItem(item, idx+1)).join('') : '<div class="result-value">(Không có)</div>';
            resultDiv.innerHTML += `<div class="result-label">Đơn hàng</div>${html}`;
        } else if (label === 'Ngày chứng từ') {
            let val = flatJson[label];
            if (val && typeof val === 'object' && val['Ngày chứng từ - Ngày'] && val['Ngày chứng từ - Tháng'] && val['Ngày chứng từ - Năm']) {
                val = `${val['Ngày chứng từ - Ngày']}-${parseInt(val['Ngày chứng từ - Tháng'], 10)}-${val['Ngày chứng từ - Năm']}`;
            } else if (val === null || val === undefined) {
                val = '';
            }
            resultDiv.innerHTML += `<div class="result-label">${label}</div><div class="result-value">${val}</div>`;
        } else {
            let val = flatJson[label];
            if (val === null || val === undefined) val = '';
            resultDiv.innerHTML += `<div class="result-label">${label}</div><div class="result-value">${val}</div>`;
        }
    });
}

function renderOrderItem(item, idx) {
    const subLabels = [
        "Đơn hàng - Mã hàng", "Đơn hàng - Tên hàng", "Đơn hàng - Đơn vị tính (ĐVT)", "Đơn hàng - Số lượng", "Đơn hàng - Đơn giá", "Đơn hàng - Chiết khấu", "Đơn hàng - Thuế suất", "Đơn hàng - Hợp đồng bán", "Đơn hàng - Số khế ước", "Đơn hàng - Thành tiền chưa thuế GTGT"
    ];
    let html = `<table class="order-table"><caption>Mặt hàng #${idx}</caption><tbody>`;
    subLabels.forEach(sub => {
        let val = item && item[sub] ? item[sub] : '';
        html += `<tr><td class="order-label">${sub}</td><td>${val}</td></tr>`;
    });
    html += '</tbody></table>';
    return html;
}