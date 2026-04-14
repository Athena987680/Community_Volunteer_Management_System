#!/usr/bin/env python
"""后端管理命令入口脚本。"""
import os
import sys


def main():
    """执行后端管理命令。"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "volunteer_system.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
