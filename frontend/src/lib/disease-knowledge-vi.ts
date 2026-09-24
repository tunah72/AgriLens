/**
 * Kiến thức bệnh học cây trồng chuyên sâu chuẩn Nông nghiệp Việt Nam
 * Hỗ trợ hiển thị 100% tiếng Việt cho cây Lúa và Cà phê.
 */

export interface VietnameseDiseaseKnowledge {
  name_vi: string;
  description: string;
  symptoms: string[];
  causes: string[];
  treatments: string[];
  prevention: string[];
  advisory: string;
}

export const DISEASE_KNOWLEDGE_VI: Record<string, VietnameseDiseaseKnowledge> = {
  Healthy: {
    name_vi: "Khỏe mạnh",
    description:
      "Lá cây phát triển bình thường, phiến lá đồng đều màu xanh đặc trưng của giống cây trồng. Không ghi nhận triệu chứng nhiễm nấm, vi khuẩn hay tổn thương do sâu hại.",
    symptoms: [
      "Phiến lá có màu xanh đồng nhất, kết cấu biểu bì nguyên vẹn, gân lá chắc khỏe.",
      "Không xuất hiện vết đốm hoại tử, quầng vàng, vết cháy bìa lá, hay lớp bột phấn trắng.",
      "Không ghi nhận dấu hiệu bị côn trùng chích hút hay cắn phá mô diệp lục.",
    ],
    causes: [
      "Không phát hiện tác nhân gây bệnh sinh học (nấm, vi khuẩn, virus) trên mẫu lá.",
      "Cây trồng đang trong trạng thái cân bằng sinh dưỡng và sinh trưởng tốt.",
    ],
    treatments: [
      "Duy trì chế độ chăm sóc, tưới tiêu và bón phân cân đối theo quy trình kỹ thuật.",
      "Không phun thuốc bảo vệ thực vật hóa học khi cây đang hoàn toàn khỏe mạnh.",
      "Tái kiểm tra định kỳ 5-7 ngày một lần để phát hiện sớm các nguy cơ phát sinh dịch hại.",
    ],
    prevention: [
      "Vệ sinh đồng ruộng sạch sẽ; tỉa cành tạo tán thông thoáng đối với vườn cà phê.",
      "Điều tiết mực nước hợp lý, tránh bón thừa đạm (N) làm cây mềm yếu dễ nhiễm bệnh.",
      "Thường xuyên thăm đồng, kiểm tra mặt dưới lá và các tầng lá dưới thấp.",
    ],
    advisory:
      "Lá cây đang ở trạng thái khỏe mạnh. Hãy duy trì chế độ canh tác cân đối và tiếp tục theo dõi đồng ruộng định kỳ.",
  },

  BrownSpot: {
    name_vi: "Bệnh đốm nâu hại lúa",
    description:
      "Bệnh đốm nâu do nấm Bipolaris oryzae gây ra, thường phát sinh và gây hại nặng trên các chân ruộng đất nghèo dinh dưỡng, đất chua phèn hoặc thiếu hụt kali, silic.",
    symptoms: [
      "Vết bệnh hình tròn hoặc bầu dục nhỏ màu nâu sẫm phân bố rải rác khắp phiến lá.",
      "Tâm vết bệnh về sau chuyển sang màu xám nhạt hoặc trắng xám, có viền nâu đỏ sẫm rõ rệt.",
      "Khi bệnh chuyển biến nặng, các vết đốm liên kết lại làm lá vàng úa, khô cháy từng mảng và giảm khả năng quang hợp.",
    ],
    causes: [
      "Nấm Bipolaris oryzae tồn tại trong tàn dư cây trồng, rơm rạ và phôi hạt giống nhiễm bệnh.",
      "Đất ruộng thiếu hụt kali, silic hoặc mất cân đối dinh dưỡng N-P-K nghiêm trọng.",
      "Thời tiết nóng ẩm, sương mù kéo dài hoặc ruộng bị hạn, phèn làm bộ rễ cây lúa kém phát triển.",
    ],
    treatments: [
      "Tháo cạn nước chua phèn (nếu có), bón bổ sung vôi bột khử chua và tăng cường bón phân Kali clorua (KCl) hoặc Silic.",
      "Phun luân phiên các hoạt chất trừ nấm đặc hiệu: Azoxystrobin, Difenoconazole, Tricyclazole hoặc Propiconazole theo đúng liều lượng hướng dẫn.",
      "Phun thuốc vào sáng sớm khi ráo sương hoặc chiều mát ngay khi vết đốm mới chớm xuất hiện.",
    ],
    prevention: [
      "Xử lý hạt giống bằng nước ấm (54°C trong 15 phút) hoặc thuốc trừ nấm trước khi gieo sạ.",
      "Vệ sinh đồng ruộng sau thu hoạch, cày vùi rơm rạ kết hợp bón chế phẩm vi sinh phân giải cellulose.",
      "Bón phân cân đối, tuyệt đối không bón thừa phân đạm trong giai đoạn đẻ nhánh rộ và làm đòng.",
    ],
    advisory:
      "Cần kết hợp cải tạo nền đất ruộng và bổ sung dinh dưỡng Kali bên cạnh việc phun thuốc trừ nấm để ngăn ngừa bệnh tái phát bền vững.",
  },

  LeafBlast: {
    name_vi: "Bệnh đạo ôn lá lúa",
    description:
      "Bệnh đạo ôn là bệnh hại nguy hiểm hàng đầu trên lúa do nấm Magnaporthe oryzae gây ra. Bệnh có tốc độ lây lan rất nhanh theo gió và có thể làm lụi tàn cả ruộng lúa nếu không khoanh vùng xử lý kịp thời.",
    symptoms: [
      "Ban đầu là các vết chấm kim nhỏ màu xám xanh hoặc nâu nhạt rải rác trên mặt lá.",
      "Vết bệnh nhanh chóng phát triển thành hình thoi (hình mắt én), tâm xám trắng, viền ngoài nâu sẫm, xung quanh có quầng vàng tươi.",
      "Khi bệnh nặng, nhiều vết bệnh liên kết làm toàn bộ phiến lá bị khô cháy hoàn toàn (cháy lá), cây lúa lụi tàn.",
    ],
    causes: [
      "Bào tử nấm Magnaporthe oryzae phát tán cực mạnh theo gió, sương mù và nước mưa.",
      "Độ ẩm không khí cao (>90%), nhiệt độ mát mẻ (20-28°C), trời âm u có mưa phùn hoặc sương đêm kéo dài.",
      "Gieo cấy quá dày, bón thừa phân đạm làm lá lúa mềm mỏng, tạo điều kiện cho nấm xâm nhiễm.",
    ],
    treatments: [
      "Ngừng ngay việc bón phân đạm, phân bón lá và các chất kích thích sinh trưởng khi phát hiện vết bệnh hình thoi.",
      "Giữ mực nước nông (3-5 cm) trong ruộng để cung cấp đủ ẩm cho cây lúa hồi phục.",
      "Phun thuốc đặc trị đạo ôn ngay lập tức: Tricyclazole (Beam, Trizole), Isoprothiolane (Fujione), Fenoxanil, hoặc hỗn hợp Azoxystrobin + Difenoconazole.",
      "Nếu thời tiết tiếp tục âm u có sương, phun lặp lại lần 2 sau 5-7 ngày.",
    ],
    prevention: [
      "Sử dụng các giống lúa kháng hoặc chống chịu đạo ôn đã được cơ quan nông nghiệp xác nhận.",
      "Gieo sạ mật độ hợp lý (80-100 kg/ha đối với sạ lan, 60-80 kg/ha đối với sạ hàng).",
      "Áp dụng quy trình '3 giảm 3 tăng' hoặc '1 phải 5 giảm', bón đạm theo bảng so màu lá lúa.",
    ],
    advisory:
      "Bào tử đạo ôn lây lan cực nhanh theo luồng gió; cần kiểm tra các ruộng lân cận để khoanh vùng phun phòng trừ đồng loạt.",
  },

  Hispa: {
    name_vi: "Bọ gai hại lúa",
    description:
      "Bọ gai (sâu gai) là loài côn trùng hại lá lúa. Cả bọ trưởng thành và sâu non đều cắn phá biểu bì lá, làm giảm mạnh diện tích quang hợp khiến cây lúa còi cọc và giảm năng suất.",
    symptoms: [
      "Mặt trên phiến lá xuất hiện các vệt cào xước màu trắng xám chạy song song dọc theo gân lá do bọ trưởng thành cạo ăn chất diệp lục.",
      "Sâu non đục lòn vào giữa hai lớp biểu bì tạo thành các đường hầm ngoằn ngoèo hoặc đốm phồng mờ màu xám nhạt.",
      "Lá lúa bị xơ xác, đầu ngọn lá khô cháy và quăn lại, cây lúa còi cọc, chậm phát triển.",
    ],
    causes: [
      "Bọ cánh cứng gai Dicladispa armigera đẻ trứng vào mô đầu lá lúa.",
      "Gieo cấy lúa quá dày, ruộng ngập úng lâu ngày và bón thừa phân đạm tạo điều kiện cho bọ sinh sôi mạnh.",
      "Thời tiết ấm nóng, ẩm độ cao vào đầu vụ xuân hè hoặc hè thu.",
    ],
    treatments: [
      "Dùng vợt bắt bọ gai trưởng thành vào sáng sớm khi sương chưa tan và bọ còn ít hoạt động.",
      "Cắt bỏ phần ngọn lá có chứa ổ trứng và sâu non đem ra khỏi ruộng tiêu hủy.",
      "Phun trừ bằng các loại thuốc có tính nội hấp hoặc thấm sâu: Cartap, Chlorantraniliprole, Thiamethoxam, hoặc Alpha-cypermethrin khi mật độ bọ cao.",
    ],
    prevention: [
      "Vệ sinh sạch cỏ dại quanh bờ ruộng, mương máng – nơi trú ngụ của bọ gai giữa các vụ lúa.",
      "Bảo vệ các loài thiên địch tự nhiên như ong ký sinh trứng, nhện bắt mồi và bọ rùa đỏ.",
      "Điều tiết mực nước ruộng hợp lý, làm đất kỹ và gieo cấy đúng khung thời vụ khuyến cáo.",
    ],
    advisory:
      "Nên phun thuốc vào sáng sớm hoặc chiều mát khi bọ trưởng thành tập trung nhiều trên bề mặt lá để đạt hiệu quả diệt trừ cao nhất.",
  },

  LeafMiner: {
    name_vi: "Sâu vẽ bùa hại lá cà phê",
    description:
      "Sâu vẽ bùa (Leucoptera coffeella) là một trong những đối tượng dịch hại nguy hiểm nhất trên cây cà phê. Sâu non đục ăn nhu mô lá tạo thành các vệt hoại tử loang lổ, gây rụng lá hàng loạt làm suy kiệt cây.",
    symptoms: [
      "Ban đầu xuất hiện các đường rãnh ngoằn ngoèo màu xám trắng dưới biểu bì lá.",
      "Về sau vết đục lan rộng thành các mảng hoại tử màu nâu tròn hoặc bầu dục loang lổ trên phiến lá.",
      "Biểu bì trên vết hại phồng rộp, bên trong có phân sâu màu đen; lá bị hại nặng sẽ khô xác và rụng sớm, trơ cành mang quả.",
    ],
    causes: [
      "Bướm nhỏ Leucoptera coffeella hoạt động vào chiều tối và ban đêm, đẻ trứng rải rác trên mặt lá cà phê.",
      "Vườn cà phê thiếu cây che bóng, ánh sáng chiếu trực xạ mạnh và nhiệt độ cao là điều kiện sâu bùng phát.",
      "Lạm dụng thuốc trừ sâu hóa học phổ rộng làm tiêu diệt các loài ong ký sinh thiên địch.",
    ],
    treatments: [
      "Tỉa bỏ và gom đốt các lá bị hại nặng ở tầng dưới tán để tiêu diệt sâu non và nhộng bên trong.",
      "Phun các hoạt chất có tính thấm sâu và lưu dẫn cao: Abamectin, Emamectin benzoate, Spinetoram hoặc Cyantraniliprole.",
      "Phun ướt đều cả hai mặt lá, ưu tiên phun lúc sâu non mới nở tuổi 1-2.",
    ],
    prevention: [
      "Trồng cây che bóng hợp lý (muồng đen, sầu riêng, mắc ca) để giảm bức xạ nhiệt chiếu trực tiếp vào tán lá cà phê.",
      "Bảo tồn các loài ong ký sinh họ Eulophidae và Braconidae bằng cách hạn chế phun thuốc hóa học độc hại.",
      "Tưới nước và bón phân cân đối giúp cây ra lộc tập trung, dễ quản lý dịch hại.",
    ],
    advisory:
      "Sâu non nằm sâu trong biểu bì lá, vì vậy thuốc bảo vệ thực vật bắt buộc phải có tính thấm sâu hoặc nội hấp mới đem lại hiệu quả diệt trừ.",
  },

  PowderyMildew: {
    name_vi: "Bệnh phấn trắng trên cà phê",
    description:
      "Bệnh phấn trắng bao phủ bề mặt lá, chồi non và cành bằng một lớp màng nấm trắng mịn như bột phấn, làm biến dạng phiến lá và suy giảm nghiêm trọng khả năng quang hợp của cây cà phê.",
    symptoms: [
      "Xuất hiện các đốm bột phấn màu trắng xám rải rác ở cả hai mặt lá và trên ngọn non.",
      "Lớp phấn trắng lan rộng bao phủ toàn bộ phiến lá; lá bị bệnh trở nên quăn queo, giòn, méo mó và chuyển màu vàng nhạt.",
      "Chồi non bị chùn đọt, lá non rụng sớm, chùm hoa và quả non có thể bị teo tóp rụng non.",
    ],
    causes: [
      "Bào tử nấm phát tán nhờ gió và không khí khô ráo sau những đợt mưa ẩm kéo dài.",
      "Độ ẩm ban đêm cao (>85%) kết hợp ban ngày ấm áp, nhiều sương mù buổi sớm.",
      "Tán cây cà phê quá rậm rạp, thiếu thông thoáng và thiếu ánh sáng khuếch tán vào trong tán.",
    ],
    treatments: [
      "Cắt tỉa ngay các cành vượt, cành tăm và chồi non bị nhiễm bệnh đem ra khỏi vườn tiêu hủy.",
      "Phun các loại thuốc gốc lưu huỳnh (Sulfur) hoặc các hoạt chất trừ nấm đặc hiệu: Hexaconazole, Difenoconazole, Diniconazole, Triadimefon.",
      "Phun thuốc vào sáng sớm sau khi sương tan hoặc chiều mát.",
    ],
    prevention: [
      "Tỉa cành tạo tán thông thoáng sau mỗi vụ thu hoạch để ánh sáng mặt trời chiếu đều vào trong tán cây.",
      "Bón phân cân đối, tăng cường bón phân hữu cơ vi sinh và bổ sung Kali, Canxi, Silic giúp thành tế bào lá dày chắc.",
      "Tránh tưới phun mưa thẳng lên ngọn vào chiều tối.",
    ],
    advisory:
      "Khi sử dụng thuốc trừ nấm gốc lưu huỳnh, tránh phun vào những ngày nắng gắt nhiệt độ cao trên 32°C vì dễ gây cháy lá non.",
  },

  Rust: {
    name_vi: "Bệnh gỉ sắt cà phê",
    description:
      "Bệnh gỉ sắt do nấm Hemileia vastatrix gây ra là bệnh hại nguy hiểm hàng đầu trên cây cà phê (đặc biệt là cà phê chè Arabica), gây rụng lá hàng loạt, khô cành và suy kiệt vườn cây.",
    symptoms: [
      "Mặt dưới lá xuất hiện các đốm tròn nhỏ phủ đầy lớp bột phấn màu vàng cam tươi giống như bột sắt rỉ.",
      "Tương ứng ở mặt trên phiến lá là các đốm đổi màu vàng nhạt mất chất diệp lục.",
      "Về sau tâm vết bệnh khô dần và chuyển sang màu nâu sẫm; bệnh nặng khiến lá rụng trơ trụi cành, quả khô héo và cây kiệt quệ.",
    ],
    causes: [
      "Bào tử nấm Hemileia vastatrix nảy mầm khi có màng nước tự do đọng trên lá trong 24-48 giờ.",
      "Bào tử lây lan qua giọt bắn của hạt mưa, gió và qua dụng cụ thu hái, quần áo người làm vườn.",
      "Vườn rậm rạp, ẩm ướt trong mùa mưa, giống cà phê mẫn cảm với nấm bệnh.",
    ],
    treatments: [
      "Phun phòng ngừa bằng các loại thuốc gốc đồng (Copper Hydroxide, Cuprous Oxide, Bordeaux) vào đầu mùa mưa khi bệnh chớm xuất hiện.",
      "Khi tỷ lệ bệnh trên 5% diện tích lá, chuyển sang phun thuốc nội hấp lưu dẫn: Cyproconazole, Hexaconazole, Pyraclostrobin, hoặc Epoxiconazole.",
      "Phun kỹ tập trung vào mặt dưới của phiến lá – nơi nấm hình thành ổ bào tử.",
    ],
    prevention: [
      "Ghép cải tạo hoặc trồng các giống cà phê kháng bệnh gỉ sắt (giống Catimor, các dòng vô tính chọn lọc TR4, TR9...).",
      "Cắt tỉa cành thông thoáng sau thu hoạch, dọn sạch tàn dư cỏ rác dưới gốc cây.",
      "Bón phân đầy đủ và cân đối, bón vôi nông nghiệp khử chua đất định kỳ hàng năm.",
    ],
    advisory:
      "Bào tử gỉ sắt tập trung 100% ở mặt dưới phiến lá; khi phun thuốc bắt buộc phải hướng vòi phun từ dưới lên trên mặt lá mới đạt hiệu quả diệt trừ.",
  },

  AlgalLeafSpot: {
    name_vi: "Bệnh đốm rong trên cà phê",
    description:
      "Bệnh đốm rong (đốm da cam) do loài tảo ký sinh Cephaleuros virescens gây ra. Bệnh xuất hiện trên lá già và cành bánh tẻ ở những vườn cà phê già cỗi, đất nghèo dinh dưỡng hoặc vườn quá ẩm rậm.",
    symptoms: [
      "Mặt trên phiến lá xuất hiện các vết đốm tròn hơi gồ lên khỏi mặt lá, bề mặt phủ lớp nhung mịn màu cam gỉ hoặc xám xanh.",
      "Về sau vết đốm chuyển sang màu nâu đen, mô lá phía dưới bị hoại tử khô xác.",
      "Trên cành, bệnh làm nứt vỏ, vỏ sần sùi màu nâu đỏ, cành còi cọc và dễ gãy khi mang quả nặng.",
    ],
    causes: [
      "Ký sinh trùng là tảo Cephaleuros virescens phát triển mạnh trong điều kiện ẩm ướt, thiếu ánh sáng.",
      "Cây cà phê già cỗi, suy kiệt sau thu hoạch hoặc bị nghẹt rễ, thiếu phân bón hữu cơ.",
      "Vườn cây rậm rạp, thoát nước kém trong mùa mưa bão.",
    ],
    treatments: [
      "Cắt tỉa cành khô, cành nhiễm đốm rong nặng đem gom đốt.",
      "Phun ướt đẫm tán lá và thân cành bằng các loại thuốc trừ tảo gốc đồng: Copper Oxychloride, Đồng Đỏ (Cuprous Oxide), Booc-đô 1%.",
      "Có thể phối hợp hoạt chất Mancozeb hoặc Azoxystrobin để tăng hiệu lực diệt tảo.",
    ],
    prevention: [
      "Tỉa cành tạo tán sau thu hoạch để vườn luôn thông thoáng, đón nhận đủ ánh sáng mặt trời.",
      "Bón phân cân đối N-P-K kết hợp bón nhiều phân chuồng hoai mục hoặc phân hữu cơ vi sinh để nâng cao sức đề kháng của cây.",
      "Đào rãnh thoát nước chống ngập úng gốc trong mùa mưa.",
    ],
    advisory:
      "Bệnh đốm rong do tảo gây ra chứ không phải do nấm thông thường, do đó các loại thuốc gốc đồng là biện pháp đặc hiệu và hiệu quả nhất.",
  },
};

/**
 * Lấy thông tin bệnh học tiếng Việt cho một nhãn bệnh
 */
export function getVietnameseDiseaseKnowledge(label: string): VietnameseDiseaseKnowledge | null {
  return DISEASE_KNOWLEDGE_VI[label] ?? null;
}
