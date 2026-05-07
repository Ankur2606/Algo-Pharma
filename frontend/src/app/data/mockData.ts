export type Severity = "RED" | "AMBER" | "GREEN";
export type SignalStatus = "NEW" | "IN_REVIEW" | "CONFIRMED" | "EXPORTED";

export interface Signal {
  id: string;
  drug: string;
  symptom: string;
  severity: Severity;
  status: SignalStatus;
  prr: number;
  ror: number;
  chi2: number;
  postCount: number;
  confidence: number;
  lastUpdated: string;
  analyst: string;
  source: string;
}

export interface Post {
  id: string;
  signalId: string;
  text: string;
  highlightedText: {
    segments: { text: string; type: "drug" | "symptom" | "normal" | "redacted" }[];
  };
  sentiment: "NEGATIVE" | "NEUTRAL" | "POSITIVE";
  confidence: number;
  replyCount: number;
  platform: string;
  timestamp: string;
  corroborationScore: number;
}

export interface CrawlerJob {
  id: string;
  source: string;
  type: "reddit" | "twitter" | "forum";
  keyword: string;
  frequency: "hourly" | "daily" | "weekly";
  language: string;
  status: "ACTIVE" | "PAUSED" | "COMPLETED" | "FAILED";
  postsCollected: number;
  lastRun: string;
}

export const signals: Signal[] = [
  {
    id: "SIG-001",
    drug: "Ibuprofen",
    symptom: "Gastrointestinal Bleeding",
    severity: "RED",
    status: "NEW",
    prr: 7.2,
    ror: 8.1,
    chi2: 42.3,
    postCount: 318,
    confidence: 94,
    lastUpdated: "2026-05-04T08:30:00Z",
    analyst: "Dr. Priya Sharma",
    source: "Reddit",
  },
  {
    id: "SIG-002",
    drug: "Metformin",
    symptom: "Lactic Acidosis",
    severity: "RED",
    status: "IN_REVIEW",
    prr: 6.8,
    ror: 7.4,
    chi2: 38.9,
    postCount: 241,
    confidence: 91,
    lastUpdated: "2026-05-04T07:15:00Z",
    analyst: "Dr. Amit Verma",
    source: "Twitter",
  },
  {
    id: "SIG-003",
    drug: "Atorvastatin",
    symptom: "Myopathy",
    severity: "AMBER",
    status: "IN_REVIEW",
    prr: 3.4,
    ror: 3.9,
    chi2: 18.2,
    postCount: 187,
    confidence: 82,
    lastUpdated: "2026-05-03T22:45:00Z",
    analyst: "Dr. Priya Sharma",
    source: "MedForum",
  },
  {
    id: "SIG-004",
    drug: "Amlodipine",
    symptom: "Peripheral Edema",
    severity: "AMBER",
    status: "CONFIRMED",
    prr: 2.9,
    ror: 3.2,
    chi2: 14.7,
    postCount: 152,
    confidence: 78,
    lastUpdated: "2026-05-03T18:20:00Z",
    analyst: "Dr. Rahul Nair",
    source: "Reddit",
  },
  {
    id: "SIG-005",
    drug: "Pantoprazole",
    symptom: "Hypomagnesemia",
    severity: "AMBER",
    status: "NEW",
    prr: 2.3,
    ror: 2.6,
    chi2: 11.4,
    postCount: 98,
    confidence: 72,
    lastUpdated: "2026-05-04T09:00:00Z",
    analyst: "Unassigned",
    source: "Twitter",
  },
  {
    id: "SIG-006",
    drug: "Cetirizine",
    symptom: "Drowsiness",
    severity: "GREEN",
    status: "CONFIRMED",
    prr: 1.4,
    ror: 1.5,
    chi2: 4.2,
    postCount: 76,
    confidence: 65,
    lastUpdated: "2026-05-02T14:00:00Z",
    analyst: "Dr. Rahul Nair",
    source: "MedForum",
  },
  {
    id: "SIG-007",
    drug: "Lisinopril",
    symptom: "Dry Cough",
    severity: "GREEN",
    status: "EXPORTED",
    prr: 1.1,
    ror: 1.2,
    chi2: 2.8,
    postCount: 54,
    confidence: 61,
    lastUpdated: "2026-05-01T10:30:00Z",
    analyst: "Dr. Amit Verma",
    source: "Reddit",
  },
  {
    id: "SIG-008",
    drug: "Sertraline",
    symptom: "Suicidal Ideation",
    severity: "RED",
    status: "IN_REVIEW",
    prr: 9.1,
    ror: 10.3,
    chi2: 58.7,
    postCount: 412,
    confidence: 97,
    lastUpdated: "2026-05-04T10:10:00Z",
    analyst: "Dr. Priya Sharma",
    source: "Twitter",
  },
];

export const posts: Post[] = [
  {
    id: "POST-001",
    signalId: "SIG-001",
    text: "Been taking ibuprofen for a week and now having severe stomach pain and noticed blood in stool. This is really scary.",
    highlightedText: {
      segments: [
        { text: "Been taking ", type: "normal" },
        { text: "ibuprofen", type: "drug" },
        { text: " for a week and now having severe ", type: "normal" },
        { text: "stomach pain", type: "symptom" },
        { text: " and noticed ", type: "normal" },
        { text: "blood in stool", type: "symptom" },
        { text: ". This is really scary.", type: "normal" },
      ],
    },
    sentiment: "NEGATIVE",
    confidence: 96,
    replyCount: 14,
    platform: "Reddit",
    timestamp: "2026-05-04T06:22:00Z",
    corroborationScore: 87,
  },
  {
    id: "POST-002",
    signalId: "SIG-001",
    text: "My doctor prescribed ibuprofen 400mg. After 3 days I started experiencing GI bleeding. Contact me at [PHONE] for more details.",
    highlightedText: {
      segments: [
        { text: "My doctor prescribed ", type: "normal" },
        { text: "ibuprofen", type: "drug" },
        { text: " 400mg. After 3 days I started experiencing ", type: "normal" },
        { text: "GI bleeding", type: "symptom" },
        { text: ". Contact me at ", type: "normal" },
        { text: "[PHONE]", type: "redacted" },
        { text: " for more details.", type: "normal" },
      ],
    },
    sentiment: "NEGATIVE",
    confidence: 93,
    replyCount: 7,
    platform: "Twitter",
    timestamp: "2026-05-04T07:45:00Z",
    corroborationScore: 72,
  },
  {
    id: "POST-003",
    signalId: "SIG-001",
    text: "Ibuprofen has been fine for me honestly. No bleeding, no problems after 2 weeks of use.",
    highlightedText: {
      segments: [
        { text: "Ibuprofen", type: "drug" },
        { text: " has been fine for me honestly. No ", type: "normal" },
        { text: "bleeding", type: "symptom" },
        { text: ", no problems after 2 weeks of use.", type: "normal" },
      ],
    },
    sentiment: "POSITIVE",
    confidence: 88,
    replyCount: 3,
    platform: "MedForum",
    timestamp: "2026-05-03T20:11:00Z",
    corroborationScore: 15,
  },
];

export const timelineData = [
  { date: "Apr 28", ibuprofen: 12, metformin: 8, sertraline: 5, atorvastatin: 3 },
  { date: "Apr 29", ibuprofen: 19, metformin: 11, sertraline: 9, atorvastatin: 4 },
  { date: "Apr 30", ibuprofen: 24, metformin: 14, sertraline: 12, atorvastatin: 6 },
  { date: "May 01", ibuprofen: 18, metformin: 17, sertraline: 14, atorvastatin: 5 },
  { date: "May 02", ibuprofen: 31, metformin: 22, sertraline: 18, atorvastatin: 8 },
  { date: "May 03", ibuprofen: 28, metformin: 19, sertraline: 22, atorvastatin: 7 },
  { date: "May 04", ibuprofen: 42, metformin: 26, sertraline: 31, atorvastatin: 11 },
];

export const crawlerJobs: CrawlerJob[] = [
  {
    id: "CRW-001",
    source: "r/medicine",
    type: "reddit",
    keyword: "adverse drug reaction",
    frequency: "hourly",
    language: "en",
    status: "ACTIVE",
    postsCollected: 12847,
    lastRun: "2026-05-04T10:00:00Z",
  },
  {
    id: "CRW-002",
    source: "Twitter/X",
    type: "twitter",
    keyword: "#sideeffects #drugwarning",
    frequency: "hourly",
    language: "en",
    status: "ACTIVE",
    postsCollected: 34521,
    lastRun: "2026-05-04T10:00:00Z",
  },
  {
    id: "CRW-003",
    source: "r/ibuprofen",
    type: "reddit",
    keyword: "pain bleeding stomach",
    frequency: "daily",
    language: "en",
    status: "ACTIVE",
    postsCollected: 5432,
    lastRun: "2026-05-04T00:00:00Z",
  },
  {
    id: "CRW-004",
    source: "MedHelp Forum",
    type: "forum",
    keyword: "metformin lactic",
    frequency: "daily",
    language: "en",
    status: "PAUSED",
    postsCollected: 2109,
    lastRun: "2026-05-02T00:00:00Z",
  },
  {
    id: "CRW-005",
    source: "Twitter/X",
    type: "twitter",
    keyword: "sertraline depression side",
    frequency: "hourly",
    language: "en",
    status: "ACTIVE",
    postsCollected: 18234,
    lastRun: "2026-05-04T10:00:00Z",
  },
];

export const activityFeed = [
  {
    id: 1,
    type: "NEW_SIGNAL",
    message: "New RED signal detected: Sertraline → Suicidal Ideation (PRR: 9.1)",
    timestamp: "2026-05-04T10:10:00Z",
    severity: "RED" as Severity,
  },
  {
    id: 2,
    type: "NEW_SIGNAL",
    message: "New RED signal detected: Ibuprofen → GI Bleeding (PRR: 7.2)",
    timestamp: "2026-05-04T08:30:00Z",
    severity: "RED" as Severity,
  },
  {
    id: 3,
    type: "CONFIRMED",
    message: "Signal CONFIRMED: Amlodipine → Peripheral Edema by Dr. Rahul Nair",
    timestamp: "2026-05-03T18:20:00Z",
    severity: "AMBER" as Severity,
  },
  {
    id: 4,
    type: "NEW_SIGNAL",
    message: "New AMBER signal detected: Pantoprazole → Hypomagnesemia (PRR: 2.3)",
    timestamp: "2026-05-04T09:00:00Z",
    severity: "AMBER" as Severity,
  },
  {
    id: 5,
    type: "EXPORTED",
    message: "Signal EXPORTED: Lisinopril → Dry Cough to VigiFlow (PvPI CSV)",
    timestamp: "2026-05-01T10:30:00Z",
    severity: "GREEN" as Severity,
  },
];
