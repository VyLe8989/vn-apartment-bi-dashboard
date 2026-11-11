# VN Apartment Intelligence — BI & DSS

Dashboard Streamlit tông đỏ, 7 trang theo Chương 7; số liệu truy vấn trực tiếp từ các view `dw` của Supabase PostgreSQL, **không có dữ liệu giả**.

## Cài đặt (Windows PowerShell)

1. Giải nén ZIP, mở terminal trong thư mục `apartment_dashboard` chứa `app.py`.
2. `python -m pip install -r requirements.txt`
3. Sao chép `.streamlit/secrets.toml.example` thành `.streamlit/secrets.toml`.
4. Dán URI PostgreSQL **chỉ đọc** của dự án vào `DATABASE_URL` (ưu tiên Supabase Session pooler). Nếu mật khẩu có ký tự đặc biệt phải URL-encode.
5. `python -m streamlit run app.py`

Có thể chạy `start_dashboard.bat` sau khi hoàn tất cấu hình.

## Cấu trúc phân tích

- **Tổng quan**: lọc năm 2022–2026 và nguồn; KPI trong kỳ và KPI chuẩn 12 tháng gần nhất; xu hướng; số tin và giá/m² theo **vùng và tỉnh/thành**; bản đồ dự án có tên khi rê chuột.
- **Địa lý**: so sánh vùng/tỉnh, drill-down tỉnh/khu vực cũ/quận huyện, treemap, bong bóng, bảng OLAP.
- **Phân khúc**: cơ cấu, phòng ngủ, diện tích, pháp lý, nội thất, ma trận cấu hình hỗ trợ AQ2.
- **Dự án**: số dự án, trạng thái, cường độ tin đăng, bản đồ, danh mục.
- **Chất lượng**: nguồn, giá, ghép dự án, độ phủ, cơ cấu KPI.
- **Khám phá**: bộ lọc nhiều chiều, bảng chi tiết, xuất CSV.
- **DSS**: xếp hạng, what-if 6 trọng số, segment gap, pipeline; cảnh báo chỉ khi view tồn tại.

## Views yêu cầu

`dw.v_listing`, `dw.v_kpi_base`, `dw.v_project_summary`, `dw.v_olap_location`, `dw.v_dss_province`, `dw.v_dss_district`, `dw.v_segment_gap`, `dw.v_pipeline_province`; `dw.v_alerts` là tùy chọn. Các biểu đồ dùng dữ liệu thực, thiếu view sẽ hiển thị thông báo thay vì số liệu tự tạo.

## Phạm vi và lưu ý

- `v_kpi_base`: 12 tháng gần nhất, tin cậy, không đăng lại; **không đồng nghĩa số tin theo năm đang chọn**.
- Giá/m² là trung vị các tin có giá/m² hợp lệ. Tin đăng không đồng nghĩa giao dịch, số căn hay hấp thụ.
- Bản đồ dùng OpenStreetMap, hiển thị từng dự án có tọa độ hợp lệ; phóng to và rê chuột để xem tên.
- Mô hình DSS gốc cho điểm giá cao tốt hơn; không nên diễn giải thành giá cạnh tranh. What-if chỉ mô phỏng thay đổi trọng số.
- Không có ngày đăng gốc/giá giao dịch thực tế thì không suy ra tốc độ hấp thụ.

## Kiểm thử

Mã nguồn được kiểm tra cú pháp và đóng gói; **chưa được chạy trên Supabase của người dùng**. Nếu view thực tế có tên cột khác, cần đối chiếu schema và điều chỉnh tương ứng.
