#!/usr/bin/env python
from django.core.management import execute_from_command_line

from garimpei.config.env import configure_django

if __name__ == "__main__":
    configure_django()
    execute_from_command_line()
