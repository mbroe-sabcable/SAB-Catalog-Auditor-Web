import os
import sys
import traceback
from pathlib import Path


def _bootstrap_project_python() -> None:
	try:
		import PySide6  # noqa: F401
		return
	except Exception as exc:
		print(f"Failed to import PySide6 during bootstrap: {exc}")
		traceback.print_exc()
		return


def main() -> int:
	_bootstrap_project_python()

	from PySide6.QtWidgets import QApplication

	from app.main_window import MainWindow

	app = QApplication(sys.argv)
	window = MainWindow()
	window.show()
	return app.exec()


if __name__ == "__main__":
	try:
		raise SystemExit(main())
	except SystemExit:
		raise
	except Exception as exc:
		print(f"Failed to start desktop application: {exc}")
		traceback.print_exc()
		sys.exit(1)