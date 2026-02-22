//! Show the extracted references section from a PDF
//!
//! Usage: cargo run --example show_refs_section -- /path/to/file.pdf

use std::path::Path;
use anyhow::{Context, Result};
use mupdf::Document;
use hallucinator_pdf::section::{find_references_section, segment_references_all_strategies};
use hallucinator_pdf::PdfParsingConfig;

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    let pdf_path = args.get(1).expect("Usage: show_refs_section <pdf>");

    let text = extract_text_from_pdf(Path::new(pdf_path))?;

    println!("=== Full text length: {} chars ===\n", text.len());

    if let Some(refs) = find_references_section(&text) {
        println!("=== References section ({} chars) ===\n", refs.len());
        println!("{}", &refs[..refs.len().min(3000)]);

        if refs.len() > 3000 {
            println!("\n... [truncated] ...\n");
        }

        let config = PdfParsingConfig::default();
        let results = segment_references_all_strategies(&refs, &config);

        println!("\n=== Segmentation Results ===");
        for r in &results {
            println!("{:?}: {} references", r.strategy, r.references.len());
        }

        // Show first few refs from best strategy
        if let Some(best) = results.iter().max_by_key(|r| r.references.len()) {
            println!("\n=== First 3 refs from {:?} ===", best.strategy);
            for (i, r) in best.references.iter().take(3).enumerate() {
                println!("\n[{}] {}", i+1, r);
            }
        }
    } else {
        println!("No references section found!");
        println!("\n=== Last 2000 chars of text ===\n");
        let start = text.len().saturating_sub(2000);
        println!("{}", &text[start..]);
    }

    Ok(())
}

fn extract_text_from_pdf(path: &Path) -> Result<String> {
    let doc = Document::open(path.to_str().unwrap()).context("Failed to open PDF")?;
    let mut text = String::new();
    for page_num in 0..doc.page_count()? {
        if let Ok(page) = doc.load_page(page_num) {
            if let Ok(text_page) = page.to_text_page(mupdf::TextPageFlags::empty()) {
                for block in text_page.blocks() {
                    for line in block.lines() {
                        for ch in line.chars() {
                            if let Some(c) = ch.char() {
                                text.push(c);
                            }
                        }
                    }
                    text.push('\n');
                }
            }
        }
    }
    Ok(text)
}
