# AgriLens Frontend — Diagnostic Web Application

Modern, accessible web user interface for foliar leaf disease instance segmentation diagnosis, agronomic advisory, and audit history, built with **Next.js 15 (App Router)**, **React 19**, and **Tailwind CSS**.

---

## 1. Key Features

1. **Interactive Foliar Instance Segmentation Visualizer**:
   - **Mask / Original Image Toggle**: Seamlessly switch between the raw photograph and the YOLO26-seg color-coded segmentation mask with bounding box overlays.
   - **Damage Metrics**: Real-time display of detected lesion counts and lesion surface area percentage over total leaf area.
   - **Lesion Polygon Cards**: Clear breakdown of localized infection sites and individual confidence scores.

2. **Bilingual Agronomic Advisory (Tiếng Việt & English)**:
   - Instant language switching (VI / EN) with zero page reloads.
   - Dedicated localized disease monographs for all 7 foliar diseases (Rice Leaf Blast, Brown Spot, Hispa; Coffee Leaf Miner, Powdery Mildew, Rust, Algal Leaf Spot) and healthy controls.
   - Calibrated diagnostic confidence notes advising in-field re-inspection when model certainty is below 60%.

3. **Modern Ergonomic UI & Bento Grid Layout**:
   - Responsive 12-column Bento Grid layout optimized for both desktop inspection and field mobile usage.
   - Collapsible navigation sidebar with custom brand typography and iconography.
   - Drag-and-drop leaf uploader with native smartphone camera capture.
   - Client-side validation enforcing file format (JPEG, PNG, WEBP) and size boundaries (up to 10 MB).

4. **Trust Signals & Model Interpretability**:
   - Prominent confidence score presentation with animated progress indicators.
   - Top-3 candidate distribution bars comparing alternative candidate classifications.
   - Automated close-margin alert badge when top-ranked predictions differ by less than 10%.
   - **Domain Guard & Out-of-Distribution Warning Card**: Prominent amber alert banner rendered whenever the backend flags an uploaded image as non-leaf, document, or certificate (`is_valid_leaf: false`), gracefully suppressing irrelevant agronomic treatment cards.

5. **Zero-Exposure Image Serving & Proxy Resolution**:
   - Intelligent URL resolution via `resolveImageUrl()` utility that routes image fetching through the backend proxy (`/api/v1/images/...`) or relative paths, avoiding browser CORS blocks or direct MinIO S3 port exposures.

6. **Personal Diagnosis Audit History**:
   - Secure user authentication with JWT bearer tokens.
   - Paginated historical cards preserving uploaded images, annotated masks, and agronomic recommendations.
---

## 2. Getting Started

### 1. Configure Environment Variables
Copy the example configuration:
```bash
cp .env.example .env.local
```

Set `NEXT_PUBLIC_API_BASE_URL` to your backend endpoint:
- **Local development**: `http://localhost:8000/api/v1`
- **Production with Reverse Proxy / Ingress (Recommended)**: `/api/v1` (Default in `frontend/Dockerfile` for seamless same-origin routing without CORS or hardcoded IPs).
- **Standalone AWS EC2 deployment**: `http://<EC2_PUBLIC_IP>:8000/api/v1` or `https://<YOUR_DOMAIN>/api/v1`

> **Important Deployment Note**: In Next.js, `NEXT_PUBLIC_*` environment variables are baked into client JavaScript bundles at **build time**. Using the default relative path `/api/v1` allows the frontend container to run behind any domain or ingress controller (Nginx, Traefik, AWS ALB) without needing image rebuilds.
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
Run Vitest unit and component test suites:
```bash
npm test -- --run
```

---

## 3. Technology Stack

- **Framework**: Next.js 15 (App Router, Standalone Output)
- **UI Library**: React 19, Tailwind CSS
- **Primitives**: Radix UI (Dialog, DropdownMenu)
- **Icons**: Lucide React
- **Animation**: Framer Motion
- **Testing**: Vitest, React Testing Library
