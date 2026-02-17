//! Per-database rate limiting with adaptive governor instances.
//!
//! Each DB query waits for its governor permit via `until_ready()`, which
//! spaces requests at the configured rate. On 429, the governor is slowed
//! and the error is returned immediately.

use std::collections::HashMap;
use std::sync::Arc;
use std::sync::atomic::{AtomicU32, Ordering};
use std::time::{Duration, Instant};

use arc_swap::ArcSwap;
use governor::clock::DefaultClock;
use governor::state::{InMemoryState, NotKeyed};
use governor::{Quota, RateLimiter};

use crate::db::{DatabaseBackend, DbQueryResult};

/// Type alias for governor's direct rate limiter.
type DirectLimiter = RateLimiter<NotKeyed, InMemoryState, DefaultClock>;

/// Error type for database queries, distinguishing rate limiting from other errors.
#[derive(Debug, Clone)]
pub enum DbQueryError {
    /// Server returned 429 Too Many Requests.
    RateLimited { retry_after: Option<Duration> },
    /// Any other error.
    Other(String),
}

impl std::fmt::Display for DbQueryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DbQueryError::RateLimited {
                retry_after: Some(d),
            } => write!(f, "Rate limited (429), retry after {:.1}s", d.as_secs_f64()),
            DbQueryError::RateLimited { retry_after: None } => write!(f, "Rate limited (429)"),
            DbQueryError::Other(msg) => write!(f, "{}", msg),
        }
    }
}

impl std::error::Error for DbQueryError {}

impl From<String> for DbQueryError {
    fn from(s: String) -> Self {
        DbQueryError::Other(s)
    }
}

/// Per-DB rate limiter with adaptive rate adjustment via ArcSwap.
///
/// When a 429 is received, the governor is atomically swapped to a slower rate.
/// After a cooldown period (60s) with no 429s, the original rate is restored.
pub struct AdaptiveDbLimiter {
    limiter: ArcSwap<DirectLimiter>,
    /// Base period between allowed requests.
    base_period: Duration,
    /// Current slowdown factor (1 = normal, 2 = half rate, etc.).
    current_factor: AtomicU32,
    /// Timestamp of the last 429 response.
    last_429: std::sync::Mutex<Option<Instant>>,
}

impl AdaptiveDbLimiter {
    /// Create a new limiter with the given period between requests.
    pub fn new(period: Duration) -> Self {
        let quota = Quota::with_period(period).expect("period must be > 0");
        let limiter = Arc::new(DirectLimiter::direct(quota));
        Self {
            limiter: ArcSwap::from(limiter),
            base_period: period,
            current_factor: AtomicU32::new(1),
            last_429: std::sync::Mutex::new(None),
        }
    }

    /// Create a limiter allowing `n` requests per second.
    pub fn per_second(n: u32) -> Self {
        let ms = 1000 / n.max(1) as u64;
        Self::new(Duration::from_millis(ms))
    }

    /// Wait until the rate limiter allows a request.
    ///
    /// Blocks the calling future until a token is available. This naturally
    /// spaces requests at the configured rate across all concurrent callers.
    pub async fn acquire(&self) {
        self.try_decay();
        let limiter = self.limiter.load();
        limiter.until_ready().await;
    }

    /// Called when a 429 is received. Doubles the slowdown factor and swaps the governor.
    pub fn on_rate_limited(&self) {
        if let Ok(mut last) = self.last_429.lock() {
            *last = Some(Instant::now());
        }

        // Double factor, cap at 16x slowdown
        let _ = self
            .current_factor
            .fetch_update(Ordering::SeqCst, Ordering::SeqCst, |f| {
                Some((f * 2).min(16))
            });

        let factor = self.current_factor.load(Ordering::SeqCst);
        if let Some(scaled) = self.base_period.checked_mul(factor)
            && let Some(quota) = Quota::with_period(scaled)
        {
            let new_limiter = Arc::new(DirectLimiter::direct(quota));
            self.limiter.store(new_limiter);
        }
    }

    /// If 60s have passed since the last 429, restore the original rate.
    fn try_decay(&self) {
        let should_restore = self
            .last_429
            .lock()
            .ok()
            .and_then(|last| last.map(|t| t.elapsed().as_secs() >= 60))
            .unwrap_or(false);

        if should_restore && self.current_factor.load(Ordering::SeqCst) > 1 {
            self.current_factor.store(1, Ordering::SeqCst);
            let quota = Quota::with_period(self.base_period).expect("base period valid");
            let limiter = Arc::new(DirectLimiter::direct(quota));
            self.limiter.store(limiter);
        }
    }
}

/// Collection of per-database rate limiters.
pub struct RateLimiters {
    limiters: HashMap<&'static str, AdaptiveDbLimiter>,
}

impl Default for RateLimiters {
    fn default() -> Self {
        Self::new(false, false)
    }
}

impl RateLimiters {
    /// Build rate limiters based on whether API keys/mailto are configured.
    pub fn new(has_crossref_mailto: bool, has_s2_api_key: bool) -> Self {
        let mut limiters = HashMap::new();

        // CrossRef: 1/s without mailto, 3/s with mailto
        let crossref_rate = if has_crossref_mailto { 3 } else { 1 };
        limiters.insert("CrossRef", AdaptiveDbLimiter::per_second(crossref_rate));

        // arXiv API: 3/s is the actual documented limit
        limiters.insert("arXiv", AdaptiveDbLimiter::per_second(3));

        // DBLP (online): ~1/s guideline
        limiters.insert("DBLP", AdaptiveDbLimiter::per_second(1));

        // Semantic Scholar: keyless ~100 req/5min, keyed 1/s (basic tier)
        if has_s2_api_key {
            limiters.insert("Semantic Scholar", AdaptiveDbLimiter::per_second(1));
        } else {
            // ~0.33/s → 1 request per 3 seconds
            limiters.insert(
                "Semantic Scholar",
                AdaptiveDbLimiter::new(Duration::from_secs(3)),
            );
        }

        // Europe PMC: not documented, conservative 2/s
        limiters.insert("Europe PMC", AdaptiveDbLimiter::per_second(2));

        // PubMed: 3/s without key
        limiters.insert("PubMed", AdaptiveDbLimiter::per_second(3));

        // ACL Anthology (online scraping): conservative 2/s
        limiters.insert("ACL Anthology", AdaptiveDbLimiter::per_second(2));

        // OpenAlex: 10/s without key, 100/s with key — light governor so adaptive
        // backoff kicks in if we get 429'd
        limiters.insert("OpenAlex", AdaptiveDbLimiter::per_second(10));
        // SSRN: disabled, skip limiter
        // NeurIPS: disabled, skip limiter
        // Offline DBs (DBLP offline, ACL offline) share names but don't make HTTP requests

        Self { limiters }
    }

    /// Get the rate limiter for a given database, if one exists.
    pub fn get(&self, db_name: &str) -> Option<&AdaptiveDbLimiter> {
        self.limiters.get(db_name)
    }
}

/// Check if an HTTP response is a 429 and extract Retry-After if present.
///
/// Returns `Err(DbQueryError::RateLimited { .. })` if 429, `Ok(())` otherwise.
pub fn check_rate_limit_response(resp: &reqwest::Response) -> Result<(), DbQueryError> {
    if resp.status().as_u16() == 429 {
        let retry_after = resp
            .headers()
            .get("retry-after")
            .and_then(|v| v.to_str().ok())
            .and_then(parse_retry_after);
        Err(DbQueryError::RateLimited { retry_after })
    } else {
        Ok(())
    }
}

/// Parse a Retry-After header value (seconds or HTTP-date).
pub fn parse_retry_after(value: &str) -> Option<Duration> {
    // Try parsing as integer seconds first
    if let Ok(secs) = value.trim().parse::<u64>() {
        return Some(Duration::from_secs(secs));
    }
    // Try parsing as HTTP-date (e.g. "Wed, 21 Oct 2015 07:28:00 GMT")
    // For simplicity, just use a conservative fallback if it looks like a date
    if value.contains(',') || value.contains("GMT") {
        return Some(Duration::from_secs(5));
    }
    None
}

/// Query a database with proactive governor rate limiting.
///
/// 1. Acquires the per-DB governor (waits if needed)
/// 2. Calls `db.query()`
/// 3. On 429: adapts governor to slower rate and returns error immediately
///    (the pool-level retry queue will re-check failed DBs later)
/// 4. On other errors or success: returns immediately
///
/// Result of a rate-limited query, including the elapsed time measured after governor wait.
pub struct RateLimitedResult {
    pub result: Result<DbQueryResult, DbQueryError>,
    /// Elapsed time measuring only the actual HTTP round-trip, not governor queue wait.
    pub elapsed: Duration,
}

pub async fn query_with_rate_limit(
    db: &dyn DatabaseBackend,
    title: &str,
    client: &reqwest::Client,
    timeout: Duration,
    rate_limiters: &RateLimiters,
) -> RateLimitedResult {
    // Skip rate limiting for local/offline backends (SQLite queries need no throttling)
    let limiter = if db.is_local() {
        None
    } else {
        rate_limiters.get(db.name())
    };

    // Wait for governor permit (blocks until it's this request's turn)
    if let Some(lim) = limiter {
        lim.acquire().await;
    }

    // Timer starts AFTER governor — measures actual HTTP time only
    let start = Instant::now();

    let result = match db.query(title, client, timeout).await {
        Ok(result) => Ok(result),
        Err(DbQueryError::RateLimited { retry_after }) => {
            // Adapt governor to slower rate so subsequent requests are throttled
            if let Some(lim) = limiter {
                lim.on_rate_limited();
            }

            // Honor Retry-After: sleep then retry once instead of bailing.
            // Cap at the DB timeout — sleeping longer than that makes no sense.
            // The governor adaptation prevents cascading 429s for future requests.
            let wait = retry_after.unwrap_or(Duration::from_secs(2));
            let wait = wait.min(timeout);
            log::info!(
                "{}: 429 rate limited, waiting {:.1}s then retrying",
                db.name(),
                wait.as_secs_f64()
            );
            tokio::time::sleep(wait).await;

            // Re-acquire governor token after sleeping
            if let Some(lim) = limiter {
                lim.acquire().await;
            }

            // Single retry — if still 429, give up
            db.query(title, client, timeout).await
        }
        Err(other) => Err(other),
    };

    RateLimitedResult {
        result,
        elapsed: start.elapsed(),
    }
}

/// Legacy wrapper: calls [`query_with_rate_limit`] (ignores `max_retries`).
///
/// Kept for API compatibility; inline retry has been replaced by
/// the pool-level retry queue.
pub async fn query_with_retry(
    db: &dyn DatabaseBackend,
    title: &str,
    client: &reqwest::Client,
    timeout: Duration,
    rate_limiters: &RateLimiters,
    _max_retries: u32,
) -> RateLimitedResult {
    query_with_rate_limit(db, title, client, timeout, rate_limiters).await
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::db::mock::{MockDb, MockResponse};

    // ── parse_retry_after ──────────────────────────────────────────────

    #[test]
    fn parse_integer_seconds() {
        assert_eq!(parse_retry_after("5"), Some(Duration::from_secs(5)));
    }

    #[test]
    fn parse_zero() {
        assert_eq!(parse_retry_after("0"), Some(Duration::from_secs(0)));
    }

    #[test]
    fn parse_http_date_gmt() {
        let val = "Wed, 21 Oct 2015 07:28:00 GMT";
        // Implementation returns a conservative 5s for date strings
        assert_eq!(parse_retry_after(val), Some(Duration::from_secs(5)));
    }

    #[test]
    fn parse_date_with_comma() {
        let val = "Mon, 01 Jan 2024 00:00:00";
        assert_eq!(parse_retry_after(val), Some(Duration::from_secs(5)));
    }

    #[test]
    fn parse_garbage_none() {
        assert_eq!(parse_retry_after("xyz"), None);
    }

    // ── check_rate_limit_response ──────────────────────────────────────

    #[test]
    fn ok_on_200() {
        let http_resp = http::Response::builder().status(200).body("").unwrap();
        let resp = reqwest::Response::from(http_resp);
        assert!(check_rate_limit_response(&resp).is_ok());
    }

    #[test]
    fn rate_limited_429_no_header() {
        let http_resp = http::Response::builder().status(429).body("").unwrap();
        let resp = reqwest::Response::from(http_resp);
        let err = check_rate_limit_response(&resp).unwrap_err();
        match err {
            DbQueryError::RateLimited { retry_after } => assert!(retry_after.is_none()),
            _ => panic!("expected RateLimited"),
        }
    }

    #[test]
    fn rate_limited_429_with_retry_after() {
        let http_resp = http::Response::builder()
            .status(429)
            .header("retry-after", "10")
            .body("")
            .unwrap();
        let resp = reqwest::Response::from(http_resp);
        let err = check_rate_limit_response(&resp).unwrap_err();
        match err {
            DbQueryError::RateLimited { retry_after } => {
                assert_eq!(retry_after, Some(Duration::from_secs(10)));
            }
            _ => panic!("expected RateLimited"),
        }
    }

    // ── AdaptiveDbLimiter ──────────────────────────────────────────────

    #[test]
    fn starts_at_factor_1() {
        let limiter = AdaptiveDbLimiter::per_second(10);
        assert_eq!(limiter.current_factor.load(Ordering::SeqCst), 1);
    }

    #[test]
    fn on_rate_limited_doubles() {
        let limiter = AdaptiveDbLimiter::per_second(10);
        limiter.on_rate_limited();
        assert_eq!(limiter.current_factor.load(Ordering::SeqCst), 2);
        limiter.on_rate_limited();
        assert_eq!(limiter.current_factor.load(Ordering::SeqCst), 4);
    }

    #[test]
    fn factor_caps_at_16() {
        let limiter = AdaptiveDbLimiter::per_second(10);
        for _ in 0..10 {
            limiter.on_rate_limited();
        }
        assert_eq!(limiter.current_factor.load(Ordering::SeqCst), 16);
    }

    #[tokio::test]
    async fn acquire_completes() {
        // With a generous rate (10/s), the first acquire should return instantly.
        let limiter = AdaptiveDbLimiter::per_second(10);
        limiter.acquire().await;
    }

    #[tokio::test]
    async fn decay_restores_after_60s() {
        let limiter = AdaptiveDbLimiter::per_second(10);
        limiter.on_rate_limited();
        limiter.on_rate_limited();
        assert_eq!(limiter.current_factor.load(Ordering::SeqCst), 4);

        // Manually backdate last_429 to 61 seconds ago
        {
            let mut last = limiter.last_429.lock().unwrap();
            *last = Some(Instant::now() - Duration::from_secs(61));
        }

        // acquire() calls try_decay() internally
        limiter.acquire().await;
        assert_eq!(limiter.current_factor.load(Ordering::SeqCst), 1);
    }

    // ── RateLimiters ───────────────────────────────────────────────────

    #[test]
    fn default_has_expected_dbs() {
        let limiters = RateLimiters::default();
        for name in [
            "CrossRef",
            "arXiv",
            "DBLP",
            "Semantic Scholar",
            "Europe PMC",
            "PubMed",
            "ACL Anthology",
        ] {
            assert!(limiters.get(name).is_some(), "missing limiter for {name}");
        }
    }

    #[test]
    fn crossref_rate_varies_with_mailto() {
        // Without mailto, CrossRef gets 1/s → base_period = 1000ms
        let without = RateLimiters::new(false, false);
        let period_without = without.get("CrossRef").unwrap().base_period;

        // With mailto, CrossRef gets 3/s → base_period = 333ms
        let with = RateLimiters::new(true, false);
        let period_with = with.get("CrossRef").unwrap().base_period;

        assert!(
            period_with < period_without,
            "with mailto should have a shorter period (faster rate)"
        );
    }

    #[test]
    fn unknown_db_returns_none() {
        let limiters = RateLimiters::default();
        assert!(limiters.get("FakeDB").is_none());
    }

    // ── query_with_rate_limit ─────────────────────────────────────────

    #[tokio::test(start_paused = true)]
    async fn success_first_try() {
        let db = MockDb::new(
            "TestDB",
            MockResponse::Found {
                title: "A Paper".into(),
                authors: vec!["Author".into()],
                url: None,
            },
        );
        let client = reqwest::Client::new();
        let limiters = RateLimiters::new(false, false);

        let rl_result =
            query_with_rate_limit(&db, "A Paper", &client, Duration::from_secs(10), &limiters)
                .await;

        assert!(rl_result.result.is_ok());
        let (title, _, _) = rl_result.result.unwrap();
        assert_eq!(title.unwrap(), "A Paper");
        assert_eq!(db.call_count(), 1);
    }

    #[tokio::test(start_paused = true)]
    async fn rate_limited_retries_once() {
        let db = MockDb::new(
            "TestDB",
            MockResponse::RateLimited {
                retry_after: Some(Duration::from_secs(5)),
            },
        );
        let client = reqwest::Client::new();
        let limiters = RateLimiters::new(false, false);

        let rl_result =
            query_with_rate_limit(&db, "A Paper", &client, Duration::from_secs(10), &limiters)
                .await;

        assert!(rl_result.result.is_err());
        // Called twice: initial attempt + one retry after honoring Retry-After
        assert_eq!(db.call_count(), 2);
    }

    #[tokio::test(start_paused = true)]
    async fn other_error_no_retry() {
        let db = MockDb::new("TestDB", MockResponse::Error("connection refused".into()));
        let client = reqwest::Client::new();
        let limiters = RateLimiters::new(false, false);

        let rl_result =
            query_with_rate_limit(&db, "A Paper", &client, Duration::from_secs(10), &limiters)
                .await;

        assert!(rl_result.result.is_err());
        assert_eq!(db.call_count(), 1);
    }
}
