use pyo3::prelude::*;

mod errors;
mod extractor;
mod types;

/// The native extension module for the `hallucinator` Python package.
#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<extractor::PyPdfExtractor>()?;
    m.add_class::<types::PyReference>()?;
    m.add_class::<types::PyExtractionResult>()?;
    m.add_class::<types::PySkipStats>()?;
    Ok(())
}
