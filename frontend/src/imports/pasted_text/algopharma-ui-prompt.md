Based on the AlgoPharma architecture and user journey, here's a comprehensive UI prompt:

---

## **AlgoPharma UI Development Prompt**

### **Project Overview**
You are building a **Pharmacovigilance Dashboard** — a real-time signal monitoring platform for healthcare professionals to detect, verify, and report adverse drug reactions (ADRs) from social media and forums. The platform processes NLP-analyzed posts and displays actionable signals with explainable AI reasoning.

### **Tech Stack Recommendation**

**🏆 Best Choice: Next.js 14+ (App Router)**
- Full-stack JavaScript (TypeScript)
- Real-time capabilities (WebSocket support)
- Built-in API layer (optional, for middleware)
- Server-side rendering for SEO
- Excellent for dashboards with Vercel deployment
- Seamless integration with Python FastAPI backend

**Alternative: Vite + React** (if you prefer lightweight SPA)
- Faster dev experience
- Use `vite-plugin-express` for dev proxy to FastAPI

**Framework Stack:**
```
Next.js 14+ (TypeScript)
├── React 18+
├── TailwindCSS (styling)
├── Recharts (data visualization)
├── Tanstack Query (server state)
├── Zustand (client state)
├── Socket.io-client (real-time updates)
└── next-auth (authentication)
```

---

### **Required Pages & Features**

#### **1. 🔐 Authentication Pages**
- **Login Page**
  - Email/password form
  - Secure token storage (httpOnly cookies)
  - Role-based redirect (Analyst → Dashboard, Admin → Settings)
- **Logout** (simple, clears session)

#### **2. 📊 Dashboard (Main Signal View)**
- **Signal Overview Cards**
  - 🔴 Red Signals (urgent, PRR > 5)
  - 🟡 Amber Signals (emerging, PRR > 2)
  - 🟢 Green Signals (baseline, PRR < 2)
  - Total posts analyzed today
  
- **Global Signal Timeline Chart**
  - Line chart: Drug-symptom pairs over 7-day window
  - Highlight anomalies/spikes
  - Clickable to drill down
  
- **Top Drugs at Risk** (table)
  - Columns: Drug Name | Symptom | PRR | ROR | Chi² | Post Count | Status
  - Sortable, filterable
  - Quick action buttons: "View Details" / "Verify"

- **Recent Activity Feed**
  - New signals detected (last 2 hours)
  - Verified signals (marked as CONFIRMED)
  - Timestamp, severity badge

#### **3. 🔍 Signal Details Page** (Core Feature)
- **Header Section**
  - Drug name (large, branded)
  - Symptom(s) identified
  - Signal strength badge (STRONG/MODERATE/WEAK)
  - Stats: PRR, ROR, Chi², Post Count, Confidence %
  
- **Explainability Panel**
  - Why was this flagged? (readable reasoning trace)
  - Gate-by-gate breakdown:
    - ✅ Gate 1: Drug found
    - ✅ Gate 2: Symptom found
    - ✅ Gate 3: Negative sentiment
    - ✅ Gate 4: Not all negated
  
- **Post Feed**
  - Individual posts with:
    - Redacted text (PII masked as [PHONE], [EMAIL], [AADHAAR])
    - Highlighted entities: **Drug** (blue), **Symptom** (red)
    - Sentiment badge (😞 NEGATIVE, 😐 NEUTRAL, 😊 POSITIVE)
    - Confidence score
    - Reply count
  
- **Thread Analysis** (if post has replies)
  - "Corroboration Score" visual (0-100%)
  - Reply breakdown:
    - ✅ Corroborating replies
    - ⚠️ Weakly corroborating
    - ❌ Contradicting
    - ⚪ Neutral
  - Show top supporting replies

- **Action Buttons**
  - ✅ "Confirm Signal" (mark as verified)
  - 📥 "Export to VigiFlow" (PvPI CSV)
  - 🔗 "View Source Posts" (link to Reddit/Twitter)
  - 💬 "Add Internal Note"

#### **4. 📋 Signal Triage/Worklist**
- **Filters**
  - Drug name search
  - Severity (Red/Amber/Green)
  - Date range
  - Status (New / In Review / Confirmed / Exported)
  
- **Worklist Table**
  - Columns: Drug | Symptom | Severity | Posts | PRR | Last Updated | Analyst | Action
  - Bulk actions: "Confirm All", "Export All"
  - Assign to analyst (dropdown)

#### **5. ⚙️ Configuration & Settings** (Admin Page)
- **Crawler Configuration**
  - Add new crawl job
    - Source (Reddit subreddit / Twitter keyword / Forum URL)
    - Frequency (hourly / daily)
    - Language filter
    - Status: Active/Paused/Completed
  - Table of active/past crawls with stats
  
- **PII Redaction Settings**
  - Toggle PII categories to redact (Aadhaar, PAN, Phone, Email, etc.)
  - Test redaction (paste text → preview redacted version)
  
- **Export Settings**
  - Default PvPI export format
  - Regulatory body selection (VigiFlow, NCLT, etc.)
  - Batch export schedule

#### **6. 📊 Analytics & Reporting** (Optional Phase 2)
- **Signal Trends** (30-day view)
  - Top 10 drugs by signal count
  - Top 10 symptoms
  - Regional breakdown (if available)
  
- **Export History**
  - Downloads, dates, regulatory bodies
  - Audit trail of confirmations

#### **7. 👤 User Profile & Notifications**
- **Profile Page**
  - Name, email, role
  - Change password
  
- **Notification Center**
  - New signals alert
  - High-risk drug alerts
  - Crawl completion status
  - Export confirmations

---

### **Component Architecture**

```
app/
├── (auth)/
│   ├── login/
│   └── logout/
├── (dashboard)/
│   ├── layout.tsx          # Sidebar + header
│   ├── page.tsx            # Dashboard overview
│   ├── signals/
│   │   ├── [id]/page.tsx   # Signal details
│   │   ├── worklist/page.tsx
│   │   └── components/
│   │       ├── SignalCard.tsx
│   │       ├── PostFeed.tsx
│   │       ├── ThreadAnalysis.tsx
│   │       ├── ExplainabilityTrace.tsx
│   │       └── ExportButton.tsx
│   ├── settings/
│   │   ├── crawlers/page.tsx
│   │   ├── redaction/page.tsx
│   │   └── export/page.tsx
│   └── analytics/page.tsx
├── api/                    # Optional: proxy to FastAPI
│   ├── signals/route.ts
│   ├── posts/route.ts
│   └── crawlers/route.ts
└── components/
    ├── Navigation.tsx
    ├── Charts/
    │   ├── SignalTimeline.tsx
    │   └── TopDrugsChart.tsx
    └── Shared/
        ├── Badge.tsx
        └── Modal.tsx
```

---

### **Key Integration Points with FastAPI Backend**

**API Endpoints to Consume:**
```
GET /api/signals              # Dashboard overview
GET /api/signals/{id}         # Signal details + reasoning trace
POST /api/signals/{id}/confirm # Mark as verified
POST /api/signals/{id}/export  # Generate & download PvPI CSV
GET /api/posts?signal_id=...  # Fetch posts for signal
GET /api/crawlers             # List active crawlers
POST /api/crawlers            # Create new crawler
GET /api/settings/redaction   # PII redaction config
WebSocket /ws/signals         # Real-time signal alerts
```

**Real-Time Updates:**
- Use Socket.io or native WebSocket to receive:
  - New signal alerts (push RED/AMBER badges)
  - Crawl progress updates
  - Export completion notifications

---

### **UI/UX Design Considerations**

1. **Color Coding** (Consistent with architecture)
   - 🔴 Red: PRR ≥ 5 (urgent)
   - 🟡 Amber: 2 ≤ PRR < 5 (emerging)
   - 🟢 Green: PRR < 2 (baseline)

2. **Explainability First**
   - Every number has a tooltip explaining "Why?"
   - Show gate-by-gate reasoning, not a black box
   - Highlight NER extractions so analysts can verify

3. **Mobile Responsive**
   - Mobile: Stack cards vertically
   - Tablet: 2-column layout
   - Desktop: Full multi-panel view

4. **Dark Mode Support** (Optional)
   - TailwindCSS dark mode for reduced eye strain (analysts work long hours)

5. **Accessibility**
   - WCAG 2.1 AA compliance
   - Keyboard navigation
   - Screen reader friendly

---

### **Implementation Timeline Suggestion**

**Phase 1 (Week 1-2):** Authentication + Dashboard + Signal Details
**Phase 2 (Week 3):** Triage Worklist + Export
**Phase 3 (Week 4):** Settings + Real-time updates
**Phase 4 (Week 5+):** Analytics + Polish

---

### **Starter Command (Next.js)**
```bash
npx create-next-app@latest algopharma-ui --typescript --tailwind --app
cd algopharma-ui
npm install recharts zustand socket.io-client @tanstack/react-query
```

---

This prompt should enable you (or your dev team) to build a production-ready UI. **Next.js is my strongest recommendation** because:
- ✅ Full-stack TypeScript
- ✅ Excellent for dashboards
- ✅ Real-time WebSocket support
- ✅ Built-in image optimization
- ✅ Seamless FastAPI integration
- ✅ Easy deployment (Vercel)

Would you like me to generate the folder structure, starter components, or specific API integration code?