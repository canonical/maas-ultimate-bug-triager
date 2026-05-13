#!/usr/bin/env python
"""CLI to reproduce a MAAS bug by its Launchpad bug ID."""

import asyncio
from typing import Annotated

import typer
from lp.reproducer import reproduce_bug

from lp import get_bug_by_id, get_launchpad_instance

app = typer.Typer()


@app.command()
def reproduce(
    bug_id: Annotated[int, typer.Argument(..., help="Launchpad bug ID to reproduce")],
    maas_ip: Annotated[
        str,
        typer.Option(..., "-mip", "--maas-ip", help="MAAS server IP address"),
    ],
) -> None:
    """Fetch a bug from Launchpad and reproduce it via OpenCode."""
    lp = get_launchpad_instance()
    bug = get_bug_by_id(lp, bug_id)

    typer.echo(f"Reproducing bug #{bug.id}…")
    typer.echo(f"  Title: {bug.title}")
    typer.echo(f"  URL:   {bug.web_link}")
    typer.echo(f"  MAAS IP: {maas_ip}")
    typer.echo()

    asyncio.run(reproduce_bug(bug, maas_ip=maas_ip))


if __name__ == "__main__":
    app()
