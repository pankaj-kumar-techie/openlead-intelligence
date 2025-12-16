# Legal & Ethical Guidelines

**OpenLead Intelligence** is a framework designed for gathering Public Business Intelligence. Users must adhere to strict ethical and legal guidelines when operating this software.

## 1. Public Data Only
This tool is designed to collect data that is manifestly made public by companies (e.g., job postings, press releases, public profiles).
- **DO NOT** use this tool to harvest personal private information (PII) such as personal email addresses, home addresses, or private phone numbers.
- **DO NOT** attempt to bypass authentication barriers (login walls) for services you do not have authorized access to.

## 2. Rate Limiting & Netiquette
- Respect the target website's resources. Aggressive scraping is distinguishable from a DoS attack.
- The framework includes built-in rate limiting (`rate_limit_delay`). Do not set this to zero.
- Use the `robots.txt` compliance feature enabled by default.

## 3. Terms of Service
- Many platforms (LinkedIn, Crunchbase, AngelList) prohibit scraping in their ToS.
- This code is provided for educational and internal analytical purposes. Usage against specific targets may violate their civil terms.
- **You are solely responsible for ensuring your usage complies with the Terms of Service of the websites you interact with.**

## 4. GDPR & Data Privacy
- If you incidentally collect data regarding EU citizens, you are a Data Controller under GDPR.
- Ensure you have a lawful basis for processing (e.g., Legitimate Interest for B2B prospecting).
- Provide mechanisms for data subjects to opt-out if you reach out to them.

## 5. Liability
The authors of OpenLead Intelligence accept no liability for any misuse of this software or legal consequences arising from its use.
