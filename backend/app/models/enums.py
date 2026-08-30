from enum import StrEnum


class UserRole(StrEnum):
    admin = "admin"
    manager = "manager"
    editor = "editor"
    viewer = "viewer"


class WebsiteType(StrEnum):
    wordpress = "wordpress"
    rss = "rss"
    custom = "custom"
    sitemap = "sitemap"
    webhook = "webhook"


class Platform(StrEnum):
    website = "website"
    facebook = "facebook"
    instagram = "instagram"
    linkedin = "linkedin"
    twitter = "twitter"
    threads = "threads"
    pinterest = "pinterest"
    telegram = "telegram"


class ScheduleMode(StrEnum):
    immediate = "immediate"
    specific = "specific"
    recurring = "recurring"
    draft = "draft"
    approval = "approval"
    auto = "auto"


class PostStatus(StrEnum):
    draft = "draft"
    pending_approval = "pending_approval"
    scheduled = "scheduled"
    publishing = "publishing"
    published = "published"
    failed = "failed"


class Tone(StrEnum):
    professional = "professional"
    friendly = "friendly"
    witty = "witty"
    educational = "educational"
    persuasive = "persuasive"


class Language(StrEnum):
    en = "English"
    hi = "Hindi"
    ar = "Arabic"
    es = "Spanish"
    fr = "French"
    de = "German"
