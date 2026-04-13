import { useState, useMemo } from "react";

// ── Registry data (extracted from REGISTRY.yaml 2026-04-11) ──
const PROJECT_CONFIG = {
  project_name: "Project PRISM",
  naming_convention: "descriptive-name-YYYYMMDD-VX.Y.ext",
  default_classification: "CONFIDENTIAL",
  staleness_threshold_days: 90,
  docs_path: "docs/",
  archive_path: "docs/archive/",
};

const REGISTRY_META = {
  total_documents: 36,
  active: 26,
  superseded: 10,
  naming_violations: 25,
  pending_cross_reference_updates: 0,
  last_audit: "2026-04-11",
  // total_on_disk aggregates across docs/, docs/archive/, docs/diagrams/,
  // operator/phase-specs/ — renamed from locations_on_disk 2026-04-11 for clarity.
  total_on_disk: 36,
  locations_in_chat: 17,
  locations_in_cowork: 36,
  in_docs_archive: 8,
};

const DOCUMENTS = [
  { filename: "project_prism_strategic_plan-v1_2.docx", title: "Strategic Plan", version: "1.2", date: "2026-04-11", status: "active", classification: "PERSONAL / INTERNAL USE ONLY", format: "docx", category: "Strategic & Planning", disk: true, chat: true, cowork: true, description: "Master strategic plan covering vision, nine-module architecture, phased build plan, deployment options, and capability roadmap", tags: ["planning", "architecture", "strategic-plan"] },
  { filename: "project_prism_project_plan-v2_2.docx", title: "Project Plan", version: "2.2", date: "2026-04-11", status: "active", classification: "PERSONAL / INTERNAL USE ONLY", format: "docx", category: "Strategic & Planning", disk: true, chat: true, cowork: true, description: "Detailed project plan with timeline, data pipeline, phase deliverables, infrastructure scaling triggers, risk register, and solo build operating cadence", tags: ["planning", "project-plan", "timeline"] },
  { filename: "project_prism_technical_architecture-v1_2.docx", title: "Technical Architecture", version: "1.2", date: "2026-04-11", status: "active", classification: "PERSONAL / INTERNAL USE ONLY", format: "docx", category: "Technical Architecture", disk: true, chat: true, cowork: true, description: "Three-tier architecture (ML Stack, Custom Skills, Claude API), complete repo map, all nine module specifications, Claude API integration points, and build vs buy analysis", tags: ["architecture", "technical-spec", "modules"] },
  { filename: "project_prism_infrastructure-v1_2.docx", title: "Infrastructure Requirements", version: "1.2", date: "2026-04-11", status: "active", classification: "PERSONAL / INTERNAL USE ONLY", format: "docx", category: "Technical Architecture", disk: true, chat: true, cowork: true, description: "Hardware requirements, software stack by phase, accounts and services, network and security architecture, exo cluster specification, and day 1 setup checklist", tags: ["infrastructure", "hardware", "security"] },
  { filename: "project_prism_addendum-v1_3.docx", title: "Strategic Plan Addendum — Sub-Modules A1-A8", version: "1.3", date: "2026-03-01", status: "active", classification: "PERSONAL / INTERNAL USE ONLY", format: "docx", category: "Addenda & Supplements", disk: true, chat: true, cowork: true, description: "Research-backed analytical sub-modules including Dark Triad Indicator Score, profile confidence tiers, and scientific basis for text-based personality profiling", tags: ["addendum", "sub-modules", "dark-triad"] },
  { filename: "prism-architectural-evolution-addendum-20260411-V1.0.docx", title: "Architectural Evolution Addendum", version: "1.0", date: "2026-04-11", status: "active", classification: "PERSONAL / INTERNAL USE ONLY", format: "docx", category: "Addenda & Supplements", disk: true, chat: true, cowork: true, description: "Three architectural evolution decisions plus LLM/RLM hybrid role architecture with three operational roles", tags: ["addendum", "architecture", "LLM integration"] },
  { filename: "prism-scientific-foundations-20260411-V1.1.docx", title: "Scientific Foundations & Methodology Validation", version: "1.1", date: "2026-04-11", status: "active", classification: "CONFIDENTIAL", format: "docx", category: "Scientific & Ethics", disk: true, chat: true, cowork: true, description: "Peer-reviewed research basis for all analytical modules — 26+ citations with PRISM implementation mapping, calibration data, and adversarial vulnerability disclosure", tags: ["scientific", "calibration", "peer-review"] },
  { filename: "ETHICS_AND_CONSTRAINTS-v1_2.docx", title: "Ethics & Constraints", version: "1.2", date: "2026-04-11", status: "active", classification: "PERSONAL / INTERNAL USE ONLY", format: "docx", category: "Scientific & Ethics", disk: true, chat: true, cowork: true, description: "Scoring philosophy, neurodivergence bias mitigations, prohibited uses, data privacy protocols, and adversarial vulnerability disclosure", tags: ["ethics", "constraints", "privacy"] },
  { filename: "prism-mutual-nda-20260410-V1.0.docx", title: "Mutual Non-Disclosure Agreement", version: "1.0", date: "2026-04-10", status: "active", classification: "ATTORNEY-CLIENT PRIVILEGED", format: "docx", category: "Legal & IP", disk: true, chat: true, cowork: true, description: "Mutual NDA template for PRISM project collaborators", tags: ["legal", "agreement", "nda"] },
  { filename: "prism-nda-ip-assignment-20260410-V1.0.docx", title: "NDA & IP Assignment Agreement", version: "1.0", date: "2026-04-10", status: "active", classification: "ATTORNEY-CLIENT PRIVILEGED", format: "docx", category: "Legal & IP", disk: true, chat: true, cowork: true, description: "Combined NDA, IP assignment, non-compete, and work product assignment for PRISM project contributors", tags: ["legal", "agreement", "ip-assignment"] },
  { filename: "project_prism_patent_analysis-v1_1.docx", title: "Patent Landscape Analysis", version: "1.1", date: "2026-04-10", status: "active", classification: "ATTORNEY-CLIENT PRIVILEGED", format: "docx", category: "Legal & IP", disk: true, chat: true, cowork: true, description: "Prior art analysis across behavioral analysis patents, PRISM's freedom-to-operate assessment, and IP positioning recommendations", tags: ["legal", "ip", "patent"] },
  { filename: "prism_ip_protection_strategy-v1_1.docx", title: "IP Protection Strategy", version: "1.1", date: "2026-04-10", status: "active", classification: "ATTORNEY-CLIENT PRIVILEGED", format: "docx", category: "Legal & IP", disk: true, chat: true, cowork: true, description: "Patent filing strategy with 6 provisional specifications, trade secret layer definitions, and filing budget estimates", tags: ["legal", "ip", "patent", "trade-secret"] },
  { filename: "prism-phase3-commands-20260403.md", title: "Phase 3 Claude Code Commands", version: "1.0", date: "2026-04-03", status: "active", classification: "PERSONAL / INTERNAL USE ONLY", format: "md", category: "Operational & Technical", disk: true, chat: false, cowork: true, description: "Paste-ready Claude Code command blocks for Phase 3 housekeeping", tags: ["operational", "phase-3", "claude-code"] },
  { filename: "prism-phase4-ai-detection-20260403.md", title: "Phase 4 AI Detection Commit Spec", version: "1.0", date: "2026-04-03", status: "active", classification: "PERSONAL / INTERNAL USE ONLY", format: "md", category: "Operational & Technical", disk: true, chat: false, cowork: true, description: "Paste-ready Claude Code commit blocks for three-layer AI assistance detection module", tags: ["operational", "ai-detection", "phase-4"] },
  { filename: "prism-phase4-audio-pipeline-20260403.md", title: "Phase 4 Audio Pipeline Commit Specs", version: "1.0", date: "2026-04-03", status: "active", classification: "PERSONAL / INTERNAL USE ONLY", format: "md", category: "Operational & Technical", disk: true, chat: true, cowork: true, description: "Nine-commit specification for the audio pipeline", tags: ["operational", "audio", "phase-4"] },
  { filename: "prism-session-integration-commit-spec-20260410.md", title: "Session Integration Commit Spec", version: "1.0", date: "2026-04-10", status: "active", classification: "PERSONAL / INTERNAL USE ONLY", format: "md", category: "Operational & Technical", disk: true, chat: false, cowork: true, description: "Infrastructure, schema, and configuration commit spec for April 10 planning-session outputs", tags: ["operational", "session-integration", "phase-4"] },
  { filename: "prism_meeting_intelligence.docx", title: "Meeting Intelligence Module", version: "1.0", date: "2026-04-10", status: "active", classification: "CONFIDENTIAL", format: "docx", category: "Operational & Technical", disk: true, chat: true, cowork: true, description: "Physical behavioral analysis, environmental influence toolkit, temporal correlation engine", tags: ["technical-spec", "meeting-intelligence", "phase-4"] },
  { filename: "prism-architectural-diagrams-20260411-V1.0.html", title: "Architectural Diagrams — Interactive Report", version: "1.0", date: "2026-04-11", status: "active", classification: "CONFIDENTIAL", format: "html", category: "Diagrams & Reports", disk: true, chat: true, cowork: true, description: "Interactive HTML report with three diagrams: hybrid architecture data flow, nine module profiles, and three LLM role scenarios", tags: ["diagram", "architecture"] },
  { filename: "doc-librarian-dashboard-20260411-V1.1.html", title: "Document Librarian Dashboard", version: "1.1", date: "2026-04-11", status: "superseded", classification: "PERSONAL / INTERNAL USE ONLY", format: "html", category: "Diagrams & Reports", disk: true, chat: false, cowork: true, description: "Interactive HTML dashboard rendering REGISTRY.yaml state (superseded by V2.0)", tags: ["dashboard", "governance", "registry"] },
  { filename: "AI_DETECTION_HANDOFF.md", title: "AI Detection Handoff", version: "1.0", date: "2026-04-03", status: "active", classification: "CONFIDENTIAL", format: "md", category: "Technical Specs", disk: true, chat: false, cowork: true, description: "Phase 4 handoff document for the AI assistance detection module", tags: ["handoff", "ai-detection", "phase-4"] },
  { filename: "COMPETITIVE_LANDSCAPE.docx", title: "Competitive Landscape Analysis", version: "1.0", date: "2026-04-10", status: "active", classification: "CONFIDENTIAL", format: "docx", category: "Technical Specs", disk: true, chat: false, cowork: true, description: "Competitive landscape survey of behavioral profiling and deception-detection products", tags: ["competitive", "market-analysis"] },
  { filename: "prism-toolchain-setup-guide-20260411.md", title: "Toolchain Setup Guide", version: "1.0", date: "2026-04-11", status: "active", classification: "PERSONAL / INTERNAL USE ONLY", format: "md", category: "Operational & Technical", disk: true, chat: true, cowork: true, description: "Developer setup instructions for PRISM: Python/venv, model caches, MPS verification", tags: ["operational", "setup", "toolchain"] },
  { filename: "prism_a9_temporal_behavior_analysis.docx", title: "A9 Temporal Behavior Analysis", version: "1.0", date: "2026-04-10", status: "active", classification: "CONFIDENTIAL", format: "docx", category: "Technical Specs", disk: true, chat: false, cowork: true, description: "Specification for sub-module A9: chronotype profile, response latency baseline, latency deviation events", tags: ["technical-spec", "temporal", "a9"] },
  { filename: "prism_advanced_analytical_capabilities.docx", title: "Advanced Analytical Capabilities (C1–C5)", version: "1.0", date: "2026-04-10", status: "active", classification: "CONFIDENTIAL", format: "docx", category: "Technical Specs", disk: true, chat: false, cowork: true, description: "Specification for capabilities C1 Network Graph through C5 Linguistic Accommodation Tracking", tags: ["technical-spec", "capabilities", "c1-c5"] },
  { filename: "prism_influence_playbook.docx", title: "Influence Playbook Specification", version: "1.0", date: "2026-04-10", status: "active", classification: "CONFIDENTIAL", format: "docx", category: "Technical Specs", disk: true, chat: false, cowork: true, description: "Six-lever influence playbook with 10 scenario templates and detect/deploy/prohibited classification", tags: ["technical-spec", "influence-playbook"] },
  { filename: "project_prism_personal_artifact_analysis.docx", title: "Personal Artifact Analysis (PAA)", version: "1.0", date: "2026-04-10", status: "active", classification: "CONFIDENTIAL", format: "docx", category: "Technical Specs", disk: true, chat: false, cowork: true, description: "Specification for Channel 7: Personal Artifacts capture, scoring rules, password/naming patterns", tags: ["technical-spec", "channel-7", "paa"] },
  { filename: "prism_document_update_spec.docx", title: "Document Update Specification", version: "1.0", date: "2026-04-10", status: "superseded", classification: "PERSONAL / INTERNAL USE ONLY", format: "docx", category: "Operational & Technical", disk: true, chat: false, cowork: true, description: "Superseded by prism-doc-librarian skill", tags: ["governance", "legacy"] },
];

// ── Naming violation data ──
const NAMING_VIOLATIONS = [
  { filename: "ETHICS_AND_CONSTRAINTS.docx", issue: "Uppercase name, no date, no version — legacy undated file" },
  { filename: "ETHICS_AND_CONSTRAINTS-v1_2.docx", issue: "Uppercase name, legacy underscore version" },
  { filename: "prism_meeting_intelligence.docx", issue: "Missing date and version in filename" },
  { filename: "AI_DETECTION_HANDOFF.md", issue: "Uppercase name, no date, no version" },
  { filename: "COMPETITIVE_LANDSCAPE.docx", issue: "Uppercase name, no date, no version" },
  { filename: "DOCUMENT_REGISTRY.md", issue: "Uppercase name, no date, no version (legacy, superseded)" },
  { filename: "prism_a9_temporal_behavior_analysis.docx", issue: "Underscore separators, no date, no version" },
  { filename: "prism_advanced_analytical_capabilities.docx", issue: "Underscore separators, no date, no version" },
  { filename: "prism_document_update_spec.docx", issue: "Underscore separators, no date, no version (legacy, superseded)" },
  { filename: "prism_influence_playbook.docx", issue: "Underscore separators, no date, no version" },
  { filename: "prism_ip_protection_strategy-v1_1.docx", issue: "Underscore separators, no date, legacy underscore version" },
  { filename: "project_prism_addendum-v1_3.docx", issue: "Underscore separators, no date, legacy underscore version" },
  { filename: "project_prism_infrastructure-v1_2.docx", issue: "Underscore separators, no date, legacy underscore version" },
  { filename: "project_prism_patent_analysis-v1_1.docx", issue: "Underscore separators, no date, legacy underscore version" },
  { filename: "project_prism_personal_artifact_analysis.docx", issue: "Underscore separators, no date, no version" },
  { filename: "project_prism_project_plan-v2_2.docx", issue: "Underscore separators, no date, legacy underscore version" },
  { filename: "project_prism_strategic_plan-v1_2.docx", issue: "Underscore separators, no date, legacy underscore version" },
  { filename: "project_prism_technical_architecture-v1_2.docx", issue: "Underscore separators, no date, legacy underscore version" },
  { filename: "prism-toolchain-setup-guide-20260411.md", issue: "Has date but missing version suffix (-V1.0)" },
];

// ── Classification badge colors ──
const CLASS_COLORS = {
  "CONFIDENTIAL": { bg: "#7f1d1d", text: "#fca5a5", border: "#991b1b" },
  "ATTORNEY-CLIENT PRIVILEGED": { bg: "#713f12", text: "#fde68a", border: "#854d0e" },
  "PERSONAL / INTERNAL USE ONLY": { bg: "#14532d", text: "#86efac", border: "#166534" },
};

const STATUS_COLORS = {
  active: { bg: "#064e3b", text: "#6ee7b7" },
  superseded: { bg: "#44403c", text: "#a8a29e" },
  draft: { bg: "#1e3a5f", text: "#7dd3fc" },
};

const FORMAT_ICONS = { docx: "W", md: "M", html: "H", pdf: "P", pptx: "S" };

// ── Component ──
export default function LibrarianDashboard() {
  const [view, setView] = useState("overview"); // overview | documents | violations | preview
  const [statusFilter, setStatusFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [sortBy, setSortBy] = useState("title");

  const categories = useMemo(() => [...new Set(DOCUMENTS.map(d => d.category))], []);

  const filtered = useMemo(() => {
    let docs = DOCUMENTS;
    if (statusFilter !== "all") docs = docs.filter(d => d.status === statusFilter);
    if (categoryFilter !== "all") docs = docs.filter(d => d.category === categoryFilter);
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      docs = docs.filter(d =>
        d.title.toLowerCase().includes(q) ||
        d.filename.toLowerCase().includes(q) ||
        d.description.toLowerCase().includes(q) ||
        d.tags.some(t => t.includes(q))
      );
    }
    return [...docs].sort((a, b) => {
      if (sortBy === "title") return a.title.localeCompare(b.title);
      if (sortBy === "date") return b.date.localeCompare(a.date);
      if (sortBy === "version") return b.version.localeCompare(a.version);
      return 0;
    });
  }, [statusFilter, categoryFilter, searchTerm, sortBy]);

  const activeCount = DOCUMENTS.filter(d => d.status === "active").length;
  const supersededCount = DOCUMENTS.filter(d => d.status === "superseded").length;
  const chatCount = DOCUMENTS.filter(d => d.chat).length;
  const diskOnlyCount = DOCUMENTS.filter(d => d.disk && !d.chat).length;

  const font = "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace";
  const displayFont = "'DM Sans', 'Inter', system-ui, sans-serif";

  const S = {
    root: { fontFamily: font, fontSize: 12, color: "#c9d1d9", background: "transparent", minHeight: "100vh", padding: "20px 24px", lineHeight: 1.6 },
    header: { marginBottom: 28 },
    projectName: { fontFamily: displayFont, fontSize: 11, fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase", color: "#8b949e", marginBottom: 4 },
    h1: { fontFamily: displayFont, fontSize: 22, fontWeight: 700, color: "#f0f6fc", margin: 0, letterSpacing: "-0.02em" },
    subtitle: { fontSize: 11, color: "#6e7681", marginTop: 4 },
    kpiRow: { display: "flex", gap: 12, marginBottom: 24, flexWrap: "wrap" },
    kpi: (color) => ({ flex: "1 1 120px", padding: "14px 16px", borderRadius: 8, border: `1px solid ${color}22`, background: `${color}08` }),
    kpiValue: (color) => ({ fontFamily: displayFont, fontSize: 28, fontWeight: 700, color, lineHeight: 1 }),
    kpiLabel: { fontSize: 10, color: "#6e7681", marginTop: 4, textTransform: "uppercase", letterSpacing: "0.06em" },
    nav: { display: "flex", gap: 2, marginBottom: 20, borderBottom: "1px solid #21262d", paddingBottom: 8 },
    navBtn: (active) => ({ background: active ? "#161b22" : "transparent", color: active ? "#f0f6fc" : "#6e7681", border: active ? "1px solid #30363d" : "1px solid transparent", borderRadius: 6, padding: "6px 14px", fontSize: 11, fontWeight: active ? 600 : 400, cursor: "pointer", fontFamily: font, transition: "all 0.15s" }),
    filterRow: { display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap", alignItems: "center" },
    select: { background: "#0d1117", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: 6, padding: "5px 10px", fontSize: 11, fontFamily: font, cursor: "pointer" },
    search: { background: "#0d1117", color: "#c9d1d9", border: "1px solid #30363d", borderRadius: 6, padding: "5px 12px", fontSize: 11, fontFamily: font, flex: "1 1 200px", outline: "none" },
    table: { width: "100%", borderCollapse: "collapse" },
    th: { textAlign: "left", padding: "8px 10px", fontSize: 10, color: "#6e7681", borderBottom: "1px solid #21262d", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 600, cursor: "pointer" },
    td: { padding: "10px 10px", borderBottom: "1px solid #161b22", verticalAlign: "top" },
    docTitle: { fontWeight: 600, color: "#58a6ff", cursor: "pointer", fontSize: 12 },
    badge: (colors) => ({ display: "inline-block", padding: "2px 8px", borderRadius: 4, fontSize: 9, fontWeight: 600, letterSpacing: "0.04em", background: colors.bg, color: colors.text, border: `1px solid ${colors.border || colors.bg}` }),
    locationDot: (on) => ({ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: on ? "#3fb950" : "#21262d", marginRight: 6, border: on ? "1px solid #2ea043" : "1px solid #30363d" }),
    previewPane: { border: "1px solid #30363d", borderRadius: 8, background: "#0d1117", padding: 24, marginTop: 16 },
    previewHeader: { display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20, flexWrap: "wrap", gap: 12 },
    previewTitle: { fontFamily: displayFont, fontSize: 18, fontWeight: 700, color: "#f0f6fc" },
    closeBtn: { background: "#21262d", color: "#8b949e", border: "1px solid #30363d", borderRadius: 6, padding: "4px 12px", fontSize: 11, cursor: "pointer", fontFamily: font },
    metaGrid: { display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12, marginBottom: 20 },
    metaItem: { padding: "10px 14px", background: "#161b22", borderRadius: 6, border: "1px solid #21262d" },
    metaLabel: { fontSize: 9, color: "#6e7681", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 2 },
    metaValue: { fontSize: 12, color: "#c9d1d9", fontWeight: 500 },
    tagPill: { display: "inline-block", padding: "2px 8px", borderRadius: 10, fontSize: 10, background: "#1c2128", color: "#8b949e", border: "1px solid #21262d", marginRight: 4, marginBottom: 4 },
    violationRow: { padding: "10px 14px", borderBottom: "1px solid #161b22", display: "flex", gap: 12, alignItems: "flex-start" },
    violationFile: { fontWeight: 600, color: "#f97316", fontSize: 11, minWidth: 280, flexShrink: 0, wordBreak: "break-all" },
    violationIssue: { fontSize: 11, color: "#8b949e" },
    locationMatrix: { display: "grid", gridTemplateColumns: "1fr auto auto auto", gap: "0", fontSize: 11 },
    matrixHeader: { padding: "6px 16px", background: "#161b22", fontWeight: 600, color: "#6e7681", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.05em", borderBottom: "1px solid #21262d" },
    matrixCell: { padding: "6px 16px", borderBottom: "1px solid #0d1117", textAlign: "center" },
  };

  const openPreview = (doc) => { setSelectedDoc(doc); setView("preview"); };
  const closePreview = () => { setSelectedDoc(null); setView("documents"); };

  return (
    <div style={S.root}>
      {/* Header */}
      <div style={S.header}>
        <div style={S.projectName}>{PROJECT_CONFIG.project_name}</div>
        <h1 style={S.h1}>Document Librarian</h1>
        <div style={S.subtitle}>Registry audit: {REGISTRY_META.last_audit} · {REGISTRY_META.total_documents} documents tracked · Naming convention: {PROJECT_CONFIG.naming_convention}</div>
      </div>

      {/* KPIs */}
      <div style={S.kpiRow}>
        <div style={S.kpi("#3fb950")}>
          <div style={S.kpiValue("#3fb950")}>{activeCount}</div>
          <div style={S.kpiLabel}>Active</div>
        </div>
        <div style={S.kpi("#8b949e")}>
          <div style={S.kpiValue("#8b949e")}>{supersededCount}</div>
          <div style={S.kpiLabel}>Superseded</div>
        </div>
        <div style={S.kpi("#58a6ff")}>
          <div style={S.kpiValue("#58a6ff")}>{chatCount}</div>
          <div style={S.kpiLabel}>In Chat</div>
        </div>
        <div style={S.kpi("#f97316")}>
          <div style={S.kpiValue("#f97316")}>{REGISTRY_META.naming_violations}</div>
          <div style={S.kpiLabel}>Naming Violations</div>
        </div>
        <div style={S.kpi("#a371f7")}>
          <div style={S.kpiValue("#a371f7")}>{REGISTRY_META.pending_cross_reference_updates}</div>
          <div style={S.kpiLabel}>Pending Xrefs</div>
        </div>
      </div>

      {/* Navigation */}
      <div style={S.nav}>
        {["overview", "documents", "violations"].map(v => (
          <button key={v} style={S.navBtn(view === v || (view === "preview" && v === "documents"))} onClick={() => { setView(v); setSelectedDoc(null); }}>
            {v === "overview" ? "Overview" : v === "documents" ? "Documents" : "Naming Violations"}
          </button>
        ))}
      </div>

      {/* ── Overview ── */}
      {view === "overview" && (
        <div>
          <div style={{ marginBottom: 24 }}>
            <h2 style={{ fontFamily: displayFont, fontSize: 14, fontWeight: 600, color: "#f0f6fc", marginBottom: 12 }}>Location Matrix</h2>
            <div style={{ border: "1px solid #21262d", borderRadius: 8, overflow: "hidden" }}>
              <div style={S.locationMatrix}>
                <div style={S.matrixHeader}>Document</div>
                <div style={S.matrixHeader}>Disk</div>
                <div style={S.matrixHeader}>Chat</div>
                <div style={S.matrixHeader}>Cowork</div>
                {DOCUMENTS.filter(d => d.status === "active").sort((a,b) => a.title.localeCompare(b.title)).map((d, i) => (
                  [
                    <div key={`t${i}`} style={{ ...S.matrixCell, textAlign: "left", color: "#c9d1d9", fontWeight: 500, background: i % 2 === 0 ? "transparent" : "#0d1117" }}>{d.title}</div>,
                    <div key={`d${i}`} style={{ ...S.matrixCell, background: i % 2 === 0 ? "transparent" : "#0d1117" }}><span style={S.locationDot(d.disk)} /></div>,
                    <div key={`c${i}`} style={{ ...S.matrixCell, background: i % 2 === 0 ? "transparent" : "#0d1117" }}><span style={S.locationDot(d.chat)} /></div>,
                    <div key={`w${i}`} style={{ ...S.matrixCell, background: i % 2 === 0 ? "transparent" : "#0d1117" }}><span style={S.locationDot(d.cowork)} /></div>,
                  ]
                ))}
              </div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div style={{ border: "1px solid #21262d", borderRadius: 8, padding: 16 }}>
              <h3 style={{ fontFamily: displayFont, fontSize: 13, fontWeight: 600, color: "#f0f6fc", marginBottom: 10 }}>By Classification</h3>
              {Object.entries(CLASS_COLORS).map(([cls, colors]) => {
                const count = DOCUMENTS.filter(d => d.classification === cls && d.status === "active").length;
                return (
                  <div key={cls} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #161b22" }}>
                    <span style={S.badge(colors)}>{cls}</span>
                    <span style={{ color: "#8b949e", fontWeight: 600 }}>{count}</span>
                  </div>
                );
              })}
            </div>
            <div style={{ border: "1px solid #21262d", borderRadius: 8, padding: 16 }}>
              <h3 style={{ fontFamily: displayFont, fontSize: 13, fontWeight: 600, color: "#f0f6fc", marginBottom: 10 }}>By Category</h3>
              {categories.map(cat => {
                const count = DOCUMENTS.filter(d => d.category === cat && d.status === "active").length;
                return (
                  <div key={cat} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #161b22" }}>
                    <span style={{ color: "#c9d1d9" }}>{cat}</span>
                    <span style={{ color: "#8b949e", fontWeight: 600 }}>{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* ── Documents ── */}
      {(view === "documents" || view === "preview") && !selectedDoc && (
        <div>
          <div style={S.filterRow}>
            <select style={S.select} value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
              <option value="all">All statuses</option>
              <option value="active">Active</option>
              <option value="superseded">Superseded</option>
            </select>
            <select style={S.select} value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
              <option value="all">All categories</option>
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <select style={S.select} value={sortBy} onChange={e => setSortBy(e.target.value)}>
              <option value="title">Sort: Title</option>
              <option value="date">Sort: Date</option>
              <option value="version">Sort: Version</option>
            </select>
            <input style={S.search} placeholder="Search title, filename, description, or tag..." value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
          </div>
          <div style={{ fontSize: 11, color: "#6e7681", marginBottom: 12 }}>{filtered.length} document{filtered.length !== 1 ? "s" : ""} shown</div>
          <table style={S.table}>
            <thead>
              <tr>
                <th style={S.th}>Document</th>
                <th style={{ ...S.th, width: 60 }}>Ver</th>
                <th style={{ ...S.th, width: 90 }}>Date</th>
                <th style={{ ...S.th, width: 70 }}>Status</th>
                <th style={{ ...S.th, width: 100 }}>Locations</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((d, i) => (
                <tr key={i} style={{ background: i % 2 === 0 ? "transparent" : "#0d1117" }}>
                  <td style={S.td}>
                    <div style={S.docTitle} onClick={() => openPreview(d)}>
                      <span style={{ display: "inline-block", width: 18, height: 18, borderRadius: 4, background: "#161b22", border: "1px solid #30363d", textAlign: "center", lineHeight: "18px", fontSize: 9, fontWeight: 700, color: "#8b949e", marginRight: 8, verticalAlign: "middle" }}>{FORMAT_ICONS[d.format] || "?"}</span>
                      {d.title}
                    </div>
                    <div style={{ fontSize: 10, color: "#6e7681", marginTop: 2, marginLeft: 26 }}>{d.filename}</div>
                  </td>
                  <td style={{ ...S.td, fontWeight: 600, color: "#c9d1d9" }}>V{d.version}</td>
                  <td style={{ ...S.td, color: "#8b949e" }}>{d.date}</td>
                  <td style={S.td}><span style={S.badge(STATUS_COLORS[d.status] || STATUS_COLORS.active)}>{d.status}</span></td>
                  <td style={S.td}>
                    <span style={S.locationDot(d.disk)} title="Disk" />
                    <span style={S.locationDot(d.chat)} title="Chat" />
                    <span style={S.locationDot(d.cowork)} title="Cowork" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Preview Pane ── */}
      {view === "preview" && selectedDoc && (
        <div style={S.previewPane}>
          <div style={S.previewHeader}>
            <div>
              <div style={S.previewTitle}>{selectedDoc.title}</div>
              <div style={{ fontSize: 11, color: "#6e7681", marginTop: 4 }}>{selectedDoc.filename}</div>
            </div>
            <button style={S.closeBtn} onClick={closePreview}>Back to list</button>
          </div>

          <div style={S.metaGrid}>
            <div style={S.metaItem}>
              <div style={S.metaLabel}>Version</div>
              <div style={S.metaValue}>V{selectedDoc.version}</div>
            </div>
            <div style={S.metaItem}>
              <div style={S.metaLabel}>Date</div>
              <div style={S.metaValue}>{selectedDoc.date}</div>
            </div>
            <div style={S.metaItem}>
              <div style={S.metaLabel}>Status</div>
              <div style={S.metaValue}><span style={S.badge(STATUS_COLORS[selectedDoc.status])}>{selectedDoc.status}</span></div>
            </div>
            <div style={S.metaItem}>
              <div style={S.metaLabel}>Format</div>
              <div style={S.metaValue}>.{selectedDoc.format}</div>
            </div>
            <div style={S.metaItem}>
              <div style={S.metaLabel}>Classification</div>
              <div style={S.metaValue}><span style={S.badge(CLASS_COLORS[selectedDoc.classification] || { bg: "#21262d", text: "#8b949e" })}>{selectedDoc.classification}</span></div>
            </div>
            <div style={S.metaItem}>
              <div style={S.metaLabel}>Category</div>
              <div style={S.metaValue}>{selectedDoc.category}</div>
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <div style={{ ...S.metaLabel, marginBottom: 6 }}>Description</div>
            <div style={{ fontSize: 12, color: "#c9d1d9", lineHeight: 1.7, padding: "12px 16px", background: "#161b22", borderRadius: 6, border: "1px solid #21262d" }}>
              {selectedDoc.description}
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <div style={{ ...S.metaLabel, marginBottom: 6 }}>Locations</div>
            <div style={{ display: "flex", gap: 16, padding: "12px 16px", background: "#161b22", borderRadius: 6, border: "1px solid #21262d" }}>
              <span><span style={S.locationDot(selectedDoc.disk)} /> Disk</span>
              <span><span style={S.locationDot(selectedDoc.chat)} /> Chat</span>
              <span><span style={S.locationDot(selectedDoc.cowork)} /> Cowork</span>
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <div style={{ ...S.metaLabel, marginBottom: 6 }}>Tags</div>
            <div>{selectedDoc.tags.map(t => <span key={t} style={S.tagPill}>{t}</span>)}</div>
          </div>

          <div style={{ padding: "16px 20px", background: "#161b22", borderRadius: 6, border: "1px solid #21262d" }}>
            <div style={{ ...S.metaLabel, marginBottom: 8 }}>Preview</div>
            {selectedDoc.format === "docx" ? (
              <div style={{ color: "#8b949e", fontSize: 11, lineHeight: 1.7 }}>
                <p style={{ marginBottom: 8 }}>Word documents cannot be rendered inline. To view this document:</p>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <span style={{ padding: "4px 12px", borderRadius: 4, background: "#21262d", color: "#58a6ff", fontSize: 11, fontWeight: 500 }}>
                    ~/projects/prism/{PROJECT_CONFIG.docs_path}{selectedDoc.filename}
                  </span>
                </div>
                <p style={{ marginTop: 8, fontSize: 10, color: "#6e7681" }}>Open in Word, Preview.app, or use Cowork for inline access.</p>
              </div>
            ) : selectedDoc.format === "html" ? (
              <div style={{ color: "#8b949e", fontSize: 11, lineHeight: 1.7 }}>
                <p style={{ marginBottom: 8 }}>HTML file — open in any browser:</p>
                <span style={{ padding: "4px 12px", borderRadius: 4, background: "#21262d", color: "#58a6ff", fontSize: 11, fontWeight: 500 }}>
                  open ~/projects/prism/{PROJECT_CONFIG.docs_path}diagrams/{selectedDoc.filename}
                </span>
              </div>
            ) : selectedDoc.format === "md" ? (
              <div style={{ color: "#8b949e", fontSize: 11, lineHeight: 1.7 }}>
                <p style={{ marginBottom: 8 }}>Markdown file — view in any editor or renderer:</p>
                <span style={{ padding: "4px 12px", borderRadius: 4, background: "#21262d", color: "#58a6ff", fontSize: 11, fontWeight: 500 }}>
                  cat ~/projects/prism/{selectedDoc.filename}
                </span>
              </div>
            ) : (
              <div style={{ color: "#6e7681" }}>Preview not available for .{selectedDoc.format} format</div>
            )}
          </div>
        </div>
      )}

      {/* ── Naming Violations ── */}
      {view === "violations" && (
        <div>
          <div style={{ marginBottom: 12, fontSize: 11, color: "#6e7681" }}>
            {NAMING_VIOLATIONS.length} files do not comply with <code style={{ background: "#161b22", padding: "1px 6px", borderRadius: 3, color: "#f97316" }}>{PROJECT_CONFIG.naming_convention}</code>. Legacy files transition on next version bump per the registry transition rule.
          </div>
          <div style={{ border: "1px solid #21262d", borderRadius: 8, overflow: "hidden" }}>
            {NAMING_VIOLATIONS.map((v, i) => (
              <div key={i} style={{ ...S.violationRow, background: i % 2 === 0 ? "transparent" : "#0d1117" }}>
                <div style={S.violationFile}>{v.filename}</div>
                <div style={S.violationIssue}>{v.issue}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={{ borderTop: "1px solid #21262d", marginTop: 28, paddingTop: 12, fontSize: 10, color: "#30363d", textAlign: "center" }}>
        Document Librarian Dashboard V2.0 · Registry data from {REGISTRY_META.last_audit} · {PROJECT_CONFIG.project_name}
      </div>
    </div>
  );
}
