# Northstar AI

### AI-Powered Real Estate Sales Concierge

Northstar AI is a conversational AI sales concierge built for the **Huvo AI Forward Deployed Engineer assignment**.
 
It simulates an AI sales representative for **Northstar Homes**, helping prospective customers explore property options, share requirements, get qualified, handle objections, and schedule site visits through a natural conversation.

The system combines a prompt-driven Gemini agent with structured customer memory, profile extraction, lead qualification, safety rules, and a simulated booking tool.

---

## Demo

### Live Demo

Not deployed. The assignment is submitted as a locally runnable application with a public GitHub repository and demo video.

### Demo Video

> Add demo video link here before submission.

### Repository

https://github.com/vijendramane/Northstar_AI

---

# 1. What Northstar AI Does

Northstar AI is designed around a simple idea:

> A real-estate sales agent should not only answer questions. It should understand the customer, remember their requirements, qualify their intent, and move the conversation toward a useful next step.

The agent can:

- Answer property-related questions
- Understand natural conversational language
- Support English, Hindi, and Hinglish
- Extract customer requirements
- Maintain conversation memory
- Distinguish questions from actual customer preferences
- Qualify leads
- Calculate a transparent qualification score
- Handle objections
- Safely handle unknown information
- Handle human escalation
- Handle callback requests
- Respect do-not-contact requests
- Provide simulated site-visit availability
- Confirm site visits
- Reject unavailable booking slots
- Return alternative slots
- Display structured customer analytics

---

# 2. Property Context

The application uses the fictional property information supplied for the assignment.

### Project

**Northstar One**

### Location

**Sector 79, Gurugram**

### Configurations

- 2 BHK
- 3 BHK

### Starting Prices

| Configuration | Starting Price |
|---|---:|
| 2 BHK | ₹1.35 crore onwards |
| 3 BHK | ₹1.75 crore onwards |

The agent is intentionally restricted from inventing property information that has not been provided.

For example, if the customer asks for an exact possession date and the system does not have verified information, it should acknowledge that limitation rather than fabricate a date.

---

# 3. Product Experience

The application contains three major areas:

### Property Context

Provides the customer with the relevant project context.

### AI Conversation

The central conversational interface where the customer interacts with Northstar AI.

### Live Lead Intelligence

The right-side panel maintains structured information extracted from the conversation, including:

- Customer name
- Configuration
- Budget
- Purpose
- Timeline
- Site-visit status
- Qualification score
- Lead temperature
- Other customer signals

This allows the application to demonstrate how a conversational interaction can simultaneously produce structured sales information.

---

# 4. Core Agent Capabilities

## 4.1 Natural Conversation

The agent is not implemented as a collection of hard-coded question/answer pairs.

Customers can express the same requirement in different ways.

For example:

```text
I want a 3 BHK.
