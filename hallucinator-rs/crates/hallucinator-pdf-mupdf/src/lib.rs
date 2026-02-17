use std::path::Path;

use mupdf::{Document, TextPageFlags};

use hallucinator_core::{BackendError, PdfBackend};

/// MuPDF-based implementation of [`PdfBackend`].
///
/// This crate is the sole AGPL island — it isolates the mupdf dependency
/// (which is AGPL-3.0) so that non-PDF code paths do not transitively
/// depend on it.
///
/// By default, text in the bottom 5% of each page (footers) and top 4%
/// (headers) is excluded to prevent conference proceedings footer lines
/// like "USENIX Association  34th USENIX Security Symposium  5281" from
/// being embedded mid-citation when references span page breaks.
pub struct MupdfBackend {
    /// Fraction of page height from bottom to exclude as footer (0.0–1.0).
    /// Default 0.05. `None` disables footer exclusion.
    footer_exclusion_ratio: Option<f32>,
    /// Fraction of page height from top to exclude as header (0.0–1.0).
    /// Default 0.04. `None` disables header exclusion.
    header_exclusion_ratio: Option<f32>,
}

impl Default for MupdfBackend {
    fn default() -> Self {
        Self {
            footer_exclusion_ratio: Some(0.05),
            header_exclusion_ratio: Some(0.04),
        }
    }
}

impl MupdfBackend {
    pub fn new() -> Self {
        Self::default()
    }

    /// Set the footer exclusion ratio. Pass `0.0` to disable.
    pub fn with_footer_exclusion(mut self, ratio: f32) -> Self {
        self.footer_exclusion_ratio = if ratio > 0.0 { Some(ratio) } else { None };
        self
    }

    /// Set the header exclusion ratio. Pass `0.0` to disable.
    pub fn with_header_exclusion(mut self, ratio: f32) -> Self {
        self.header_exclusion_ratio = if ratio > 0.0 { Some(ratio) } else { None };
        self
    }
}

impl PdfBackend for MupdfBackend {
    fn extract_text(&self, path: &Path) -> Result<String, BackendError> {
        let path_str = path
            .to_str()
            .ok_or_else(|| BackendError::OpenError("invalid path encoding".into()))?;

        let document =
            Document::open(path_str).map_err(|e| BackendError::OpenError(e.to_string()))?;

        let mut pages_text = Vec::new();

        for page_result in document
            .pages()
            .map_err(|e| BackendError::ExtractionError(e.to_string()))?
        {
            let page = page_result.map_err(|e| BackendError::ExtractionError(e.to_string()))?;
            let text_page = page
                .to_text_page(TextPageFlags::empty())
                .map_err(|e| BackendError::ExtractionError(e.to_string()))?;

            // Get page bounds for header/footer exclusion
            let page_bounds = page
                .bounds()
                .map_err(|e| BackendError::ExtractionError(e.to_string()))?;
            let page_height = page_bounds.y1 - page_bounds.y0;

            let header_threshold = self
                .header_exclusion_ratio
                .map(|r| page_bounds.y0 + page_height * r);
            let footer_threshold = self
                .footer_exclusion_ratio
                .map(|r| page_bounds.y1 - page_height * r);

            // Use block/line iteration to match PyMuPDF's get_text() behavior
            let mut page_text = String::new();
            for block in text_page.blocks() {
                let block_bounds = block.bounds();

                // Skip blocks entirely within the header region
                if let Some(threshold) = header_threshold {
                    if block_bounds.y1 <= threshold {
                        continue;
                    }
                }

                // Skip blocks whose top edge is in the footer region
                if let Some(threshold) = footer_threshold {
                    if block_bounds.y0 >= threshold {
                        continue;
                    }
                }

                for line in block.lines() {
                    let line_text: String = line
                        .chars()
                        .map(|c| c.char().unwrap_or('\u{FFFD}'))
                        .collect();
                    page_text.push_str(&line_text);
                    page_text.push('\n');
                }
            }
            pages_text.push(page_text);
        }

        Ok(pages_text.join("\n"))
    }
}
