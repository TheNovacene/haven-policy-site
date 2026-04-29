// HavenFooter — site footer including charity registration legal note.
// Mandatory for charities under the Charities Act: registered charity number must
// appear on official documentation and websites.

import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
// @ts-ignore
import havenFooterStyle from "./styles/havenFooter.scss"

const HavenFooter: QuartzComponent = ({ }: QuartzComponentProps) => {
  return (
    <footer class="haven-footer">
      <div class="haven-footer-links">
        <a href="https://thehavenonline.school/">Back to The Haven main site</a>
        <span class="haven-footer-sep">·</span>
        <a href="https://autisticgirlsnetwork.org/">Autistic Girls Network</a>
      </div>
      <p class="haven-footer-charity">
        The Haven is part of <a href="https://autisticgirlsnetwork.org/">Autistic Girls Network</a>, registered as a charity in England and Wales (1196655) and in Scotland (SC054837).
      </p>
      <p class="haven-footer-meta">
        Site generated from the Haven Policy Vault. Last refresh: April 2026.
      </p>
    </footer>
  )
}

HavenFooter.css = havenFooterStyle

export default (() => HavenFooter) satisfies QuartzComponentConstructor
