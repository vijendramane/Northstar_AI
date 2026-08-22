import { useEffect, useRef, useState } from "react";
import "./App.css";
import heroImage from "./assets/hero.png";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

const EMPTY_PROFILE = {
  name: null,
  configuration: null,
  budget: null,
  purpose: null,
  timeline: null,
  location_preference: null,
  preferred_language: null,
  interest_level: null,
  intent: null,
  objections: [],
  site_visit_status: "not_requested",
  follow_up_required: false,
  human_escalation: false,
  do_not_contact: false,
};

function App() {
  const [sessionId] = useState(
    () => `northstar-${crypto.randomUUID()}`
  );

  const [messages, setMessages] = useState([
    {
      id: crypto.randomUUID(),
      role: "assistant",
      content:
        "Welcome to Northstar One. Tell me what you're looking for and I'll help you explore the right home.",
    },
  ]);

  const [profile, setProfile] =
    useState(EMPTY_PROFILE);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  async function sendMessage(messageOverride) {
    const message = (
      messageOverride ?? input
    ).trim();

    if (!message || loading) {
      return;
    }

    setError("");

    setMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: message,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const response = await fetch(
        `${API_URL}/api/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({
            session_id: sessionId,
            message,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `Request failed: ${response.status}`
        );
      }

      const data = await response.json();

      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.message || "",
        },
      ]);

      if (data.profile) {
        setProfile({
          ...EMPTY_PROFILE,
          ...data.profile,
        });
      }
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to Northstar AI. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    sendMessage();
  }

  const quickActions = [
    [
      "Explore 3 BHK",
      "Tell me about the 3 BHK options.",
    ],
    [
      "View pricing",
      "What are the available prices?",
    ],
    [
      "Schedule a visit",
      "I would like to schedule a site visit.",
    ],
  ];

  const qualificationSteps = [
    {
      label: "Configuration",
      value: profile.configuration,
    },
    {
      label: "Budget",
      value: profile.budget,
    },
    {
      label: "Purpose",
      value: profile.purpose,
    },
    {
      label: "Timeline",
      value: profile.timeline,
    },
  ];

  return (
    <div className="shell">

      {/* TOP BAR */}

      <header className="topbar">

        <div className="logo-wrap">

          <div className="logo-mark">
            N
          </div>

          <div>
            <div className="logo-title">
              NORTHSTAR
            </div>

            <div className="logo-caption">
              AI SALES CONCIERGE
            </div>
          </div>

        </div>

        <div className="topbar-center">
          NORTHSTAR ONE
          <span>·</span>
          SECTOR 79, GURUGRAM
        </div>

        <div className="live-pill">
          <span className="live-dot" />
          AI ONLINE
        </div>

      </header>


      {/* MAIN DASHBOARD */}

      <main className="dashboard">

        {/* LEFT PROPERTY PANEL */}

        <aside className="property-panel">

          <div className="property-image-wrap">

            <img
              src={heroImage}
              alt="Northstar One"
              className="property-image"
            />

            <div className="image-gradient" />

            <div className="image-label">
              NORTHSTAR ONE
            </div>

          </div>


          <div className="property-body">

            <div className="mini-label">
              FEATURED RESIDENCE
            </div>

            <h1>
              Northstar One
            </h1>

            <p className="location">
              Sector 79 · Gurugram
            </p>


            <div className="property-price-grid">

              <div>
                <span>2 BHK</span>
                <strong>₹1.35 Cr+</strong>
              </div>

              <div>
                <span>3 BHK</span>
                <strong>₹1.75 Cr+</strong>
              </div>

            </div>


            <div className="property-features">

              <span>Premium residences</span>
              <span>Self-use</span>
              <span>Site visits</span>

            </div>


            <div className="property-note">
              <span className="small-dot" />
              AI concierge is ready to help
            </div>

          </div>

        </aside>


        {/* CENTER CHAT */}

        <section className="chat-panel">

          <div className="chat-top">

            <div>
              <div className="section-eyebrow">
                CONVERSATION
              </div>

              <h2>
                Your property concierge
              </h2>

              <p>
                Ask naturally. I'll help with
                requirements, pricing and visits.
              </p>
            </div>

            <div className="chat-status">
              <span />
              READY
            </div>

          </div>


          <div className="messages">

            <div className="date-divider">
              TODAY
            </div>

            {messages.map((message) => (

              <div
                key={message.id}
                className={`msg-row ${
                  message.role === "user"
                    ? "msg-user"
                    : "msg-ai"
                }`}
              >

                {message.role ===
                  "assistant" && (
                  <div className="ai-avatar">
                    N
                  </div>
                )}

                <div className="msg-stack">

                  <div className="msg-name">
                    {message.role === "user"
                      ? "YOU"
                      : "NORTHSTAR AI"}
                  </div>

                  <div className="msg-bubble">
                    {message.content}
                  </div>

                </div>

              </div>

            ))}


            {loading && (

              <div className="msg-row msg-ai">

                <div className="ai-avatar">
                  N
                </div>

                <div className="msg-stack">

                  <div className="msg-name">
                    NORTHSTAR AI
                  </div>

                  <div className="typing-bubble">
                    <i />
                    <i />
                    <i />
                  </div>

                </div>

              </div>

            )}

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <div ref={bottomRef} />

          </div>


          {/* QUICK ACTIONS */}

          <div className="quick-row">

            <span>
              TRY ASKING
            </span>

            {quickActions.map(
              ([label, message]) => (
                <button
                  key={label}
                  disabled={loading}
                  onClick={() =>
                    sendMessage(message)
                  }
                >
                  {label}
                </button>
              )
            )}

          </div>


          {/* INPUT */}

          <form
            className="composer"
            onSubmit={handleSubmit}
          >

            <input
              value={input}
              onChange={(event) =>
                setInput(event.target.value)
              }
              placeholder="Ask anything about Northstar One..."
              disabled={loading}
            />

            <button
              type="submit"
              disabled={
                loading ||
                !input.trim()
              }
              className="send-button"
            >
              <span>Send</span>
              <b>↗</b>
            </button>

          </form>

          <div className="composer-note">
            AI-assisted · Property information is subject
            to verification.
          </div>

        </section>


        {/* RIGHT LEAD PANEL */}

        <aside className="lead-panel">

          <div className="lead-panel-header">

            <div>
              <div className="section-eyebrow">
                LIVE LEAD
              </div>

              <h2>
                Qualification
              </h2>
            </div>

            <div className="lead-live">
              LIVE
            </div>

          </div>


          {/* LEAD IDENTITY */}

          <div className="lead-identity">

            <div className="lead-avatar">
              {profile.name
                ? profile.name
                    .charAt(0)
                    .toUpperCase()
                : "?"}
            </div>

            <div>

              <div className="lead-name">
                {profile.name ||
                  "New visitor"}
              </div>

              <div className="lead-sub">
                {profile.intent ||
                  "Qualification in progress"}
              </div>

            </div>

          </div>


          {/* PROFILE */}

          <div className="profile-card">

            {qualificationSteps.map(
              (item) => (

                <div
                  className="profile-row"
                  key={item.label}
                >

                  <span>
                    {item.label}
                  </span>

                  <strong
                    className={
                      item.value
                        ? "filled"
                        : ""
                    }
                  >
                    {item.value || "Pending"}
                  </strong>

                </div>

              )
            )}

          </div>


          {/* SIGNALS */}

          <div className="signals">

            <div className="signals-title">
              AI SIGNALS
            </div>

            <Signal
              label="Requirement captured"
              active={
                !!profile.configuration
              }
            />

            <Signal
              label="Budget identified"
              active={!!profile.budget}
            />

            <Signal
              label="Buying intent"
              active={!!profile.purpose}
            />

            <Signal
              label="Timeline identified"
              active={!!profile.timeline}
            />

            <Signal
              label="Site visit"
              active={
                profile.site_visit_status ===
                "confirmed"
              }
            />

          </div>


          {/* STATUS */}

          <div className="lead-status">

            <div>
              <span>FOLLOW-UP</span>
              <strong>
                {profile.follow_up_required
                  ? "Required"
                  : "Not required"}
              </strong>
            </div>

            <div>
              <span>ESCALATION</span>
              <strong>
                {profile.human_escalation
                  ? "Requested"
                  : "None"}
              </strong>
            </div>

          </div>


          {profile.do_not_contact && (

            <div className="do-not-contact">
              Do not contact requested
            </div>

          )}

        </aside>

      </main>

    </div>
  );
}


function Signal({ label, active }) {
  return (
    <div className="signal">

      <div
        className={
          active
            ? "signal-icon active"
            : "signal-icon"
        }
      >
        {active ? "✓" : "○"}
      </div>

      <span>{label}</span>

    </div>
  );
}


export default App;