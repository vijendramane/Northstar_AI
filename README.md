# Northstar AI

### AI-Powered Real Estate Sales Concierge

A conversational AI sales agent built for the Huvo AI Forward Deployed Engineer assignment.

Northstar AI acts as a sales concierge for the fictional real-estate company Northstar Homes. It understands customer requirements, remembers conversation context, qualifies leads, handles objections, answers property questions using verified information, and helps customers schedule site visits.

---

## Demo

### Demo Video
[Watch the demo video](YOUR_DEMO_VIDEO_LINK)

### GitHub Repository
[Northstar AI on GitHub](YOUR_GITHUB_REPOSITORY_LINK)

---

# 1. Project Overview

Northstar AI is designed to simulate an AI-powered real-estate sales representative.

The agent can:

- Have natural conversations with customers
- Understand English, Hindi, and Hinglish
- Remember customer information across a conversation
- Identify customer requirements
- Qualify leads
- Answer property-related questions
- Handle unknown or unverified questions safely
- Handle customer objections
- Handle callback requests
- Handle human escalation
- Respect do-not-contact requests
- Provide site-visit availability
- Simulate site-visit booking
- Handle failed booking attempts
- Generate structured customer analytics
- Calculate a transparent qualification score

The main design principle is to keep the agent conversational while maintaining structured customer state in the backend.

---

# 2. Property Context

The fictional property used in this assignment is:

**Project:** Northstar One

**Location:** Sector 79, Gurugram

### Configurations

- 2 BHK
- 3 BHK

### Starting Prices

- 2 BHK: ₹1.35 crore onwards
- 3 BHK: ₹1.75 crore onwards

The agent is instructed not to invent property information that has not been provided.

---

# 3. Key Features

## Conversational AI

The agent uses Gemini to generate natural conversational responses while following a dedicated system prompt.

The prompt controls:

- Conversation behaviour
- Customer qualification
- Language handling
- Safety rules
- Objection handling
- Escalation
- Booking behaviour
- Conversation ending

The final prompt is available at:

```text
prompts/northstar_agent.txt