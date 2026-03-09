import os

import click


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--cwd", default=None, help="Project working directory")
def main(ctx, cwd):
    """cmux - Claude Code session monitor."""
    if ctx.invoked_subcommand is None:
        from .launcher import launch

        launch(cwd or os.getcwd())


@main.command()
@click.option("--cwd", required=True, help="Project working directory")
@click.option("--session-id", required=True, help="Session UUID")
def todos(cwd, session_id):
    """Launch the TODO tracker TUI."""
    from .todos_app import TodosApp

    app = TodosApp(cwd=cwd, session_id=session_id)
    app.run()


@main.command()
@click.option("--cwd", required=True, help="Project working directory")
@click.option("--session-id", required=True, help="Session UUID")
def agents(cwd, session_id):
    """Launch the Subagent monitor TUI."""
    from .agents_app import AgentsApp

    app = AgentsApp(cwd=cwd, session_id=session_id)
    app.run()
