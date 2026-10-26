package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// minServerVersion is the oldest KinoGuild server this client can talk to.
//
// The shell loads the server's dashboard straight from the server, so a server
// that is too old would fail later with scattered 404s and blank panels. The
// handshake turns that into one clear message up front. Servers that predate
// the version field are accepted with a warning instead of being refused, so a
// client build can still be pointed at an older deployment during rollout.
const minServerVersion = "1.0.2"

// serverHealth is the part of GET /api/health this client reads.
type serverHealth struct {
	OK      bool   `json:"ok"`
	Version string `json:"version"`
}

// normalizeServerURL accepts what a user types — "example.com",
// "https://example.com/app/", "http://10.0.0.5:8088" — and returns a canonical
// base URL with no trailing slash and no query or fragment.
func normalizeServerURL(raw string) (string, error) {
	text := strings.TrimSpace(raw)
	if text == "" {
		return "", fmt.Errorf("server address is empty")
	}
	if !strings.Contains(text, "://") {
		text = "https://" + text
	}
	parsed, err := url.Parse(text)
	if err != nil {
		return "", fmt.Errorf("invalid server address %q: %w", raw, err)
	}
	if parsed.Host == "" {
		return "", fmt.Errorf("invalid server address %q: missing host", raw)
	}
	switch parsed.Scheme {
	case "http", "https":
	default:
		return "", fmt.Errorf("unsupported scheme %q: use http or https", parsed.Scheme)
	}
	parsed.Path = strings.TrimRight(parsed.Path, "/")
	parsed.RawQuery = ""
	parsed.Fragment = ""
	parsed.User = nil
	return parsed.String(), nil
}

// fetchServerHealth reads GET /api/health from base.
func fetchServerHealth(base string, timeout time.Duration) (serverHealth, error) {
	client := &http.Client{Timeout: timeout}
	resp, err := client.Get(strings.TrimRight(base, "/") + "/api/health")
	if err != nil {
		return serverHealth{}, err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return serverHealth{}, fmt.Errorf("health check returned HTTP %d", resp.StatusCode)
	}
	var health serverHealth
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		return serverHealth{}, fmt.Errorf("not a KinoGuild server: %w", err)
	}
	if !health.OK {
		return serverHealth{}, fmt.Errorf("server is reachable but not ready")
	}
	return health, nil
}

// checkServer validates a candidate base URL: reachable, healthy, and new
// enough. It returns the server version (empty when the server is too old to
// report one).
func checkServer(base string, timeout time.Duration) (string, error) {
	health, err := fetchServerHealth(base, timeout)
	if err != nil {
		return "", err
	}
	if health.Version == "" {
		return "", nil
	}
	if compareVersions(health.Version, minServerVersion) < 0 {
		return health.Version, fmt.Errorf(
			"server version %s is older than the supported minimum %s; upgrade the server first",
			health.Version, minServerVersion,
		)
	}
	return health.Version, nil
}
