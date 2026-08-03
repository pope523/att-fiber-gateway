# HAR PII Manual Checklist

If you don't want to use an AI assistant for the PII screen, use this
checklist instead. Open the `.sanitized.har` (decompressed) in a text
editor and search for each item:

| Search for | Expected result |
|------------|-----------------|
| Your WiFi network name (SSID) | No results |
| Your WiFi password | No results |
| Your router admin password | No results |
| Your public IP | Replaced with `***PUBLIC_IP***` |
| Serial numbers | Replaced with `***SERIAL***` or hashed |

If anything sensitive remains, replace it with `***REDACTED***`, save,
re-gzip, and note in your issue what you redacted.
