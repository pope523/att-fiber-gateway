"""Cable Modem Monitor Core — platform-agnostic engine."""

from .log_filters import install_filters as _install_log_filters

# Suppress upstream-library log noise (urllib3 firmware-quirk warnings,
# etc.) for every consumer of Core. See ``log_filters`` for details
# and the procedure for adding new patterns.
_install_log_filters()
