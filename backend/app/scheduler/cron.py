from apscheduler.schedulers.blocking import BlockingScheduler

from app.tasks.automation import publish_due_posts, scan_all_websites


def main() -> None:
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(lambda: scan_all_websites.delay(), "interval", minutes=10, id="scan-websites", replace_existing=True)
    scheduler.add_job(lambda: publish_due_posts.delay(), "interval", minutes=1, id="publish-due-posts", replace_existing=True)
    scheduler.start()


if __name__ == "__main__":
    main()
