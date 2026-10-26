package main

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestNormalizeServerURLAcceptsWhatUsersType(t *testing.T) {
	cases := []struct {
		in   string
		want string
	}{
		{"kino.example.com", "https://kino.example.com"},
		{"  https://kino.example.com/  ", "https://kino.example.com"},
		{"https://kino.example.com/app/", "https://kino.example.com/app"},
		{"http://10.0.0.5:8088", "http://10.0.0.5:8088"},
		{"https://kino.example.com/?x=1#frag", "https://kino.example.com"},
		{"https://user:pw@kino.example.com", "https://kino.example.com"},
	}
	for _, tc := range cases {
		got, err := normalizeServerURL(tc.in)
		if err != nil {
			t.Fatalf("normalizeServerURL(%q) returned error: %v", tc.in, err)
		}
		if got != tc.want {
			t.Fatalf("normalizeServerURL(%q) = %q, want %q", tc.in, got, tc.want)
		}
	}
}

func TestNormalizeServerURLRejectsGarbage(t *testing.T) {
	for _, in := range []string{"", "   ", "ftp://kino.example.com", "https://"} {
		if _, err := normalizeServerURL(in); err == nil {
			t.Fatalf("normalizeServerURL(%q) should fail", in)
		}
	}
}

func TestCheckServerAcceptsSupportedVersion(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/health" {
			t.Fatalf("unexpected path %q", r.URL.Path)
		}
		_, _ = w.Write([]byte(`{"ok":true,"version":"1.0.3"}`))
	}))
	defer srv.Close()

	version, err := checkServer(srv.URL, 5*time.Second)
	if err != nil {
		t.Fatalf("checkServer returned error: %v", err)
	}
	if version != "1.0.3" {
		t.Fatalf("version = %q, want 1.0.3", version)
	}
}

func TestCheckServerRefusesServerOlderThanMinimum(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`{"ok":true,"version":"1.0.0"}`))
	}))
	defer srv.Close()

	_, err := checkServer(srv.URL, 5*time.Second)
	if err == nil {
		t.Fatal("expected the handshake to refuse an old server")
	}
	if !strings.Contains(err.Error(), minServerVersion) {
		t.Fatalf("error should name the minimum version, got: %v", err)
	}
}

func TestCheckServerAllowsServerWithoutVersionField(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`{"ok":true,"db":true}`))
	}))
	defer srv.Close()

	version, err := checkServer(srv.URL, 5*time.Second)
	if err != nil {
		t.Fatalf("a server without a version field must still connect: %v", err)
	}
	if version != "" {
		t.Fatalf("version = %q, want empty for a legacy server", version)
	}
}

func TestCheckServerReportsUnhealthyServer(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte(`{"ok":false}`))
	}))
	defer srv.Close()

	if _, err := checkServer(srv.URL, 5*time.Second); err == nil {
		t.Fatal("expected an error for a server that reports not-ready")
	}
}

func TestCheckServerRejectsNonKinoGuildEndpoint(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		_, _ = w.Write([]byte("<html>hello</html>"))
	}))
	defer srv.Close()

	if _, err := checkServer(srv.URL, 5*time.Second); err == nil {
		t.Fatal("expected an error for a payload that is not health JSON")
	}
}

func TestNormalizeModeKeepsOnlyKnownValues(t *testing.T) {
	if got := normalizeMode("portable"); got != modePortable {
		t.Fatalf("normalizeMode(portable) = %q", got)
	}
	for _, in := range []string{"", "server", "garbage", "PORTABLE"} {
		if got := normalizeMode(in); got != modeServer {
			t.Fatalf("normalizeMode(%q) = %q, want %q", in, got, modeServer)
		}
	}
}
