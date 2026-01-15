# test_cmd.py
import pytest

pytest.importorskip("typer")
import typer

app_test = typer.Typer()


@app_test.command()
def hello(name: str):
    print(f"Hello {name}")


@app_test.command()
def goodbye(name: str):
    print(f"Goodbye {name}")


if __name__ == "__main__":
    app_test()
