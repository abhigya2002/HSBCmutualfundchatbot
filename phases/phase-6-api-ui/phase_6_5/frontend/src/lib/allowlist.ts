export const ALLOWLISTED_CITATION_URLS: readonly string[] = [
  "https://groww.in/mutual-funds/hsbc-india-opportunities-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-small-cap-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-value-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-large-and-mid-cap-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-equity-savings-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-infrastructure-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-multi-asset-allocation-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-focused-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-gold-etf-fof-direct-growth",
  "https://groww.in/mutual-funds/hsbc-india-export-opportunities-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-consumption-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-medium-duration-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-dynamic-bond-fund-direct-growth",
  "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth",
] as const;

export function normalizeUrl(url: string): string {
  return url.trim().replace(/\/+$/, "");
}

const allowlistSet = new Set(ALLOWLISTED_CITATION_URLS.map(normalizeUrl));

export function isAllowlistedCitationUrl(url: string): boolean {
  if (!url.trim()) return false;
  return allowlistSet.has(normalizeUrl(url));
}

export function citationLabelFromUrl(url: string): string {
  try {
    const slug = new URL(url).pathname.split("/").pop() || "Official Source";
    return slug.replace(/-/g, " ");
  } catch {
    return "Official Source";
  }
}
