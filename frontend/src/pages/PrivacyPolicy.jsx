import { Link } from "react-router-dom";

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-bg py-12 px-6">
      <div className="max-w-2xl mx-auto">

        <p className="text-sm text-ink-muted mb-8">
          <Link to="/login" className="text-accent font-medium hover:underline">
            ← Back to login
          </Link>
        </p>

        <h1 className="font-display text-3xl font-semibold text-ink mb-1">RAVISN Privacy Policy</h1>
        <p className="text-ink-muted text-sm mb-10">Last updated: August 7, 2026</p>

        <div className="bg-surface border border-line rounded-xl p-8 space-y-8 text-ink">

          <section>
            <h2 className="font-display text-xl font-semibold mb-3">Overview</h2>
            <p className="text-ink-muted leading-relaxed">
              RAVISN ("we," "us," "our") is based in Lahore, Punjab, Pakistan, and provides automated
              messaging technology that businesses ("Business Clients") use to communicate with their
              own customers over WhatsApp, Facebook Messenger, and Instagram Direct Messages. This
              policy explains what information we collect when you message a business that uses
              RAVISN's technology, how we use it, and what choices you have.
            </p>
            <p className="text-ink-muted leading-relaxed mt-3">
              RAVISN acts as a technology provider for Business Clients — we do not own or control
              the underlying WhatsApp number, Facebook Page, or Instagram account you're messaging,
              which remain the Business Client's own.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-semibold mb-3">Information We Collect</h2>
            <p className="text-ink-muted leading-relaxed mb-3">
              When you send a message to a business that uses RAVISN's messaging agent, we may collect:
            </p>
            <ul className="list-disc list-inside space-y-2 text-ink-muted">
              <li>Your platform identifier — your WhatsApp number, or a platform-assigned identifier for Facebook Messenger or Instagram</li>
              <li>Your display name, where the messaging platform makes it available to us</li>
              <li>The content of the messages you send, and the automated replies sent back to you</li>
              <li>Booking details you choose to share — such as your name, a contact method, a preferred date or time, and any notes — if you use the agent to request an appointment or booking</li>
            </ul>
            <p className="text-ink-muted leading-relaxed mt-3">
              We only collect this information through the conversation itself. We do not scrape,
              purchase, or receive your information from any other source.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-semibold mb-3">How We Use This Information</h2>
            <ul className="list-disc list-inside space-y-2 text-ink-muted">
              <li>To generate a relevant automatic reply, based on the specific Business Client's own knowledge base</li>
              <li>To keep a record of the conversation so replies stay consistent and the Business Client can review it</li>
              <li>To record any booking or appointment details you provide, so the Business Client can follow up with you directly</li>
            </ul>
            <p className="text-ink-muted leading-relaxed mt-3">
              We do not use your information for advertising, and we do not sell it to third parties.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-semibold mb-3">How Messages Are Processed</h2>
            <p className="text-ink-muted leading-relaxed">
              To generate replies, message content is sent to a third-party AI language model
              provider (such as OpenAI or Google) solely to produce a reply to your specific
              message. We do not permit these providers to use your conversations to train their
              general-purpose models beyond what their own standard API terms allow.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-semibold mb-3">Who Can Access Your Information</h2>
            <p className="text-ink-muted leading-relaxed">
              Only the specific Business Client you messaged, and RAVISN staff who operate the
              underlying platform, can access your conversation. RAVISN serves many different
              Business Clients; one business cannot see another business's customer conversations.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-semibold mb-3">Data Retention</h2>
            <p className="text-ink-muted leading-relaxed">
              We retain your conversation and any booking information for as long as the Business
              Client's account with RAVISN remains active, or until a valid deletion request is
              processed, whichever comes first.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-semibold mb-3">Your Rights and Data Deletion</h2>
            <p className="text-ink-muted leading-relaxed">
              You may request that we delete your conversation history and any booking information
              by contacting us at{" "}
              <a href="mailto:privacy@ravisn.com" className="text-accent hover:underline">
                privacy@ravisn.com
              </a>{" "}
              with the phone number or account handle you messaged from, and the name of the
              business you contacted. We will remove your data from our active systems within
              30 days of a verified request, except where we are required to retain it for legal
              or regulatory reasons.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-semibold mb-3">Security</h2>
            <p className="text-ink-muted leading-relaxed">
              We use reasonable technical measures — including encrypted connections and access
              controls limiting data to authorized staff and the relevant Business Client — to
              protect your information. No online system can be guaranteed completely secure.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-semibold mb-3">Children's Privacy</h2>
            <p className="text-ink-muted leading-relaxed">
              Our services are not directed at children. Use of WhatsApp, Facebook Messenger, and
              Instagram is subject to each platform's own minimum age requirements, and we rely on
              those platforms' own safeguards in this respect.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-semibold mb-3">Changes to This Policy</h2>
            <p className="text-ink-muted leading-relaxed">
              We may update this policy from time to time. The date at the top reflects the most
              recent revision. Continued use of the messaging service after a change constitutes
              acceptance of the updated policy.
            </p>
          </section>

          <section>
            <h2 className="font-display text-xl font-semibold mb-3">Contact Us</h2>
            <div className="text-ink-muted space-y-1">
              <p>RAVISN</p>
              <p>Lahore, Punjab, Pakistan</p>
              <p>
                <a href="mailto:privacy@ravisn.com" className="text-accent hover:underline">
                  privacy@ravisn.com
                </a>
              </p>
              <p>
                <a href="https://ravisn.com" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">
                  ravisn.com
                </a>
              </p>
            </div>
          </section>

        </div>

        <p className="text-center text-xs text-ink-muted mt-8">
          © 2026 RAVISN. All rights reserved.
        </p>
      </div>
    </div>
  );
}
