# HAR PII Screening Prompt

Paste this into ChatGPT, Claude, or any AI assistant that accepts file
attachments, after attaching your `.sanitized.har` (decompress the
`.sanitized.har.gz` first). The free tiers of ChatGPT and Claude both
work for a few prompts; an incognito window without an account works
too.

---

```text
I need a defensive privacy review on a sanitized HAR file before I
share it publicly on GitHub. The file has been through an automated
sanitizer; I'm asking you to look for anything it might have missed,
so I can redact before sharing. This is a leak-prevention check, not
credential extraction.

Search the attached HAR for:

1. WiFi network names — short alphanumeric tokens near "ssid",
   "network_name", "wifi_name", or JSON keys ending in "Ssid" or
   "NetworkName". Report any value that doesn't look like a placeholder.
2. Passwords — any value near "password", "passphrase", "psk",
   "wpa_key", "admin_password" that is NOT "***REDACTED***" or empty.
3. MAC addresses NOT in the format "02:xx:xx:xx:xx:xx" (sanitizer
   hash format starts with 02). Real MACs in any other format are a leak.
4. IPv4 addresses that aren't RFC1918 private (10.x, 172.16-31.x,
   192.168.x), 0.0.0.0, 127.0.0.1, or 240.x.x.x (sanitizer's
   placeholder for redacted public IPs).
5. Session tokens, bearer tokens, or API keys — long opaque strings
   in cookies, Authorization headers, or response bodies that aren't
   already "***REDACTED***".

Output a fenced markdown block:

​```
## PII review

- WiFi names found: <list or "none">
- Passwords found: <list or "none">
- Non-hashed MACs: <list or "none">
- Non-redacted public IPs: <list or "none">
- Suspicious tokens: <list or "none">
- Verdict: <CLEAN | NEEDS MANUAL REDACTION>
​```

For each item include the entry index plus a 10-20 character snippet
around the value (e.g. "entry 47, response body, near
`var wifiSsid = `"). Don't paste the actual sensitive value back to me.
```

---

**If verdict is CLEAN**: you're ready to submit.

**If verdict is NEEDS MANUAL REDACTION**: open the file in a text
editor, replace each flagged value with `***REDACTED***`, save, re-gzip,
and submit. Note in your issue what you redacted so the sanitizer can
be improved for future contributors.

False positives are common (an AI may flag a placeholder as
suspicious). Err on the side of redacting if unsure — the cost of an
unnecessary redaction is zero, the cost of a leaked credential is
real.
