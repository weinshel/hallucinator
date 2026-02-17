use std::path::Path;

use mupdf::{Document, TextPageFlags};

use crate::PdfError;
use crate::config::PdfParsingConfig;
use crate::text_processing::expand_ligatures;

/// Extract text from a PDF file using MuPDF.
///
/// Opens the PDF, iterates all pages, extracts text from each,
/// joins with newlines, and expands typographic ligatures.
///
/// If `config.footer_exclusion_height_ratio` is set, text blocks in the
/// bottom portion of each page (based on the ratio) will be excluded.
/// If `config.header_exclusion_height_ratio` is set, text blocks in the
/// top portion of each page will be excluded.
pub fn extract_text_from_pdf(pdf_path: &Path, config: &PdfParsingConfig) -> Result<String, PdfError> {
    let path_str = pdf_path
        .to_str()
        .ok_or_else(|| PdfError::OpenError("invalid path encoding".into()))?;

    let document = Document::open(path_str).map_err(|e| PdfError::OpenError(e.to_string()))?;

    let mut pages_text = Vec::new();

    for page_result in document
        .pages()
        .map_err(|e| PdfError::ExtractionError(e.to_string()))?
    {
        let page = page_result.map_err(|e| PdfError::ExtractionError(e.to_string()))?;
        let text_page = page
            .to_text_page(TextPageFlags::empty())
            .map_err(|e| PdfError::ExtractionError(e.to_string()))?;

        // Get page bounds for footer exclusion
        let page_bounds = page.bounds().map_err(|e| PdfError::ExtractionError(e.to_string()))?;
        let page_height = page_bounds.y1 - page_bounds.y0;

        // Calculate header threshold if configured
        let header_threshold = config.header_exclusion_height_ratio
            .map(|ratio| page_bounds.y0 + (page_height * ratio as f32));

        // Calculate footer threshold if configured
        let footer_threshold = config.footer_exclusion_height_ratio
            .map(|ratio| page_bounds.y1 - (page_height * ratio as f32));

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

            // Skip blocks whose top edge is below the footer threshold
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

    let text = pages_text.join("\n");

    // Expand typographic ligatures (ﬁ → fi, ﬂ → fl, etc.)
    Ok(expand_ligatures(&text))
}
