import json

import typer

from cli.e4a_cli import app as e4a_app
from sdk.python.e4a_sdk.client import E4AClient
from sdk.python.e4a_sdk.config_loader import load_config

cli = typer.Typer()
config = load_config()


@cli.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """E4A CLI — use --help for subcommands."""
    if ctx.invoked_subcommand is None:
        typer.echo("E4A CLI — use subcommands. Try 'e4a --help'.")


cli.add_typer(e4a_app, name="e4a")


@cli.command("sdk-test")
def sdk_test():
    """Quick SDK smoke test using local config.api host."""
    cfg = load_config()
    base_url = cfg.get("api", {}).get("host", "http://localhost:8000")
    typer.echo(f"Running E4A SDK smoke test against: {base_url}")
    try:
        client = E4AClient(base_url=base_url)
        info = client.health()
        typer.echo(json.dumps(info, indent=2))
    except Exception as e:
        typer.echo(typer.style("⚠️  SDK test failed:", fg=typer.colors.RED, bold=True))
        typer.echo(f"Error: {e}")
        typer.echo(
            "\nTip: Ensure the E4A API server is running.\n"
            "  uvicorn api.server:app --reload --port 8000\n"
            "Then rerun the prompt."
        )


app = cli


if __name__ == "__main__":
    cli()
