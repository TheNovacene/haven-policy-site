import { PageLayout, SharedLayout } from "./quartz/cfg"
import * as Component from "./quartz/components"
import HavenHeader from "./quartz/components/HavenHeader"
import HavenFooter from "./quartz/components/HavenFooter"

// Components shared by all layouts
export const sharedPageComponents: SharedLayout = {
  head: Component.Head(),
  header: [HavenHeader()],  // Haven brand banner — links back to thehavenonline.school
  afterBody: [],
  footer: HavenFooter(),  // Custom footer with charity registration (legal requirement)
}

// Component layout for content pages (a single policy)
export const defaultContentPageLayout: PageLayout = {
  beforeBody: [
    Component.Breadcrumbs(),
    Component.ArticleTitle(),
    Component.ContentMeta(),
    Component.TagList(),
  ],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Search(),
    Component.Darkmode(),
    Component.DesktopOnly(Component.Explorer()),
  ],
  right: [
    Component.Graph(),
    Component.DesktopOnly(Component.TableOfContents()),
    Component.Backlinks(),
  ],
}

// Component layout for list/folder pages (e.g. /policies/safeguarding/)
export const defaultListPageLayout: PageLayout = {
  beforeBody: [Component.Breadcrumbs(), Component.ArticleTitle(), Component.ContentMeta()],
  left: [
    Component.PageTitle(),
    Component.MobileOnly(Component.Spacer()),
    Component.Search(),
    Component.Darkmode(),
    Component.DesktopOnly(Component.Explorer()),
  ],
  right: [],
}
