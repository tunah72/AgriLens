# Frontend — Plant Disease Diagnostic Web Application

Web user interface for diagnosing rice and coffee leaf diseases, built on Next.js 15 (App Router), React 19, and Tailwind CSS.

---

## 1. Key Features

1. **Foliar Disease Diagnosis**:
   - Upload leaf photographs via drag-and-drop or file selection.
   - Native mobile camera integration for in-field captures.
   - Client-side image validation (up to 10 MB, JPEG, PNG, or WEBP formats).

2. **Trust Signals & Model Interpretability**:
   - Prominent confidence score presentation with animated progress indicators.
   - Visual comparison of alternative candidates via Top-K probability distribution charts.
   - Automatic close-margin alert when top-ranked predictions differ by less than 10%.

3. **Expert Agricultural Knowledge Base**:
   - Direct lookup of all supported rice and coffee disease conditions.
   - Detailed symptomology, underlying causes, agronomic treatments, prevention measures, and literature references.

4. **Personal Diagnosis History**:
   - Secure user authentication with JWT bearer tokens.
   - Synchronized historical diagnosis records with paginated inspection cards and image previews.

---

## 2. Getting Started

### 1. Configure Environment Variables
Copy the example configuration:
```bash
cp .env.example .env.local
```
Set `NEXT_PUBLIC_API_BASE_URL` to your backend endpoint (default: `http://localhost:8000/api/v1`).

### 2. Install Dependencies
```bash
npm install
```

### 3. Start Development Server
```bash
npm run dev
```
Open `http://localhost:3000` in your browser.

### 4. Production Build
```bash
npm run build
npm run start
```

### 5. Automated Tests
Run Vitest unit and integration test suites:
```bash
npm test -- --run
```

---

## 3. Technology Stack

- **Framework**: Next.js 15 (App Router)
- **UI Library**: React 19, Tailwind CSS
- **Primitives**: Radix UI (Dialog, DropdownMenu)
- **Icons**: Lucide React
- **Animation**: Framer Motion
- **Testing**: Vitest, React Testing Library
