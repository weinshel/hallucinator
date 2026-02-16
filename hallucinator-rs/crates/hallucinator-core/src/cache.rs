//! SQLite-based query result cache for database lookups.
//!
//! Caches `(db_name, normalized_title) -> DbQueryResult` to avoid redundant
//! network requests when re-checking the same papers. Errors are never cached.
//! Found results expire after 30 days; not-found results after 7 days.

use crate::db::DbQueryResult;
use crate::matching::normalize_title;
use rusqlite::Connection;
use std::path::Path;
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

/// TTL for results where the title was found in the database (30 days).
const TTL_FOUND_SECS: i64 = 30 * 24 * 60 * 60;

/// TTL for results where the title was not found (7 days).
const TTL_NOT_FOUND_SECS: i64 = 7 * 24 * 60 * 60;

/// A persistent SQLite cache for database query results.
///
/// Thread-safe via `Mutex<Connection>`. All operations silently log errors
/// rather than propagating them, so the cache never blocks validation.
pub struct QueryCache {
    conn: Mutex<Connection>,
}

impl std::fmt::Debug for QueryCache {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("QueryCache")
            .field("conn", &"<sqlite>")
            .finish()
    }
}

impl QueryCache {
    /// Open (or create) a cache database at the given path.
    pub fn open(path: &Path) -> Result<Self, rusqlite::Error> {
        if let Some(parent) = path.parent() {
            let _ = std::fs::create_dir_all(parent);
        }

        let conn = Connection::open(path)?;
        conn.pragma_update(None, "journal_mode", "WAL")?;
        conn.pragma_update(None, "synchronous", "NORMAL")?;

        conn.execute_batch(
            "CREATE TABLE IF NOT EXISTS query_cache (
                db_name    TEXT NOT NULL,
                norm_title TEXT NOT NULL,
                found_title TEXT,
                authors    TEXT NOT NULL DEFAULT '[]',
                paper_url  TEXT,
                cached_at  INTEGER NOT NULL,
                ttl_secs   INTEGER NOT NULL,
                PRIMARY KEY (db_name, norm_title)
            )",
        )?;

        Ok(Self {
            conn: Mutex::new(conn),
        })
    }

    /// Look up a cached result. Returns `None` on miss or expiry.
    pub fn get(&self, db_name: &str, title: &str) -> Option<DbQueryResult> {
        let norm = normalize_title(title);
        let now = now_epoch();
        let conn = self.conn.lock().ok()?;

        let result = conn.query_row(
            "SELECT found_title, authors, paper_url, cached_at, ttl_secs
             FROM query_cache
             WHERE db_name = ?1 AND norm_title = ?2",
            rusqlite::params![db_name, norm],
            |row| {
                let found_title: Option<String> = row.get(0)?;
                let authors_json: String = row.get(1)?;
                let paper_url: Option<String> = row.get(2)?;
                let cached_at: i64 = row.get(3)?;
                let ttl_secs: i64 = row.get(4)?;
                Ok((found_title, authors_json, paper_url, cached_at, ttl_secs))
            },
        );

        match result {
            Ok((found_title, authors_json, paper_url, cached_at, ttl_secs)) => {
                // Check expiry
                if now - cached_at > ttl_secs {
                    // Expired — remove it
                    let _ = conn.execute(
                        "DELETE FROM query_cache WHERE db_name = ?1 AND norm_title = ?2",
                        rusqlite::params![db_name, norm],
                    );
                    return None;
                }

                let authors: Vec<String> =
                    serde_json::from_str(&authors_json).unwrap_or_default();
                Some((found_title, authors, paper_url))
            }
            Err(_) => None,
        }
    }

    /// Store a result in the cache. Only call for `Ok(...)` results — never cache errors.
    pub fn put(&self, db_name: &str, title: &str, result: &DbQueryResult) {
        let norm = normalize_title(title);
        let now = now_epoch();
        let (found_title, authors, paper_url) = result;
        let ttl = if found_title.is_some() {
            TTL_FOUND_SECS
        } else {
            TTL_NOT_FOUND_SECS
        };

        let authors_json = serde_json::to_string(authors).unwrap_or_else(|_| "[]".to_string());

        let Ok(conn) = self.conn.lock() else {
            return;
        };

        let _ = conn.execute(
            "INSERT OR REPLACE INTO query_cache
             (db_name, norm_title, found_title, authors, paper_url, cached_at, ttl_secs)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
            rusqlite::params![db_name, norm, found_title, authors_json, paper_url, now, ttl],
        );
    }

    /// Remove all entries from the cache.
    pub fn clear(&self) {
        if let Ok(conn) = self.conn.lock() {
            let _ = conn.execute("DELETE FROM query_cache", []);
        }
    }

    /// Remove expired entries.
    pub fn evict_expired(&self) {
        let now = now_epoch();
        if let Ok(conn) = self.conn.lock() {
            let _ = conn.execute(
                "DELETE FROM query_cache WHERE (cached_at + ttl_secs) < ?1",
                rusqlite::params![now],
            );
        }
    }

    /// Return the number of cached entries (for diagnostics).
    pub fn len(&self) -> usize {
        let Ok(conn) = self.conn.lock() else {
            return 0;
        };
        conn.query_row("SELECT COUNT(*) FROM query_cache", [], |row| row.get(0))
            .unwrap_or(0)
    }

    /// Whether the cache is empty.
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }
}

fn now_epoch() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs() as i64
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::NamedTempFile;

    fn temp_cache() -> QueryCache {
        let f = NamedTempFile::new().unwrap();
        QueryCache::open(f.path()).unwrap()
    }

    #[test]
    fn test_put_and_get_found() {
        let cache = temp_cache();
        let result: DbQueryResult = (
            Some("Some Paper Title".to_string()),
            vec!["Alice".to_string(), "Bob".to_string()],
            Some("https://example.com/paper".to_string()),
        );

        cache.put("CrossRef", "Some Paper Title", &result);

        let cached = cache.get("CrossRef", "Some Paper Title");
        assert!(cached.is_some());
        let (title, authors, url) = cached.unwrap();
        assert_eq!(title, Some("Some Paper Title".to_string()));
        assert_eq!(authors, vec!["Alice", "Bob"]);
        assert_eq!(url, Some("https://example.com/paper".to_string()));
    }

    #[test]
    fn test_put_and_get_not_found() {
        let cache = temp_cache();
        let result: DbQueryResult = (None, vec![], None);

        cache.put("arXiv", "Nonexistent Paper", &result);

        let cached = cache.get("arXiv", "Nonexistent Paper");
        assert!(cached.is_some());
        let (title, authors, url) = cached.unwrap();
        assert!(title.is_none());
        assert!(authors.is_empty());
        assert!(url.is_none());
    }

    #[test]
    fn test_different_dbs_independent() {
        let cache = temp_cache();
        let found: DbQueryResult = (Some("Paper".to_string()), vec![], None);
        let not_found: DbQueryResult = (None, vec![], None);

        cache.put("CrossRef", "Paper", &found);
        cache.put("arXiv", "Paper", &not_found);

        let cr = cache.get("CrossRef", "Paper").unwrap();
        assert!(cr.0.is_some());

        let ax = cache.get("arXiv", "Paper").unwrap();
        assert!(ax.0.is_none());
    }

    #[test]
    fn test_miss_returns_none() {
        let cache = temp_cache();
        assert!(cache.get("CrossRef", "Unknown Paper").is_none());
    }

    #[test]
    fn test_clear() {
        let cache = temp_cache();
        let result: DbQueryResult = (Some("Paper".to_string()), vec![], None);
        cache.put("CrossRef", "Paper", &result);
        assert!(!cache.is_empty());

        cache.clear();
        assert!(cache.is_empty());
        assert!(cache.get("CrossRef", "Paper").is_none());
    }

    #[test]
    fn test_normalize_key() {
        let cache = temp_cache();
        let result: DbQueryResult = (Some("Paper Title".to_string()), vec![], None);

        // Store with one casing, retrieve with another
        cache.put("CrossRef", "Paper Title!", &result);
        let cached = cache.get("CrossRef", "paper title");
        assert!(cached.is_some());
    }

    #[test]
    fn test_len() {
        let cache = temp_cache();
        assert_eq!(cache.len(), 0);

        let result: DbQueryResult = (Some("Paper".to_string()), vec![], None);
        cache.put("CrossRef", "Paper", &result);
        assert_eq!(cache.len(), 1);

        cache.put("arXiv", "Paper", &result);
        assert_eq!(cache.len(), 2);
    }
}
