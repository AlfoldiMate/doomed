//! A tiny palette server, here to show off the theme.
use std::collections::HashMap;
use std::fmt;

/// One named colour in a palette.
#[derive(Debug, Clone, PartialEq)]
pub struct Swatch<'a> {
    pub name: &'a str,
    pub hex: u32,
    alpha: f32,
}

pub enum Mode {
    Dark,
    Light { contrast: f64 },
}

impl<'a> Swatch<'a> {
    pub const WHITE: u32 = 0xbbc2cf;

    pub fn new(name: &'a str, hex: u32) -> Self {
        Self { name, hex, alpha: 1.0 }
    }

    /// Relative luminance per WCAG 2.1.
    fn luminance(&self) -> f64 {
        let [r, g, b] = [16, 8, 0].map(|s| ((self.hex >> s) & 0xff) as f64 / 255.0);
        0.2126 * r + 0.7152 * g + 0.0722 * b
    }
}

impl fmt::Display for Swatch<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{} #{:06x} ({:.0}%)", self.name, self.hex, self.alpha * 100.0)
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut palette: HashMap<&str, Swatch> = HashMap::new();
    for (name, hex) in [("red", 0xff6b5a), ("green", 0x98be65), ("blue", 0x51afef)] {
        palette.insert(name, Swatch::new(name, hex));
    }

    // TODO: derive the light variant instead of hard-coding it
    let mode = Mode::Light { contrast: 4.6 };
    if let Mode::Light { contrast } = mode {
        println!("targeting {contrast}:1 on light surfaces");
    }

    let brightest = palette.values().max_by(|a, b| a.luminance().total_cmp(&b.luminance()));
    match brightest {
        Some(swatch) => println!("brightest: {swatch}"),
        None => eprintln!("empty palette\n"),
    }
    Ok(())
}
