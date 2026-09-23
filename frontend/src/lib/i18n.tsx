"use client";

import React, { createContext, useContext, useEffect, useState, useMemo } from "react";

export type Language = "vi" | "en";

export const translations = {
  vi: {
    // App & Brand
    brand: "AgriLens",
    appTitle: "AgriLens - Hệ thống chẩn đoán bệnh lá lúa & cà phê",
    appDescription: "Hệ thống AI chẩn đoán bệnh và khuyến nghị điều trị trên lá cây lúa và cà phê.",
    tagline: "Chẩn đoán bệnh học & Hỗ trợ điều trị cây trồng bằng AI",
    
    // Navigation & Tabs
    diagnosis: "Chẩn đoán",
    newDiagnosis: "Chẩn đoán mới",
    knowledge: "Cơ sở tri thức",
    knowledgeShort: "Tri thức",
    history: "Lịch sử chẩn đoán",
    historyShort: "Lịch sử",
    signIn: "Đăng nhập",
    signUp: "Đăng ký",
    signOut: "Đăng xuất",
    yourAccount: "Tài khoản của bạn",
    collapseNav: "Thu gọn thanh điều hướng",
    expandNav: "Mở rộng thanh điều hướng",
    loadingAccount: "Đang tải trạng thái tài khoản",
    
    // Header
    switchThemeLight: "Chuyển sang chế độ sáng",
    switchThemeDark: "Chuyển sang chế độ tối",
    switchLanguage: "Chuyển sang Tiếng Anh (Switch to English)",
    langVi: "Tiếng Việt",
    langEn: "English",

    // Home / Hero
    heroTitle: "Chẩn đoán bệnh lá cây trồng",
    heroSubtitle: "Tải lên ảnh chụp lá lúa hoặc cà phê bị bệnh để nhận chẩn đoán AI tức thì và hướng dẫn điều trị từ chuyên gia nông học.",
    
    // Image Uploader
    dragDropPrompt: "Kéo thả hoặc nhấn để chọn ảnh lá cây (Lúa / Cà phê)",
    readyToDiagnose: "Ảnh đã sẵn sàng để chẩn đoán",
    attachDevice: "Đính kèm ảnh từ máy",
    takePhoto: "Chụp ảnh từ camera",
    startDiagnosisBtn: "Bắt đầu chẩn đoán",
    analyzingImage: "Hệ thống đang phân tích ảnh lá...",
    unsupportedFormat: "Chỉ hỗ trợ định dạng ảnh JPEG, PNG hoặc WEBP.",
    fileTooLarge: "Dung lượng ảnh vượt quá giới hạn 10 MB.",
    removeFile: "Xóa ảnh",
    uploadedImage: "Ảnh đã tải lên",
    errorPrefix: "Lỗi:",

    // Results
    analysisResults: "Kết quả chẩn đoán",
    topPrediction: "Chẩn đoán bệnh học",
    confidenceScores: "Độ tin cậy",
    modelLatency: "Thời gian xử lý",
    crop: "Cây trồng",
    cropRice: "Lúa",
    cropCoffee: "Cà phê",
    severity: "Mức độ gây hại",
    severityHigh: "Nghiêm trọng (Cao)",
    severityMedium: "Trung bình",
    severityLow: "Nhẹ",
    confidenceAlternatives: "Độ tin cậy & Các bệnh liên quan",
    alternativeDiagnoses: "Các khả năng bệnh học khác",
    alternativeDesc: "Tỷ lệ dự đoán của các lớp bệnh liên quan",
    closeMarginWarningTitle: "Cảnh báo độ chênh lệch thấp",
    closeMarginWarningDesc: "Hai bệnh dự đoán hàng đầu chênh lệch dưới 10%. Khuyến nghị: Đối chiếu thêm triệu chứng ngoài đồng ruộng trong mục Cơ sở tri thức hoặc chụp lại ảnh sắc nét hơn.",

    // Expert Recommendation
    expertRecommendation: "Khuyến nghị điều trị từ chuyên gia",
    detailedDescription: "Mô tả chi tiết bệnh học",
    typicalSymptoms: "Triệu chứng nhận biết",
    underlyingCauses: "Nguyên nhân gây bệnh",
    treatmentsRemedies: "Biện pháp xử lý & điều trị",
    preventionMeasures: "Biện pháp phòng ngừa",
    advisoryNote: "Lưu ý nông học:",
    references: "Tài liệu tham khảo",
    noRecommendationTitle: "Chưa có khuyến nghị chuyên gia cho nhãn này",
    noRecommendationDesc: "Nhãn phân loại này hiện chưa có dữ liệu hướng dẫn từ chuyên gia bảo vệ thực vật.",

    // Knowledge Base
    knowledgeBaseTitle: "Cơ sở tri thức bệnh học cây trồng",
    backToList: "Quay lại danh sách",
    emptyKnowledgeTitle: "Cơ sở tri thức trống",
    emptyKnowledgeDesc: "Không tìm thấy dữ liệu bệnh học nào trong cơ sở tri thức.",
    knowledgeDetailError: "Không thể tải thông tin chi tiết về loại bệnh này.",
    knowledgeConnectError: "Không thể kết nối đến cơ sở tri thức.",

    // History
    historyTitle: "Lịch sử chẩn đoán",
    allDiagnoses: "Tất cả chẩn đoán",
    emptyHistoryTitle: "Chưa có lịch sử chẩn đoán",
    emptyHistoryDesc: "Bác chưa có phiên chẩn đoán nào khi đăng nhập. Hãy chụp hoặc tải ảnh lá lên để chẩn đoán, kết quả sẽ tự động lưu tại đây.",
    signInPromptTitle: "Lịch sử chẩn đoán cá nhân",
    signInPromptDesc: "Đăng nhập tài khoản để tự động lưu vết và tra cứu lại các đợt chẩn đoán cũng như phác đồ điều trị bất kỳ lúc nào.",
    signInNow: "Đăng nhập ngay",
    pageOf: "Trang {page} / {totalPages}",
    prevPage: "Trang trước",
    nextPage: "Trang sau",
    historyLoadError: "Không thể tải lịch sử chẩn đoán.",

    // Auth
    authTitle: "Tài khoản AgriLens",
    authDesc: "Đăng nhập để lưu và theo dõi lịch sử chẩn đoán bệnh cây trồng.",
    username: "Tên đăng nhập",
    email: "Địa chỉ Email",
    password: "Mật khẩu",
    usernameHint: "Sử dụng từ 3 ký tự trở lên.",
    emailHint: "Nhập địa chỉ email hợp lệ của bạn.",
    passwordHint: "Sử dụng từ 6 ký tự trở lên.",
    usernameMinError: "Tên đăng nhập phải có ít nhất 3 ký tự.",
    emailInvalidError: "Địa chỉ email không hợp lệ.",
    passwordMinError: "Mật khẩu phải có ít nhất 6 ký tự.",
    processingCredentials: "Đang xử lý thông tin…",
    createAccountAndSignIn: "Tạo tài khoản & Đăng nhập",
    authFailed: "Không thể hoàn thành xác thực. Vui lòng thử lại.",
    authMethodLabel: "Phương thức xác thực",
    signInFormLabel: "Biểu mẫu đăng nhập",
    signUpFormLabel: "Biểu mẫu đăng ký",

    // Errors & Dialog
    systemErrorOccurred: "Đã xảy ra lỗi hệ thống",
    retryAction: "Thử lại",
    closeDialog: "Đóng cửa sổ",
  },
  en: {
    // App & Brand
    brand: "AgriLens",
    appTitle: "AgriLens - Rice & Coffee Leaf Disease Diagnostic System",
    appDescription: "AI-powered leaf disease instance segmentation and expert treatment recommendation system.",
    tagline: "AI-Powered Plant Disease Diagnosis & Treatment",

    // Navigation & Tabs
    diagnosis: "Diagnosis",
    newDiagnosis: "New diagnosis",
    knowledge: "Knowledge Base",
    knowledgeShort: "Knowledge",
    history: "Diagnosis History",
    historyShort: "History",
    signIn: "Sign in",
    signUp: "Sign up",
    signOut: "Sign Out",
    yourAccount: "Your Account",
    collapseNav: "Collapse navigation bar",
    expandNav: "Expand navigation bar",
    loadingAccount: "Loading account status",

    // Header
    switchThemeLight: "Switch to Light Mode",
    switchThemeDark: "Switch to Dark Mode",
    switchLanguage: "Chuyển sang Tiếng Việt (Switch to Vietnamese)",
    langVi: "Tiếng Việt",
    langEn: "English",

    // Home / Hero
    heroTitle: "Start Leaf Diagnosis",
    heroSubtitle: "Upload an image of a diseased crop leaf for real-time AI diagnosis and expert care recommendations.",

    // Image Uploader
    dragDropPrompt: "Drag & drop or click to select leaf image (Coffee / Rice)",
    readyToDiagnose: "Ready for diagnosis",
    attachDevice: "Attach image from device",
    takePhoto: "Take photo with camera",
    startDiagnosisBtn: "Start diagnosis",
    analyzingImage: "Analyzing leaf image...",
    unsupportedFormat: "Only JPEG, PNG, or WEBP image formats are supported.",
    fileTooLarge: "Image file size exceeds the 10 MB limit.",
    removeFile: "Remove file",
    uploadedImage: "Uploaded Image",
    errorPrefix: "Error:",

    // Results
    analysisResults: "Analysis Results",
    topPrediction: "Top Prediction",
    confidenceScores: "Confidence Score",
    modelLatency: "Model Latency",
    crop: "Crop",
    cropRice: "Rice",
    cropCoffee: "Coffee",
    severity: "Severity",
    severityHigh: "High",
    severityMedium: "Medium",
    severityLow: "Low",
    confidenceAlternatives: "Confidence & Alternatives",
    alternativeDiagnoses: "Alternative Diagnoses Considered",
    alternativeDesc: "Confidence scores of top ranked candidates",
    closeMarginWarningTitle: "Close Margin Prediction",
    closeMarginWarningDesc: "The top two predicted classes differ by less than 10%. Recommendation: Compare field symptoms against the Knowledge Base or capture clearer photos for optimal diagnosis.",

    // Expert Recommendation
    expertRecommendation: "Expert Recommendation",
    detailedDescription: "Detailed Description",
    typicalSymptoms: "Typical Symptoms",
    underlyingCauses: "Underlying Causes",
    treatmentsRemedies: "Treatments & Remedies",
    preventionMeasures: "Prevention Measures",
    advisoryNote: "Advisory Note:",
    references: "References",
    noRecommendationTitle: "No expert recommendation available",
    noRecommendationDesc: "This classification label does not yet have supporting advice from plant protection specialists.",

    // Knowledge Base
    knowledgeBaseTitle: "Plant Disease Knowledge Base",
    backToList: "Back to list",
    emptyKnowledgeTitle: "Knowledge Base is empty",
    emptyKnowledgeDesc: "No plant disease records found in the knowledge base.",
    knowledgeDetailError: "Failed to load details for this disease.",
    knowledgeConnectError: "Failed to connect to the knowledge base.",

    // History
    historyTitle: "Diagnosis History",
    allDiagnoses: "All Diagnoses",
    emptyHistoryTitle: "Diagnosis history is empty",
    emptyHistoryDesc: "You have not performed any diagnosis sessions yet while signed in. Try uploading an image to diagnose, and results will automatically appear here.",
    signInPromptTitle: "Personal Diagnosis History",
    signInPromptDesc: "Sign in to your account to automatically track leaf diagnoses and consult expert treatment recommendations anytime.",
    signInNow: "Sign In Now",
    pageOf: "Page {page} of {totalPages}",
    prevPage: "Previous page",
    nextPage: "Next page",
    historyLoadError: "Failed to load diagnosis history.",

    // Auth
    authTitle: "AgriLens Account",
    authDesc: "Sign in to save and review your leaf diagnosis history.",
    username: "Username",
    email: "Email Address",
    password: "Password",
    usernameHint: "Use 3 or more characters.",
    emailHint: "Enter your active email address.",
    passwordHint: "Use 6 or more characters.",
    usernameMinError: "Username must contain at least 3 characters.",
    emailInvalidError: "Invalid email address.",
    passwordMinError: "Password must contain at least 6 characters.",
    processingCredentials: "Processing credentials…",
    createAccountAndSignIn: "Create Account & Sign In",
    authFailed: "Unable to complete authentication. Please try again.",
    authMethodLabel: "Select authentication method",
    signInFormLabel: "Sign in form",
    signUpFormLabel: "Sign up form",

    // Errors & Dialog
    systemErrorOccurred: "System error occurred",
    retryAction: "Retry action",
    closeDialog: "Close dialog",
  },
} as const;

export type TranslationKey = keyof typeof translations.vi;

interface LanguageContextType {
  lang: Language;
  setLang: (lang: Language) => void;
  t: (key: TranslationKey, params?: Record<string, string | number>) => string;
}

const LanguageContext = createContext<LanguageContextType>({
  lang: "vi",
  setLang: () => {},
  t: (key, params) => {
    let text = (translations.vi[key] as string) || (translations.en[key] as string) || key;
    if (params) {
      Object.entries(params).forEach(([pKey, pVal]) => {
        text = text.replace(new RegExp(`\\{${pKey}\\}`, "g"), String(pVal));
      });
    }
    return text;
  },
});

export function LanguageProvider({
  children,
  defaultLang,
}: {
  children: React.ReactNode;
  defaultLang?: Language;
}) {
  const [lang, setLangState] = useState<Language>(defaultLang ?? "vi");

  useEffect(() => {
    if (defaultLang) {
      setLangState(defaultLang);
      document.documentElement.lang = defaultLang;
      return;
    }
    try {
      const stored = localStorage.getItem("agrilens_lang");
      if (stored === "vi" || stored === "en") {
        setLangState(stored);
        document.documentElement.lang = stored;
      } else {
        document.documentElement.lang = "vi";
      }
    } catch {}
  }, [defaultLang]);
  const setLang = (nextLang: Language) => {
    setLangState(nextLang);
    try {
      localStorage.setItem("agrilens_lang", nextLang);
      document.documentElement.lang = nextLang;
    } catch {
      // Ignore localStorage errors
    }
  };

  const t = useMemo(() => {
    return (key: TranslationKey, params?: Record<string, string | number>) => {
      const dict = translations[lang] || translations.vi;
      let text = (dict[key] as string) || (translations.en[key] as string) || key;
      if (params) {
        Object.entries(params).forEach(([pKey, pVal]) => {
          text = text.replace(new RegExp(`\\{${pKey}\\}`, "g"), String(pVal));
        });
      }
      return text;
    };
  }, [lang]);

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  return useContext(LanguageContext);
}
