# Thin SPEC - Location-based Food Recommendation

Dựa trên Insight và Opportunity từ Evidence Pack (theo hướng dẫn của bài Day 05), dưới đây là bản Thin SPEC để chuẩn bị build prototype trong Day 06.

---

## 1. Cơ hội (Opportunity Statement)

Cơ hội là dùng AI để **augment quá trình ra quyết định chọn quán ăn**, thay thế vai trò của người địa phương biết rành khu vực — trust signal cao nhất mà khách du lịch không có —
giúp họ **vượt qua "dining decision anxiety"**: chọn được quán phù hợp khẩu vị/ngân sách, tránh tourist trap, không tốn công đọc hàng chục review trái chiều bằng cách AI chủ động hỏi để hiểu intent thay vì chỉ lọc theo category,
trong khi vẫn kiểm soát **rủi ro thông tin lỗi thời (quán đóng cửa, đổi địa chỉ) khiến khách mất công di chuyển và có trải nghiệm tệ làm hỏng cả chuyến đi**.

## 2. Quyết định AI (Auto/Aug decision)

Prototype nên đi theo hướng **AI Augment**: AI đóng vai trò hỗ trợ người dùng tìm kiếm, lọc và so sánh các lựa chọn quán ăn, nhưng **không tự động quyết định thay người dùng**. Trong phạm vi Day 06, hệ thống không nên để AI tự đặt món, tự đặt bàn hoặc tự chọn quán cuối cùng, vì quyết định ăn uống phụ thuộc nhiều vào khẩu vị cá nhân, ngân sách, tình trạng sức khỏe và bối cảnh thực tế tại địa điểm du lịch.

- **Phương pháp:** AI Augmentation — AI hỗ trợ gợi ý, người dùng giữ quyền quyết định cuối cùng.
- **Mức độ tự động hóa:** AI chỉ dừng ở mức tư vấn và đề xuất. Các hành động có rủi ro như đặt món, đặt bàn, gọi quán, mở chỉ đường hoặc thanh toán đều cần người dùng tự xác nhận và thực hiện.
- **Lý do không chọn full automation:** Dữ liệu quán ăn có thể thay đổi theo thời gian thực, ví dụ quán đóng cửa, hết món, đổi giá, thay đổi giờ mở cửa hoặc chất lượng dịch vụ không ổn định. Ngoài ra, review/rating có thể bị nhiễu và không phản ánh đúng khẩu vị của từng khách du lịch. Nếu AI tự động quyết định, người dùng có thể mất thời gian di chuyển đến quán không phù hợp hoặc gặp rủi ro liên quan đến dị ứng, ăn kiêng và ngân sách.

| Rủi ro | Vì sao cần human-in-the-loop | Cách prototype xử lý |
|---|---|---|
| Quán đóng cửa hoặc đổi giờ mở cửa | Dữ liệu bản đồ/review có thể chưa cập nhật kịp thời | AI hiển thị cảnh báo và yêu cầu user kiểm tra lại trên bản đồ trước khi đi |
| Giá thay đổi | Giá món ăn có thể khác so với thông tin cũ | AI chỉ đưa mức giá tham khảo, không cam kết giá chính xác |
| Review không đáng tin | Rating có thể bị nhiễu, seeding hoặc không phù hợp với nhu cầu cá nhân | AI tóm tắt cả điểm mạnh và điểm cần cân nhắc từ review |
| Khẩu vị cá nhân khác nhau | Cùng một quán có thể hợp với người này nhưng không hợp với người khác | AI hỏi trước về món muốn ăn, khẩu vị, ngân sách và khoảng cách chấp nhận được |
| Dị ứng hoặc ăn kiêng | Sai sót có thể ảnh hưởng trực tiếp đến sức khỏe người dùng | AI luôn hỏi về dị ứng/ăn kiêng và nhắc user xác nhận lại với quán |

**Human giữ quyền ở đâu:** Người dùng giữ quyền kiểm soát ở các bước quan trọng trong flow: chọn tiêu chí ban đầu, xem danh sách gợi ý, so sánh 3 quán, chọn quán cuối cùng, bấm chỉ đường, gọi quán hoặc đặt món qua nền tảng bên ngoài. AI không được tự động thực hiện các hành động này nếu chưa có xác nhận rõ ràng từ người dùng.

**AI làm gì:** AI đóng vai trò như một **Local Guide Assistant**. AI hỏi 2-3 câu để hiểu nhu cầu, ví dụ người dùng muốn ăn món gì, ngân sách bao nhiêu, đi một mình hay đi nhóm, có dị ứng hay ăn kiêng không, muốn đi bộ hay chấp nhận di chuyển xa hơn. Sau đó AI lọc các lựa chọn phù hợp, xếp hạng mức độ phù hợp, đưa ra 3 quán đề xuất kèm lý do ngắn gọn, cảnh báo nếu dữ liệu chưa chắc chắn và gợi ý phương án thay thế khi không tìm thấy quán phù hợp.

**Ranh giới trách nhiệm của AI trong prototype:** AI chỉ nên đưa ra khuyến nghị có giải thích, không cam kết thông tin là tuyệt đối chính xác. Mỗi gợi ý cần có lý do rõ ràng như phù hợp ngân sách, gần vị trí hiện tại, món ăn đúng nhu cầu, review tốt hoặc phù hợp với khách du lịch. Nếu dữ liệu yếu hoặc không chắc chắn, AI phải nói rõ mức độ không chắc chắn thay vì đưa ra câu trả lời quá tự tin.

**Kết luận quyết định:** Với bài toán gợi ý quán ăn theo vị trí cho khách du lịch, lựa chọn hợp lý nhất là **AI Augment, không phải AI Automate**. Cách tiếp cận này giúp prototype vẫn tạo giá trị rõ ràng là giảm thời gian tìm kiếm và ra quyết định, đồng thời giữ người dùng trong vòng kiểm soát để hạn chế rủi ro từ dữ liệu sai, thông tin lỗi thời và khác biệt khẩu vị cá nhân.

## 3. Build Slice

Cho **khách du lịch lần đầu đến một tỉnh/thành lạ** (ví dụ: vừa check-in khách sạn, không có người quen hỏi thăm), đang ở trạng thái **đói và không biết bắt đầu tìm ở đâu**,

prototype dùng AI để **thu thập nhu cầu nhanh qua MCQ (Multiple Choice Questions) và gợi ý 3 quán ăn phù hợp gần vị trí hiện tại**,

tạo ra **danh sách 3 quán kèm lý do gợi ý ngắn gọn (tổng hợp từ review thực tế)**,

và xử lý **lỗi AI không tìm thấy quán phù hợp** bằng cách **mở rộng bán kính tìm kiếm hoặc gợi ý lựa chọn an toàn phổ thông**.

### 3a. Input Flow — MCQ thay vì hỏi mở

Thay vì AI đặt câu hỏi tự do (khiến user phải nghĩ và gõ nhiều), prototype hiển thị **4 màn hình MCQ ngắn** để người dùng chọn nhanh:

| # | Câu hỏi MCQ | Lựa chọn mẫu |
|---|---|---|
| 1 | **Bữa ăn này là bữa nào?** | 🌅 Sáng / ☀️ Trưa / 🌙 Tối / 🌃 Khuya |
| 2 | **Bạn ăn cùng ai?** | 👤 Một mình / 👫 Đôi / 👨‍👩‍👧 Gia đình / 👥 Nhóm bạn (3+) |
| 3 | **Phong cách bữa ăn bạn muốn?** | 🍜 Đặc sản địa phương / 🍱 Nhanh - gọn / 🕯️ Thoải mái - ngồi lâu / 💰 Bình dân - no bụng |
| 4 | **Có yêu cầu đặc biệt nào không?** | 🥗 Chay / 🚫 Không hải sản / 🌶️ Không cay / ✅ Không có yêu cầu gì |

> **AI decision:** Sau khi user hoàn tất 4 MCQ, AI tự động tổng hợp profile bữa ăn và sinh ra 3 gợi ý — **không cần user gõ thêm gì**.

### 3b. Walkthrough Example — Bối cảnh cụ thể

> **Persona:** Minh, 28 tuổi, đi du lịch Nha Trang một mình lần đầu. Vừa check-in khách sạn gần biển lúc 12h trưa, bụng đói, không quen ai ở đây, mở app.

**Bước 1 — App xác định vị trí:** GPS tự động → *"Bạn đang ở Nha Trang, Khánh Hòa"* ✅

**Bước 2 — Minh trả lời 4 MCQ (mỗi câu chỉ cần tap 1 lần):**

| # | Câu hỏi | Minh chọn |
|---|---|---|
| 1 | Bữa ăn này là bữa nào? | ☀️ **Trưa** |
| 2 | Bạn ăn cùng ai? | 👤 **Một mình** |
| 3 | Phong cách bữa ăn? | 🍜 **Đặc sản địa phương** |
| 4 | Có yêu cầu đặc biệt? | ✅ **Không có yêu cầu gì** |

**Bước 3 — AI tổng hợp và trả kết quả (không cần Minh gõ thêm gì):**

---

🍽️ **Gợi ý cho bữa trưa một mình tại Nha Trang — Đặc sản địa phương**

**① Bún cá Nha Trang Bà Bảy**
📍 12 Bến Chợ, cách bạn 350m — đi bộ ~5 phút
⭐ 4.6 · "Nước dùng đậm vị cá tươi, đúng kiểu Nha Trang, giá 45k/tô"
💡 *Phù hợp vì: đặc sản nổi tiếng, suất ăn một người, mở đến 14h*

**② Bánh căn Mỹ Hòa**
📍 Đường Trần Phú, cách bạn 600m — đi bộ ~8 phút
⭐ 4.4 · "Bánh giòn, trứng chín đều, ăn kèm mắm nêm rất ngon"
💡 *Phù hợp vì: ăn nhẹ buổi trưa, thử đặc sản bánh căn vùng biển*

**③ Nem nướng Ninh Hòa Hai Bà**
📍 Lô 6 Chợ Đầm, cách bạn 1.1km — xe ôm ~5 phút
⭐ 4.7 · "Nem cuốn bánh tráng tại chỗ, tươi ngon, không cần đặt trước"
💡 *Phù hợp vì: món Khánh Hòa không nơi nào có, review rất ổn định*

---

> ⚠️ *Giờ mở cửa có thể thay đổi. Nhấn tên quán để kiểm tra trên Google Maps trước khi xuất phát.*

**Bước 4 — Minh chọn quán ① → App mở Google Maps chỉ đường.**

---

### 3c. Evidence Anchor

| Loại | Bằng chứng cụ thể | Nguồn |
|---|---|---|
| **Self-use** | Một thành viên nhóm đi Đà Lạt lần đầu (tháng 4/2025): mở Google Maps gõ *"quán ăn ngon gần đây"* → 47 kết quả, không biết chọn cái nào → scroll 10 phút → hỏi nhân viên lễ tân khách sạn → nhận được 1 gợi ý cụ thể và đi ngay. **Vấn đề:** cần một người quen biết địa phương mới ra được quyết định. | Trải nghiệm cá nhân thành viên nhóm |
| **User quote** | *"Mỗi lần đến thành phố mới mình lại mở Google Maps rồi không biết gõ gì, scroll mãi không chọn được"* — phỏng vấn nhanh 1 bạn trong lớp | Interview Day 05 |
| **Competitor gap** | Foody/Google Maps yêu cầu user tự gõ từ khoá → không filter được bối cảnh (bữa nào, mấy người, phong cách); không có lý do gợi ý match với nhu cầu | Tự kiểm tra UI Foody v3.x & Google Maps |
| **Behavioural data** | 61% người dùng rời ứng dụng food discovery sau bước tìm kiếm đầu tiên nếu không thấy kết quả phù hợp ngay *(Nielsen Norman Group, 2023)* | Desk research |

## 4. Four Paths (4 Kịch bản)

### ✅ Happy Path

Người dùng cung cấp đủ thông tin cần thiết (số người ăn, loại món mong muốn, ngân sách, khoảng cách chấp nhận, các yêu cầu đặc biệt như ăn chay hoặc dị ứng thực phẩm). Nếu còn thiếu thông tin quan trọng, AI sẽ hỏi bổ sung ngắn gọn trước khi tìm kiếm.

AI tổng hợp nhu cầu, tìm các quán phù hợp gần vị trí hiện tại và trả về 3 gợi ý tốt nhất kèm:

- Tên quán
- Khoảng cách
- Mức giá phù hợp
- Lý do đề xuất ngắn gọn (tổng hợp từ review và thông tin công khai)

Người dùng chọn một quán và chuyển sang xem đường đi hoặc thông tin liên hệ.

---

### ⚠️ Low-Confidence Path

AI tìm được các quán tương đối phù hợp nhưng độ tin cậy của dữ liệu không cao, ví dụ:

- Review quá ít
- Review mâu thuẫn nhau
- Dữ liệu đã cũ
- Chỉ đáp ứng một phần tiêu chí của người dùng

Thay vì thể hiện sự chắc chắn quá mức, AI vẫn đưa ra gợi ý nhưng kèm cảnh báo về mức độ tin cậy.

> **Ví dụ:**
> "Quán này phù hợp với tiêu chí của bạn, tuy nhiên gần đây có một số review phản ánh thời gian lên món khá chậm."
>
> Hoặc:
>
> "Quán này có món bạn yêu cầu nhưng số lượng review gần đây còn hạn chế, bạn nên tham khảo thêm trước khi quyết định."

---

### ❌ Failure Path

Người dùng đưa ra các tiêu chí quá hẹp hoặc quá khó để hệ thống tìm được kết quả phù hợp.

> **Ví dụ:**
> Tìm quán hủ tiếu chay đang mở cửa lúc 2 giờ sáng, cách dưới 500m.

Sau khi tìm kiếm trong phạm vi hiện tại, hệ thống không tìm thấy quán nào đáp ứng đầy đủ các điều kiện. AI sẽ thông báo rõ ràng:

> "Hiện tại mình không tìm thấy quán nào đáp ứng đầy đủ các tiêu chí bạn yêu cầu."

**Lưu ý:** AI không được tự bịa dữ liệu hoặc gợi ý các quán không đáp ứng điều kiện chỉ để có kết quả.

---

### 🔄 Correction Path

Sau khi xảy ra Failure hoặc khi người dùng không hài lòng với các gợi ý hiện tại, AI chủ động đề xuất các phương án thay thế nhằm tiếp tục hỗ trợ thay vì kết thúc cuộc hội thoại.

> **Ví dụ:**
> "Hiện tại quanh đây không có quán hủ tiếu chay mở giờ này."
>
> Mình có thể:
> - Mở rộng bán kính tìm kiếm lên 5km
> - Gợi ý các quán chay khác vẫn đang mở
> - Gợi ý cửa hàng tiện lợi gần nhất có đồ ăn chay
>
> Hoặc:
>
> "Mình chưa tìm được quán đáp ứng 100% tiêu chí của bạn. Bạn muốn ưu tiên giữ nguyên món ăn hay giữ nguyên khoảng cách để mình tìm phương án gần nhất?"

**Mục tiêu của Correction Path** là không để người dùng rơi vào ngõ cụt và luôn có hướng xử lý tiếp theo.

---

## 5. Failure Mode

### Failure Mode: Recommendation Mismatch Due to Unreliable Data

**Tình huống**

Người dùng có một yêu cầu quan trọng ảnh hưởng trực tiếp đến quyết định ăn uống, ví dụ:

- Ăn chay
- Dị ứng thực phẩm
- Không ăn hải sản
- Yêu cầu thực đơn Halal
- Đi theo nhóm đông người

AI dựa trên dữ liệu địa điểm và review công khai để đưa ra gợi ý. Tuy nhiên, menu, giờ mở cửa hoặc cách phục vụ của quán có thể đã thay đổi và không được cập nhật kịp thời. Kết quả là AI có thể đề xuất một quán tưởng như phù hợp nhưng thực tế không đáp ứng được yêu cầu của người dùng.

**Tác động**

- Người dùng mất thời gian di chuyển.
- Trải nghiệm du lịch bị gián đoạn.
- Người dùng mất niềm tin vào hệ thống.
- Trong trường hợp dị ứng thực phẩm, có thể gây rủi ro nghiêm trọng.

**Cách Prototype Xử Lý**

1. AI đánh dấu các yêu cầu như dị ứng, ăn chay hoặc yêu cầu đặc biệt là **Critical Constraints**.
2. Với các ràng buộc quan trọng này, AI chỉ đưa ra gợi ý khi tìm thấy đủ bằng chứng từ dữ liệu hiện có.
3. Nếu độ tin cậy thấp hoặc dữ liệu không rõ ràng, AI sẽ hiển thị cảnh báo thay vì khẳng định chắc chắn.

> **Ví dụ:**
> "Review gần đây cho thấy quán có phục vụ món chay, tuy nhiên thông tin menu có thể đã thay đổi. Bạn nên liên hệ trực tiếp với quán để xác nhận trước khi đến."

Mọi kết quả gợi ý đều kèm thông báo:

> "Các đề xuất được tổng hợp từ dữ liệu và review công khai hiện có. Thông tin có thể thay đổi theo thời gian. Đối với các yêu cầu quan trọng, vui lòng xác nhận trực tiếp với cơ sở kinh doanh trước khi ghé thăm."

**Nguyên tắc thiết kế:** AI hỗ trợ người dùng ra quyết định, nhưng không thay thế việc xác nhận cuối cùng với cơ sở kinh doanh khi có các yêu cầu đặc biệt hoặc liên quan đến an toàn thực phẩm.

---

## 6. Owner Plan (Phân công Day 06)

*(Nhóm điền tên các thành viên phụ trách)*

| Nhiệm vụ | Người phụ trách |
|---|---|
| Research & Evidence (Kiểm chứng bằng chứng) | Nguyễn Tùng Lâm & Đỗ Phan Hà|
| Prompt Engineering (Thiết kế prompt cho AI Local Guide) | Đàm Xuân Giáp|
| Thiết kế UI/UX & Flow của Prototype | Đỗ Tuấn Đạt |
| Test 4 paths & Failure mode | Hoàng Hiếu Trung |
| Làm slide & chuẩn bị Demo | Phan Văn Hiếu |

---

## 7. Backlog (Không build trong Day 06)

Những thứ không build trong Day 06 để đảm bảo scope đủ nhỏ:

- Tính năng đặt bàn trực tiếp qua AI.
- Đặt đồ ăn giao tận nơi (chỉ tập trung gợi ý quán ăn gần đó để khách tự đi/book xe).
- Tích hợp thanh toán/ưu đãi voucher.
