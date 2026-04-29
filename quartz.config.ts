import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

/**
 * Haven Policy Site — Quartz v4 configuration.
 *
 * Brand alignment: per The Haven Academy Brand Basics —
 *   Primary palette: Rose #b8838c, Damson #786170, China Rose #b06378
 *   Secondary palette: Sea Green #abccbd, Light Blue #93b7be, Sunny Yellow #f2c078, Tea Rose #dbb4ad
 *   Tertiary palette: Gunmetal #143642 (text), Warm Grey #e7e2da, Light Pink #ffe3dc (backgrounds)
 *   Typography: Poppins.
 */
const config: QuartzConfig = {
  configuration: {
    pageTitle: "The Haven — Policies",
    pageTitleSuffix: " · The Haven",
    enableSPA: true,
    enablePopovers: true,
    analytics: null, // No third-party analytics — ICO Children's Code aligned
    locale: "en-GB",
    baseUrl: "policies.thehavenonline.school",
    ignorePatterns: [
      "private",
      "templates",
      ".obsidian",
      "_meta/role-holders*",
      "_dashboards",
      "_templates",
    ],
    defaultDateType: "modified",
    theme: {
      fontOrigin: "googleFonts",
      cdnCaching: true,
      typography: {
        header: "Poppins",
        body: "Poppins",
        code: "JetBrains Mono",
      },
      colors: {
        lightMode: {
          // Backgrounds
          light: "#ffe3dc",            // Light Pink — page background (warm, welcoming)
          lightgray: "#e7e2da",         // Warm Grey — secondary surfaces, borders
          // Mid tones
          gray: "#b8838c",              // Rose — muted/quiet accent
          // Text
          darkgray: "#143642",          // Gunmetal — secondary text
          dark: "#143642",              // Gunmetal — primary body text
          // Primary accent (links, headings)
          secondary: "#786170",         // Damson — primary heading/link colour
          // Tertiary accent (visited links, secondary hover)
          tertiary: "#b06378",          // China Rose — accent / hover / visited
          highlight: "rgba(242, 192, 120, 0.25)",  // Sunny Yellow tint
          textHighlight: "#f2c078aa",   // Sunny Yellow translucent
        },
        darkMode: {
          // Inverted Haven palette for dark reading
          light: "#143642",             // Gunmetal — page background
          lightgray: "#1f4a55",         // Slightly lighter gunmetal
          gray: "#786170",              // Damson — muted
          darkgray: "#e7e2da",          // Warm Grey — secondary text
          dark: "#ffe3dc",              // Light Pink — primary text
          secondary: "#dbb4ad",         // Tea Rose — primary heading/link colour
          tertiary: "#b8838c",          // Rose — accent
          highlight: "rgba(242, 192, 120, 0.18)",
          textHighlight: "#f2c07866",
        },
      },
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({ priority: ["frontmatter", "filesystem"] }),
      Plugin.SyntaxHighlighting({ theme: { light: "github-light", dark: "github-dark" }, keepBackground: false }),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents(),
      Plugin.CrawlLinks({ markdownLinkResolution: "shortest" }),
      Plugin.Description(),
      Plugin.Latex({ renderEngine: "katex" }),
    ],
    filters: [
      // The sync-vault.py step already excludes drafts, superseded, archived,
      // needs-remediation, and resolved policies before Quartz sees them. Keeping
      // RemoveDrafts here as a defence-in-depth backstop — it strips anything with
      // `draft: true` in frontmatter as well.
      Plugin.RemoveDrafts(),
    ],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({ enableSiteMap: true, enableRSS: false }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.NotFoundPage(),
    ],
  },
}

export default config
