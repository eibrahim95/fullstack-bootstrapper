// Django expects the CSRF token in X-CSRFToken; Unpoly reads it from <meta name="csrf-token">.
up.protocol.config.csrfHeader = "X-CSRFToken";

// Init page scripts with up.compiler(), not DOMContentLoaded, so swapped fragments get them too.
