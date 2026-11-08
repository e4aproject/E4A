"""E4A command-line entry point.

Installed as the ``e4a`` console script by the e4a-sdk distribution.
Commands:

- ``e4a version`` — print the package and protocol versions.
- ``e4a mandate ...`` — the mandate lifecycle (see cli/e4a_cli.py).
- ``e4a serve`` — run the reference HTTP service (uvicorn, factory mode).
"""

import typer

from cli.e4a_cli import app as mandate_app
from e4a_sdk import PROTOCOL_VERSION, __version__

cli = typer.Typer(help="E4A — Ethos4Agents protocol CLI.")
cli.add_typer(mandate_app, name="mandate")


@cli.command("version")
def version():
    """Print package and protocol versions."""
    typer.echo(f"e4a-sdk {__version__} (protocol {PROTOCOL_VERSION})")


@cli.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
):
    """Run the reference HTTP service from the installed package."""
    import uvicorn

    uvicorn.run("api.server:create_app", factory=True, host=host, port=port)


app = cli

if __name__ == "__main__":
    cli()
