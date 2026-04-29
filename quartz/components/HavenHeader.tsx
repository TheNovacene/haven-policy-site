// HavenHeader — site banner that links back to The Haven main site.
// Renders the Haven brand mark + wordmark on the left (linking to thehavenonline.school)
// and a "Policies" section label on the right. Designed to make the policy site
// feel like a contiguous extension of the main Haven domain.

import { QuartzComponent, QuartzComponentConstructor, QuartzComponentProps } from "./types"
// @ts-ignore — SCSS file imported as string at build time
import havenHeaderStyle from "./styles/havenHeader.scss"

const HavenHeader: QuartzComponent = ({ }: QuartzComponentProps) => {
  return (
    <header class="haven-header">
      <a href="https://thehavenonline.school/" class="haven-logo-link" aria-label="Back to The Haven main site">
        <span class="haven-logo-mark" aria-hidden="true">
          <svg viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
            {/* Three pillars of the Haven gate — pointed tops, the middle one
                with a horizontal crossbar to form the "H" of HAVEN. */}
            {/* Left pillar */}
            <polygon points="6,18 14,10 22,18 22,52 6,52" fill="#ffffff" />
            {/* Middle pillar (slightly taller, with crossbar) */}
            <polygon points="26,12 34,4 42,12 42,52 26,52" fill="#ffffff" />
            {/* Crossbar on middle pillar — the "H" stroke */}
            <rect x="22" y="32" width="20" height="4" fill="var(--haven-damson, #786170)" />
            {/* Right pillar */}
            <polygon points="46,16 54,8 60,16 60,52 46,52" fill="#ffffff" />
          </svg>
        </span>
        <span class="haven-logo-text">
          <span class="haven-logo-the">THE</span>
          <span class="haven-logo-haven">HAVEN</span>
        </span>
      </a>
      <span class="haven-header-section">Policies</span>
    </header>
  )
}

HavenHeader.css = havenHeaderStyle

export default (() => HavenHeader) satisfies QuartzComponentConstructor
