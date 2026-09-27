import { useState } from "react";

export function Swatch({ name, hex }: { name: string; hex: string }) {
  const [copied, setCopied] = useState(false);
  return <button className="swatch" style={{ background: hex }} onClick={() => setCopied(true)}>
    {copied ? "copied!" : name}
  </button>;
}
