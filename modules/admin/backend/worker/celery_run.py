def main() -> None:
    # Invoke Celery CLI programmatically so it works inside a PEX image
    import sys

    from celery.bin.celery import main as celery_main

    sys.argv = [
        "celery",
        "-A",
        "modules.admin.backend.worker.celery_app",
        "worker",
        "-l",
        "info",
    ]
    celery_main()


if __name__ == "__main__":
    main()
