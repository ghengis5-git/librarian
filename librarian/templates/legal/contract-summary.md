---
template_id: contract-summary
display_name: Contract Summary
preset: legal
description: Executive summary of key contract terms, obligations, and risks for commercial or legal contracts
suggested_tags: [contract, summary, legal]
suggested_folder: legal/
typical_cross_refs: [legal-review, nda-tracker]
recommended_with: [legal-review]
requires: []
sections:
  - Contract Overview
  - Parties
  - Key Terms
  - Financial Terms
  - Term & Termination
  - Liability & Indemnification
  - IP Provisions
  - Compliance Obligations
  - Notable Risks
  - Recommended Modifications
---

# Contract Summary — {{title}}

**Date:** {{date}}  
**Author:** {{author}}  
**Version:** {{version}}  
**Classification:** {{classification}}  
**Contract Type:** *[e.g., Service Agreement, Supply Agreement, License Agreement, NDA]*

---

## Contract Overview

### Executive Summary

*[Provide a 2-3 paragraph overview of the contract. Include the nature of the relationship, primary deliverables or obligations, commercial purpose, and total contract value or scope.]*

### Contract Metadata

| Property | Value |
|----------|-------|
| **Contract Title** | *[Official name]* |
| **Effective Date** | *[Date]* |
| **Execution Date** | *[Date signed]* |
| **Signed By** | *[Signatory names/titles]* |
| **Counterparty Lead** | *[Primary contact]* |
| **Internal Lead** | *[Your company lead]* |
| **File Location** | *[Storage path/repository]* |

---

## Parties

### Our Organization

**Legal Entity:** *[Entity name]*  
**Address:** *[Address]*  
**Contact:** *[Primary contact name, email, phone]*  
**Role:** *[Provider/Customer/Licensor/Licensee]*

### Counterparty

**Legal Entity:** *[Counterparty name]*  
**Address:** *[Address]*  
**Contact:** *[Primary contact name, email, phone]*  
**Role:** *[Provider/Customer/Licensor/Licensee]*

### Affiliated Entities

*[Note any subsidiaries, parent companies, or related entities that have rights or obligations under the contract.]*

---

## Key Terms

### Business Scope

| Element | Description |
|---------|-------------|
| **Deliverables** | *[Primary product/service being provided]* |
| **Service Level** | *[Performance metrics, uptime, availability]* |
| **Quality Standards** | *[Industry standards, specifications, acceptance criteria]* |
| **Scope Limitations** | *[What is excluded or out of scope]* |

### Performance Obligations

1. *[Obligation 1: [Description with timeline if applicable]]*
2. *[Obligation 2: [Description with timeline if applicable]]*
3. *[Obligation 3: [Description with timeline if applicable]]*

### Acceptance & Inspection

*[Describe acceptance procedures, inspection rights, rejection criteria, and cure periods.]*

---

## Financial Terms

### Pricing & Payment

| Component | Amount | Payment Schedule | Notes |
|-----------|--------|------------------|-------|
| *[Base Fee/Cost]* | *[$X]* | *[Monthly/Quarterly/Annual]* | *[Description]* |
| *[Usage-Based Fees]* | *[Variable]* | *[As incurred]* | *[Unit/metric]* |
| *[Reimbursable Expenses]* | *[Cap or %]* | *[Monthly/As invoiced]* | *[Included categories]* |
| **Total Contract Value** | **$X** | **Over X years** | **[If fixed term]** |

### Payment Terms

- **Invoice Frequency:** *[Monthly/Quarterly/Upon delivery]*
- **Payment Due Date:** *[Net 30/Net 60/Upon receipt]*
- **Payment Method:** *[Wire transfer/ACH/Check]*
- **Late Fees:** *[% per month or fixed amount if applicable]*
- **Taxes:** *[Responsibility for sales tax, VAT, withholding taxes]*

### Cost Escalation

*[Describe any price increase mechanisms: annual CPI adjustment, cost-plus pass-through, step increases, or renegotiation rights.]*

---

## Term & Termination

### Initial Term

- **Start Date:** *[Effective date]*
- **Initial Term:** *[X years/months]*
- **Renewal:** *[Auto-renewal, opt-in, or negotiated extension]*
- **Termination Deadline:** *[Notice required by X days before expiration]*

### Termination Rights

| Trigger | Notice Period | Termination Type | Consequences |
|---------|---------------|------------------|--------------|
| *[Breach]* | *[X days]* | For Cause | *[Remedies, penalties]* |
| *[Insolvency]* | *[Immediate]* | For Cause | *[Termination effective immediately]* |
| *[Change of Control]* | *[X days]* | Conditional | *[Triggering party rights]* |
| *[Convenience]* | *[X days]* | Without Cause | *[Penalties or restrictions]* |

### Post-Termination Obligations

*[Describe wind-down procedures, transition services, return of materials, deletion of data, survival clauses, and any ongoing payment or performance obligations.]*

{% if "hipaa" in compliance %}
### BAA Termination Requirements

- **Destruction of PHI:** *[Data destruction within X days of termination]*
- **Audit Rights:** *[Certification of PHI destruction required]*
- **Survival Clauses:** *[Confidentiality and security obligations survive termination]*
{% endif %}

---

## Liability & Indemnification

### Limitation of Liability

| Category | Cap |
|----------|-----|
| **Indirect/Consequential Damages** | *[Excluded / Capped at $X]*|
| **Total Liability Cap** | *[$X or X months of fees]* |
| **Exceptions to Cap** | *[IP infringement, confidentiality breaches, indemnification, death/injury]* |

### Insurance Requirements

*[Specify required insurance types and minimums: general liability, professional liability, cybersecurity liability, errors & omissions.]*

### Indemnification

| Indemnifying Party | Indemnifying Against | Scope |
|-------------------|-------------------|-------|
| *[Party A]* | *[Party B]* | *[IP infringement, breach of contract, negligence]* |
| *[Party B]* | *[Party A]* | *[IP infringement, breach of contract, data misuse]* |

### Indemnification Procedures

*[Describe notice requirements, control of defense, settlement authority, and cooperation obligations.]*

---

## IP Provisions

### Ownership

| IP Category | Owner | Rights |
|-------------|-------|--------|
| **Pre-existing IP** | *[Original creator]* | *[License scope / Ownership]* |
| **Developed IP** | *[Party]* | *[Ownership / License grant]* |
| **Work Product** | *[Party]* | *[All rights / Limited license]* |
| **Third-party Materials** | *[Licensor]* | *[Pass-through license terms]* |

### License Grants

*[Describe grants of rights: scope (worldwide/territory), exclusivity, sublicense rights, field of use, duration.]*

### IP Infringement

*[Address responsibility for third-party IP claims, indemnification, and modifications if IP is challenged.]*

### Confidential Information

- **Definition:** *[Trade secrets, proprietary data, specifications, business plans]*
- **Term:** *[X years post-termination]*
- **Permitted Disclosures:** *[Attorneys, accountants, necessary employees]*
- **Return/Destruction:** *[Upon termination or request]*

---

## Compliance Obligations

### General Compliance

*[Describe any compliance with laws, regulations, industry standards, or contractual audit rights.]*

{% if "hipaa" in compliance %}
### Healthcare Compliance (HIPAA)

- **BAA Status:** *[Executed / Pending / Not required]*
- **PHI Access:** *[Permitted/Not permitted]*
- **Security Safeguards:** *[Required controls per HIPAA Security Rule]*
- **Breach Notification:** *[Timeline and procedures]*
- **Audit & Compliance:** *[Right to audit compliance with HIPAA Security Rule]*
{% endif %}

{% if "sec_finra" in compliance %}
### Securities & Financial Compliance

- **SOX Compliance:** *[Internal controls and financial reporting requirements]*
- **FINRA Rules:** *[Anti-corruption, suitability, best execution obligations]*
- **Record Retention:** *[Minimum 6-7 years for regulatory records]*
- **Regulatory Notifications:** *[Any required SEC/FINRA notifications]*
{% endif %}

### Data Protection

*[Describe data handling, processing, security requirements, and applicable privacy regulations (GDPR, CCPA, etc.).]*

---

## Notable Risks

### High-Risk Provisions

| Risk | Impact | Mitigation |
|------|--------|-----------|
| *[Risk 1]* | *[Financial/Operational/Legal]* | *[Current safeguard or recommendation]* |
| *[Risk 2]* | *[Financial/Operational/Legal]* | *[Current safeguard or recommendation]* |
| *[Risk 3]* | *[Financial/Operational/Legal]* | *[Current safeguard or recommendation]* |

### Ambiguous Language

*[Identify any vague, undefined, or potentially conflicting provisions that could lead to disputes.]*

### Performance Dependencies

*[Note any critical assumptions or dependencies on third parties or external factors that could impact performance.]*

---

## Recommended Modifications

### Priority 1: Critical Changes (Before Signing)

1. *[Modification 1: [Justification]]*
2. *[Modification 2: [Justification]]*
3. *[Modification 3: [Justification]]*

### Priority 2: Important Changes (First Amendment)

1. *[Modification: [Justification]]*
2. *[Modification: [Justification]]*

### Priority 3: Nice-to-Have Changes (Future Amendment)

1. *[Modification: [Justification]]*
2. *[Modification: [Justification]]*

### Template Language Suggestions

**Limitation of Liability:**
```
Each party's total cumulative liability under this Agreement shall not exceed 
the total fees paid in the twelve (12) months preceding the claim, except for 
each party's indemnification obligations, breaches of confidentiality, and 
willful misconduct.
```

**Termination for Convenience:**
```
Either party may terminate this Agreement without cause upon sixty (60) days' 
written notice. Termination fees shall [describe any wind-down costs, transition 
services, or early termination penalties].
```

---

## Action Items

| Action | Responsible Party | Priority | Due Date | Status |
|--------|------------------|----------|----------|--------|
| *[Negotiate amendment]* | *[Legal/Business]* | High | *[Date]* | Pending |
| *[Obtain executive sign-off]* | *[Executive]* | High | *[Date]* | Pending |
| *[Store executed copy]* | *[Admin]* | Medium | *[Date]* | Pending |
| *[Calendar renewal deadline]* | *[Admin]* | Medium | *[Date]* | Pending |
| *[Share with stakeholders]* | *[Owner]* | Medium | *[Date]* | Pending |

---

*Document generated by librarian v{{librarian_version}} from template \`contract-summary\`.*
