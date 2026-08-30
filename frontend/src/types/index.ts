export type Platform = "website" | "facebook" | "instagram" | "linkedin" | "twitter" | "threads" | "pinterest" | "telegram";
export type WebsiteType = "wordpress" | "rss" | "custom" | "sitemap" | "webhook";
export type PostStatus = "draft" | "pending_approval" | "scheduled" | "publishing" | "published" | "failed";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "manager" | "editor" | "viewer";
}

export interface Website {
  _id?: string;
  id?: string;
  name: string;
  url: string;
  type: WebsiteType;
  is_active: boolean;
  last_checked_at?: string;
}

export interface ContentItem {
  _id?: string;
  id?: string;
  title: string;
  canonical_url: string;
  meta_description?: string;
  keywords: string[];
  short_summary?: string;
  long_summary?: string;
}

export interface GeneratedPost {
  _id?: string;
  id?: string;
  platform: Platform;
  text: string;
  hashtags: string[];
  cta: string;
  image_urls: string[];
  status: PostStatus;
}

export interface SocialAccount {
  _id?: string;
  id?: string;
  platform: Platform;
  display_name: string;
  external_id: string;
}

export interface ScheduledPost {
  _id?: string;
  id?: string;
  platform: Platform;
  status: PostStatus;
  scheduled_for?: string;
  mode: string;
  failure_reason?: string;
}
