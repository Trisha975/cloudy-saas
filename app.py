"""Cloudy Grounding Studio - clickable prototype (Streamlit). All data is fictional sample data."""
import streamlit as st

st.set_page_config(page_title="Cloudy Grounding Studio", layout="wide")

# ---------- Sample data ----------
def initial_sources():
    return [
        dict(n="Oracle Fusion – POs", c="ERP", p="Custom", cx="High", acl="High", fresh="2h", st="REVIEW",
             why=["Mechanism 3 | Schema 3 | ACL 3 (score 5/6)", "EU data-residency tag", "Confidence 0.84"],
             risk=["Persona leak possible between buyers and approvers", "API v24B deprecation in 14 days"],
             ev=["[1] Oracle API scopes export – 12 Oct", "[2] Data group map – 10 Oct", "[3] Similar approved case S07 (golden set)"]),
        dict(n="SharePoint – Policies", c="Content", p="Native", cx="Low", acl="Low", fresh="12m", st="APPROVED",
             why=["Native connector, full ACL sync", "10 entities, flat schema", "Confidence 0.97"],
             risk=["None above threshold"], ev=["[1] Connector docs", "[2] Tenant ACL sync log"]),
        dict(n="Workday HCM", c="HR", p="Custom", cx="High", acl="High", fresh="1d", st="BLOCKED",
             why=["PATH: Custom connector", "Complexity High (score 5/6)", "Confidence 0.86"],
             risk=["Integration runs as a single system user", "HR admins and managers share one view",
                   "Residency: EU-West tag on 38% of records", "Recommendation: per-user OAuth + group mapping"],
             ev=["[1] Workday API scopes export – 12 Oct", "[2] Okta group map – 10 Oct",
                 "[3] Tenant policy: least privilege = ON", "[4] Similar approved case S07 (golden set)"]),
        dict(n="Notion Workspace", c="Collab", p="MCP/API", cx="Low", acl="Medium", fresh="6h", st="APPROVED",
             why=["REST API, per-user OAuth", "Low schema depth"], risk=["Quota at 92% of limit – throttle plan needed"],
             ev=["[1] API docs", "[2] Rate-limit log"]),
        dict(n="NetSuite – Vendor bills", c="ERP", p="MCP/API", cx="Medium", acl="Medium", fresh="3h", st="REVIEW",
             why=["REST API, role-based access", "60 entities, depth 2"], risk=["Tight rate limit during month-end close"],
             ev=["[1] API docs", "[2] Role export"]),
        dict(n="Snowflake – FIN_DW", c="Data", p="Custom", cx="High", acl="High", fresh="45m", st="REVIEW",
             why=["Row-access policies (nested)", "Residency constraint"], risk=["Row-level rules must be mirrored per persona"],
             ev=["[1] Row policy export", "[2] Residency tag report"]),
        dict(n="Teams – Channels", c="Collab", p="Native", cx="Low", acl="Low", fresh="5m", st="APPROVED",
             why=["Native, full ACL sync"], risk=["None above threshold"], ev=["[1] Connector docs"]),
    ]

DRIFT0 = [
    dict(sev="High", src="Oracle Fusion AP", what="API v24B deprecation announced (14 days)", act="Re-classify"),
    dict(sev="High", src="Workday HCM", what="Admin widened integration scope", act="Open review"),
    dict(sev="Medium", src="Notion", what="Quota at 92% of limit", act="Plan throttling"),
    dict(sev="Medium", src="Ramp (new SaaS)", what="Unmapped app, 31 users via SSO", act="Start discovery"),
]
QUESTIONS = {
    "PO status and policy check": ["Oracle Fusion – POs", "SharePoint – Policies"],
    "Headcount for approver escalation": ["Workday HCM", "Teams – Channels"],
    "Open vendor bills this month": ["NetSuite – Vendor bills", "Notion Workspace"],
}
ICON = {"APPROVED": "🟢", "REVIEW": "🟠", "BLOCKED": "🔴", "High": "🔴", "Medium": "🟠", "Low": "🟢"}

if "src" not in st.session_state:
    st.session_state.src = initial_sources()
    st.session_state.drift = list(DRIFT0)
    st.session_state.sel = 2
    st.session_state.pol = {
        "Least privilege for sensitive data": True,
        "Two-person approval for High ACL risk": True,
        "Block connections that move EU data out of region": True,
        "Daily re-scan of all sources": True,
    }
S = st.session_state

def count(status): return sum(x["st"] == status for x in S.src)

# ---------- Sidebar ----------
st.sidebar.title("Cloudy Grounding Studio")
st.sidebar.selectbox("Tenant", ["Acme Corp", "Globex Ltd"])
page = st.sidebar.radio("Go to", ["Overview", "Source inventory", "Review queue", "Drift alerts", "Policies", "Agent preview"])
st.sidebar.caption(f"{count('REVIEW')} waiting for review · {len(S.drift)} drift alerts")

# ---------- Screens ----------
if page == "Overview":
    st.header("Grounding health")
    st.caption("Which sources the agent can safely use right now.")
    a, b, c, d = st.columns(4)
    a.metric("Approved and fresh", f"{count('APPROVED')}/{len(S.src)}")
    b.metric("Waiting for review", count("REVIEW"))
    c.metric("Blocked by policy", count("BLOCKED"))
    d.metric("Open drift alerts", len(S.drift))
    st.subheader("Integration path mix")
    mix = {p: sum(x["p"] == p for x in S.src) for p in ["Native", "MCP/API", "Custom"]}
    st.bar_chart(mix)
    st.info("Try it: Source inventory → pick a source → Review queue → approve or reject → check Agent preview.")

elif page == "Source inventory":
    st.header(f"Source inventory ({len(S.src)})")
    c1, c2 = st.columns([4, 1])
    q = c1.text_input("Search source / system", label_visibility="collapsed", placeholder="Search source / system…")
    if c2.button("+ Run discovery", type="primary", use_container_width=True):
        if not any(x["n"] == "Ramp – Spend" for x in S.src):
            S.src.append(dict(n="Ramp – Spend", c="Finance", p="MCP/API", cx="Medium", acl="Medium", fresh="new", st="REVIEW",
                              why=["REST API, OAuth available", "Newly discovered via SSO logs"],
                              risk=["Spend data is sensitive; confirm role mapping"], ev=["[1] SSO app catalogue", "[2] API docs"]))
            S.drift = [d for d in S.drift if d["src"] != "Ramp (new SaaS)"]
            st.success("Discovery finished: 1 new source added to Review.")
        else:
            st.info("Discovery finished: nothing new.")
    rows = [(i, x) for i, x in enumerate(S.src) if q.lower() in (x["n"] + x["c"] + x["p"]).lower()]
    h = st.columns([3, 1.3, 1.3, 1.3, 1.3, 1, 1.5, 1.2])
    for col, t in zip(h, ["Source", "Category", "Path", "Complexity", "ACL risk", "Fresh", "Status", ""]):
        col.markdown(f"**{t}**")
    for i, x in rows:
        r = st.columns([3, 1.3, 1.3, 1.3, 1.3, 1, 1.5, 1.2])
        r[0].write(x["n"]); r[1].write(x["c"]); r[2].write(x["p"])
        r[3].write(f"{ICON[x['cx']]} {x['cx']}"); r[4].write(f"{ICON[x['acl']]} {x['acl']}")
        r[5].write(x["fresh"]); r[6].write(f"{ICON[x['st']]} {x['st']}")
        if r[7].button("Review", key=f"rv{i}"):
            S.sel = i
            st.toast(f"Selected {x['n']}. Open 'Review queue' in the sidebar.")

elif page == "Review queue":
    x = S.src[S.sel]
    names = [s["n"] for s in S.src]
    S.sel = names.index(st.selectbox("Source under review", names, index=S.sel))
    x = S.src[S.sel]
    st.header(x["n"])
    st.caption("AI proposal with evidence. A person makes the final call.")
    a, b = st.columns(2)
    with a:
        st.subheader("Classification (AI proposal)")
        st.write(f"**Path:** {x['p']} connector  \n**Complexity:** {ICON[x['cx']]} {x['cx']}")
        for w in x["why"]: st.markdown(f"- {w}")
    with b:
        st.subheader(f"ACL risk analysis ({ICON[x['acl']]} {x['acl']})")
        for w in x["risk"]: st.markdown(f"- {w}")
    a, b = st.columns(2)
    with a:
        st.subheader("Evidence (citations)")
        for w in x["ev"]: st.markdown(f"- {w}")
    with b:
        st.subheader("Decision")
        st.write(f"Current status: {ICON[x['st']]} **{x['st']}**")
        needs_two = x["acl"] == "High" and S.pol["Two-person approval for High ACL risk"]
        second = st.checkbox("Security reviewer co-approves (two-person rule)") if needs_two else True
        c1, c2, c3 = st.columns(3)
        if c1.button("Approve & start connector", type="primary"):
            if second: x["st"] = "APPROVED"; st.rerun()
            else: st.error("High ACL risk: a second (security) reviewer must co-approve.")
        if c2.button("Override / send back"): x["st"] = "REVIEW"; st.rerun()
        if c3.button("Reject"): x["st"] = "BLOCKED"; st.rerun()

elif page == "Drift alerts":
    st.header("Drift alerts")
    st.caption("Changes that re-trigger classification so decisions never go stale.")
    if not S.drift:
        st.success("No open alerts. New drift will appear here.")
    for i, d in enumerate(list(S.drift)):
        a, b, c, e = st.columns([1, 2, 4, 2])
        a.write(f"{ICON[d['sev']]} {d['sev']}"); b.write(d["src"]); c.write(d["what"])
        if e.button(d["act"], key=f"d{i}"):
            if d["act"] == "Open review":
                S.sel = next(k for k, s in enumerate(S.src) if s["n"].startswith("Workday"))
            S.drift.remove(d)
            st.toast(f"Action started: {d['act']}")
            st.rerun()

elif page == "Policies":
    st.header("Policies")
    st.caption("Rules the AI cannot override. Reviewers can edit trigger rules.")
    for k in S.pol:
        S.pol[k] = st.toggle(k, value=S.pol[k])

else:
    st.header("Agent preview")
    st.caption("What the end user sees. The grounding gate checks every source behind an answer.")
    qn = st.selectbox("Ask the agent", list(QUESTIONS))
    ok = 0
    for n in QUESTIONS[qn]:
        s = next(z for z in S.src if z["n"] == n)
        good = s["st"] == "APPROVED"; ok += good
        (st.success if good else st.error)(f"{n} – " + (f"approved, fresh {s['fresh']} ago" if good else f"{s['st']}: not queried"))
    if ok == len(QUESTIONS[qn]): st.write("Answer shown with sources and freshness badges.")
    elif ok: st.warning("Partial answer shown. One source was excluded by the grounding gate, and the user is told which.")
    else: st.error("No answer given. The agent says the data is not yet approved and offers to notify the owner.")
