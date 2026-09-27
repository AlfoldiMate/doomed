# Build the palette and serve it
def main [--release] {
  cargo build (if $release { "--release" } else { "" })
}
